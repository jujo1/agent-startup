#!/usr/bin/env python3
"""
MCP Authentication Proxy for Tailscale Funnel
AGENTS 4.0 - Cloud Agent Gateway

This proxy provides authenticated access to local MCP servers via Tailscale Funnel.
It validates bearer tokens, enforces tool whitelisting, and rate limits requests.

Usage:
    python mcp_auth_proxy.py                    # Start with default config
    python mcp_auth_proxy.py --config my.yaml   # Use custom config
    python mcp_auth_proxy.py --port 8081        # Override port
"""

import json
import asyncio
import logging
import hashlib
import time
from pathlib import Path
from datetime import datetime
from typing import Any
import sys

# Optional dependencies with fallbacks
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

try:
    from aiohttp import web, ClientSession
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class TokenManager:
    """Manage bearer tokens for authentication."""
    
    def __init__(self, token_file: Path):
        self.token_file = token_file
        self.tokens: dict[str, dict] = {}
        self.load_tokens()
    
    def load_tokens(self):
        """Load tokens from JSON file."""
        if not self.token_file.exists():
            logger.warning(f"Token file not found: {self.token_file}")
            return
        
        try:
            with open(self.token_file) as f:
                data = json.load(f)
            
            for token_entry in data.get('tokens', []):
                token_hash = self._hash_token(token_entry['token'])
                self.tokens[token_hash] = {
                    'purpose': token_entry.get('purpose', 'unknown'),
                    'created': token_entry.get('created'),
                    'expires': token_entry.get('expires'),
                    'last_used': None,
                    'use_count': 0
                }
            
            logger.info(f"Loaded {len(self.tokens)} bearer tokens")
        except Exception as e:
            logger.error(f"Failed to load tokens: {e}")
    
    def _hash_token(self, token: str) -> str:
        """Create secure hash of token for comparison."""
        return hashlib.sha256(token.encode()).hexdigest()
    
    def validate(self, token: str) -> tuple[bool, str]:
        """Validate a bearer token. Returns (is_valid, reason)."""
        if not token:
            return False, "No token provided"
        
        token_hash = self._hash_token(token)
        
        if token_hash not in self.tokens:
            return False, "Invalid token"
        
        token_info = self.tokens[token_hash]
        
        # Check expiration
        if token_info.get('expires'):
            expires = datetime.fromisoformat(token_info['expires'])
            if datetime.now() > expires:
                return False, "Token expired"
        
        # Update usage stats
        token_info['last_used'] = datetime.now().isoformat()
        token_info['use_count'] += 1
        
        return True, token_info.get('purpose', 'authorized')


class RateLimiter:
    """Simple token bucket rate limiter."""
    
    def __init__(self, requests_per_minute: int = 60, burst_limit: int = 10):
        self.rpm = requests_per_minute
        self.burst = burst_limit
        self.tokens: dict[str, list[float]] = {}
    
    def check(self, client_id: str) -> tuple[bool, str]:
        """Check if request is allowed. Returns (allowed, reason)."""
        now = time.time()
        minute_ago = now - 60
        
        if client_id not in self.tokens:
            self.tokens[client_id] = []
        
        # Clean old entries
        self.tokens[client_id] = [t for t in self.tokens[client_id] if t > minute_ago]
        
        # Check rate limit
        if len(self.tokens[client_id]) >= self.rpm:
            return False, f"Rate limit exceeded ({self.rpm}/min)"
        
        # Check burst
        recent = [t for t in self.tokens[client_id] if t > now - 1]
        if len(recent) >= self.burst:
            return False, f"Burst limit exceeded ({self.burst}/sec)"
        
        self.tokens[client_id].append(now)
        return True, "ok"


class MCPAuthProxy:
    """Authentication proxy for MCP servers."""
    
    def __init__(self, config_path: Path | None = None):
        self.config = self._load_config(config_path)
        self.token_manager = TokenManager(
            Path(self.config['paths']['tokens']).expanduser()
        )
        self.rate_limiter = RateLimiter(
            self.config['rate_limit']['requests_per_minute'],
            self.config['rate_limit']['burst']
        )
        self.allowed_tools = set(self.config.get('allowed_tools', []))
        self.request_count = 0
        self.start_time = time.time()
    
    def _load_config(self, config_path: Path | None) -> dict:
        """Load configuration from YAML or use defaults."""
        default_config = {
            'proxy': {
                'backend_port': 8080,
                'listen_port': 8081,
                'listen_host': '127.0.0.1'
            },
            'paths': {
                'tokens': '~/.credentials/mcp_tokens.json',
                'logs': '~/.claude/mcp-funnel/access.log'
            },
            'allowed_tools': [
                'ping', 'health', 'read_file', 'list_directory',
                'search', 'grep', 'glob', 'get_status', 'semantic_search',
                'git_status', 'git_diff', 'git_log'
            ],
            'rate_limit': {
                'requests_per_minute': 60,
                'burst': 10
            }
        }
        
        if config_path and config_path.exists() and YAML_AVAILABLE:
            try:
                with open(config_path) as f:
                    user_config = yaml.safe_load(f)
                # Merge configs
                for key in user_config:
                    if key in default_config and isinstance(default_config[key], dict):
                        default_config[key].update(user_config[key])
                    else:
                        default_config[key] = user_config[key]
                logger.info(f"Loaded config from {config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config: {e}, using defaults")
        
        return default_config
    
    def _get_client_id(self, request) -> str:
        """Extract client identifier from request."""
        # Use X-Forwarded-For if behind proxy, otherwise peer IP
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()
        if request.transport:
            peername = request.transport.get_extra_info('peername')
            if peername:
                return peername[0]
        return 'unknown'
    
    def _extract_token(self, request) -> str | None:
        """Extract bearer token from Authorization header."""
        auth = request.headers.get('Authorization', '')
        if auth.startswith('Bearer '):
            return auth[7:]
        return None
    
    async def health_handler(self, request):
        """Handle /health endpoint (no auth required)."""
        uptime = time.time() - self.start_time
        return web.json_response({
            'status': 'healthy',
            'uptime_seconds': round(uptime, 2),
            'requests_served': self.request_count,
            'version': '1.0.0',
            'timestamp': datetime.now().isoformat()
        })
    
    async def tools_handler(self, request):
        """Handle /tools endpoint - list available tools."""
        token = self._extract_token(request)
        valid, reason = self.token_manager.validate(token)
        
        if not valid:
            return web.json_response(
                {'error': 'Unauthorized', 'reason': reason},
                status=401
            )
        
        return web.json_response({
            'tools': sorted(self.allowed_tools),
            'count': len(self.allowed_tools)
        })
    
    async def mcp_handler(self, request):
        """Handle /mcp endpoint - proxy tool invocations."""
        self.request_count += 1
        client_id = self._get_client_id(request)
        
        # Rate limiting
        allowed, reason = self.rate_limiter.check(client_id)
        if not allowed:
            logger.warning(f"Rate limited: {client_id} - {reason}")
            return web.json_response(
                {'error': 'Rate Limited', 'reason': reason},
                status=429
            )
        
        # Authentication
        token = self._extract_token(request)
        valid, auth_reason = self.token_manager.validate(token)
        
        if not valid:
            logger.warning(f"Auth failed: {client_id} - {auth_reason}")
            return web.json_response(
                {'error': 'Unauthorized', 'reason': auth_reason},
                status=401
            )
        
        # Parse request
        try:
            body = await request.json()
        except Exception:
            return web.json_response(
                {'error': 'Invalid JSON'},
                status=400
            )
        
        tool = body.get('tool')
        params = body.get('params', {})
        
        # Tool whitelist check
        if tool not in self.allowed_tools:
            logger.warning(f"Blocked tool: {tool} from {client_id}")
            return web.json_response({
                'success': False,
                'error': {
                    'code': 'TOOL_NOT_ALLOWED',
                    'message': f"Tool '{tool}' not in whitelist",
                    'allowed_tools': sorted(self.allowed_tools)
                }
            }, status=403)
        
        # Execute tool (proxy to backend)
        logger.info(f"Executing: {tool} from {client_id}")
        
        try:
            result = await self._proxy_to_backend(tool, params)
            return web.json_response({
                'success': True,
                'tool': tool,
                'result': result,
                'metadata': {
                    'execution_time_ms': 0,  # TODO: measure actual time
                    'timestamp': datetime.now().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Tool execution failed: {tool} - {e}")
            return web.json_response({
                'success': False,
                'error': {
                    'code': 'EXECUTION_ERROR',
                    'message': str(e)
                }
            }, status=500)
    
    async def _proxy_to_backend(self, tool: str, params: dict) -> Any:
        """Proxy request to actual MCP backend."""
        backend_port = self.config['proxy']['backend_port']
        backend_url = f"http://localhost:{backend_port}/mcp"
        
        # Special handling for built-in tools
        if tool == 'ping':
            return {'pong': True, 'timestamp': datetime.now().isoformat()}
        
        if tool == 'health':
            return {'status': 'healthy'}
        
        # Proxy to actual MCP server
        async with ClientSession() as session:
            async with session.post(
                backend_url,
                json={'tool': tool, 'params': params},
                timeout=30
            ) as response:
                return await response.json()
    
    def create_app(self) -> web.Application:
        """Create and configure the web application."""
        app = web.Application()
        
        # Routes
        app.router.add_get('/health', self.health_handler)
        app.router.add_get('/mcp/tools', self.tools_handler)
        app.router.add_post('/mcp', self.mcp_handler)
        
        # Add CORS headers
        async def cors_middleware(app, handler):
            async def middleware_handler(request):
                response = await handler(request)
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
                response.headers['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
                return response
            return middleware_handler
        
        app.middlewares.append(cors_middleware)
        
        return app
    
    def run(self, host: str | None = None, port: int | None = None):
        """Start the proxy server."""
        host = host or self.config['proxy']['listen_host']
        port = port or self.config['proxy']['listen_port']
        
        logger.info(f"MCP Auth Proxy starting on {host}:{port}")
        logger.info(f"Loaded {len(self.token_manager.tokens)} bearer tokens")
        logger.info(f"Allowed tools: {', '.join(sorted(self.allowed_tools))}")
        
        app = self.create_app()
        web.run_app(app, host=host, port=port, print=None)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='MCP Authentication Proxy')
    parser.add_argument('--config', type=Path, help='Config file path')
    parser.add_argument('--port', type=int, help='Listen port')
    parser.add_argument('--host', type=str, help='Listen host')
    args = parser.parse_args()
    
    if not AIOHTTP_AVAILABLE:
        print("ERROR: aiohttp is required. Install with: pip install aiohttp")
        sys.exit(1)
    
    config_path = args.config or Path('~/.claude/mcp-funnel/config.yaml').expanduser()
    
    proxy = MCPAuthProxy(config_path)
    proxy.run(host=args.host, port=args.port)


if __name__ == '__main__':
    main()
