#!/usr/bin/env python3
"""
Token Generator for MCP Auth Proxy
AGENTS 4.0 - Cloud Agent Gateway

Generates secure bearer tokens for cloud agent authentication.

Usage:
    python generate_tokens.py                       # Generate 3 tokens (default)
    python generate_tokens.py --count 5             # Generate 5 tokens
    python generate_tokens.py --output tokens.json  # Save to specific file
    python generate_tokens.py --expires 30          # Tokens expire in 30 days
    python generate_tokens.py --list                # List existing tokens
"""

import json
import secrets
import string
from datetime import datetime, timedelta
from pathlib import Path
import argparse


def generate_token(length: int = 43) -> str:
    """Generate a cryptographically secure random token."""
    # URL-safe base64-like characters
    alphabet = string.ascii_letters + string.digits + '-_'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def create_token_entry(
    purpose: str,
    expires_days: int | None = None
) -> dict:
    """Create a token entry with metadata."""
    now = datetime.now()
    
    entry = {
        'token': generate_token(),
        'purpose': purpose,
        'created': now.isoformat(),
        'created_human': now.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    if expires_days:
        expires = now + timedelta(days=expires_days)
        entry['expires'] = expires.isoformat()
        entry['expires_human'] = expires.strftime('%Y-%m-%d %H:%M:%S')
    
    return entry


def load_existing_tokens(path: Path) -> dict:
    """Load existing tokens file."""
    if not path.exists():
        return {'tokens': [], 'metadata': {}}
    
    try:
        with open(path) as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {'tokens': [], 'metadata': {}}


def save_tokens(data: dict, path: Path):
    """Save tokens to JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Set restrictive permissions (Unix only)
    try:
        path.chmod(0o600)
    except Exception:
        pass


def list_tokens(path: Path):
    """Display existing tokens (masked)."""
    data = load_existing_tokens(path)
    
    if not data['tokens']:
        print("No tokens found.")
        return
    
    print(f"\n{'Purpose':<25} {'Created':<20} {'Expires':<20} {'Token (masked)':<20}")
    print('=' * 90)
    
    for token in data['tokens']:
        purpose = token.get('purpose', 'unknown')[:24]
        created = token.get('created_human', 'unknown')[:19]
        expires = token.get('expires_human', 'never')[:19]
        masked = token['token'][:8] + '...' + token['token'][-4:]
        print(f"{purpose:<25} {created:<20} {expires:<20} {masked:<20}")
    
    print(f"\nTotal: {len(data['tokens'])} tokens")


def revoke_token(path: Path, token_prefix: str):
    """Revoke a token by prefix."""
    data = load_existing_tokens(path)
    
    original_count = len(data['tokens'])
    data['tokens'] = [
        t for t in data['tokens']
        if not t['token'].startswith(token_prefix)
    ]
    
    revoked = original_count - len(data['tokens'])
    
    if revoked > 0:
        save_tokens(data, path)
        print(f"✅ Revoked {revoked} token(s)")
    else:
        print(f"❌ No tokens found matching prefix: {token_prefix}")


def main():
    parser = argparse.ArgumentParser(
        description='Generate bearer tokens for MCP Auth Proxy'
    )
    parser.add_argument(
        '--count', '-n', type=int, default=3,
        help='Number of tokens to generate (default: 3)'
    )
    parser.add_argument(
        '--output', '-o', type=Path,
        default=Path('~/.credentials/mcp_tokens.json').expanduser(),
        help='Output file path'
    )
    parser.add_argument(
        '--expires', '-e', type=int,
        help='Days until expiration (default: never)'
    )
    parser.add_argument(
        '--purposes', '-p', nargs='+',
        help='Custom purposes for each token'
    )
    parser.add_argument(
        '--list', '-l', action='store_true',
        help='List existing tokens'
    )
    parser.add_argument(
        '--revoke', '-r', type=str,
        help='Revoke token by prefix'
    )
    parser.add_argument(
        '--append', '-a', action='store_true',
        help='Append to existing tokens instead of replacing'
    )
    
    args = parser.parse_args()
    output_path = args.output.expanduser()
    
    # List existing tokens
    if args.list:
        list_tokens(output_path)
        return
    
    # Revoke token
    if args.revoke:
        revoke_token(output_path, args.revoke)
        return
    
    # Generate new tokens
    default_purposes = [
        'claude_web_primary',
        'claude_code_primary',
        'rotation_backup'
    ]
    
    purposes = args.purposes or default_purposes[:args.count]
    
    # Extend purposes if needed
    while len(purposes) < args.count:
        purposes.append(f'backup_{len(purposes) + 1}')
    
    # Load or create token data
    if args.append:
        data = load_existing_tokens(output_path)
    else:
        data = {
            'tokens': [],
            'metadata': {
                'version': '1.0',
                'generated_at': datetime.now().isoformat(),
                'generator': 'generate_tokens.py'
            }
        }
    
    # Generate tokens
    new_tokens = []
    for i in range(args.count):
        purpose = purposes[i] if i < len(purposes) else f'token_{i + 1}'
        token_entry = create_token_entry(purpose, args.expires)
        data['tokens'].append(token_entry)
        new_tokens.append(token_entry)
    
    # Save
    save_tokens(data, output_path)
    
    # Display results
    print(f"\n✅ Generated {args.count} new token(s)")
    print(f"📁 Saved to: {output_path}")
    print()
    
    print("=" * 60)
    print("IMPORTANT: Copy these tokens now - they won't be shown again!")
    print("=" * 60)
    print()
    
    for token in new_tokens:
        print(f"Purpose: {token['purpose']}")
        print(f"Token:   {token['token']}")
        if 'expires_human' in token:
            print(f"Expires: {token['expires_human']}")
        print()
    
    print("=" * 60)
    print("⚠️  SECURITY REMINDERS:")
    print("  • Never commit tokens to git")
    print("  • Share one token per cloud agent instance")
    print("  • Rotate tokens every 30 days")
    print("  • Revoke immediately if compromised")
    print("=" * 60)


if __name__ == '__main__':
    main()
