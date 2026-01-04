#!/usr/bin/env python3
"""
Verification Before Completion Hook
Based on obra/superpowers verification-before-completion skill.

CORE PRINCIPLE: Evidence before claims, always.
Violating the letter of this rule is violating the spirit of this rule.

NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE.
If you haven't run the verification command in this message, you cannot claim it passes.

Usage:
    python verification_hook.py --claim "Tests pass" --command "pytest" --evidence ./logs/test.log
    python verification_hook.py --check-output output.json
"""

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ============================================================================
# VERIFICATION PATTERNS
# ============================================================================

COMPLETION_CLAIMS = [
    r"(?i)tests?\s+(pass|passed|passing)",
    r"(?i)all\s+(tests?)?\s*(green|pass)",
    r"(?i)(fixed|resolved|complete|done|working)",
    r"(?i)successfully\s+(implemented|created|built)",
    r"(?i)verified|confirmed|checked",
    r"(?i)no\s+(errors?|issues?|problems?)",
]

DISALLOWED_WITHOUT_EVIDENCE = [
    r"(?i)i('ve|'m|\s+have|\s+am)\s+(confident|sure|certain)",
    r"(?i)should\s+(work|pass|be\s+fixed)",
    r"(?i)looks?\s+(good|correct|right)",
    r"(?i)seems?\s+(to\s+)?(work|pass)",
]


def detect_completion_claim(text: str) -> list[str]:
    """Detect completion claims in text."""
    claims = []
    for pattern in COMPLETION_CLAIMS:
        if re.search(pattern, text):
            match = re.search(pattern, text)
            claims.append(match.group(0))
    return claims


def detect_speculation(text: str) -> list[str]:
    """Detect speculative language without evidence."""
    speculation = []
    for pattern in DISALLOWED_WITHOUT_EVIDENCE:
        if re.search(pattern, text):
            match = re.search(pattern, text)
            speculation.append(match.group(0))
    return speculation


# ============================================================================
# VERIFICATION EXECUTION
# ============================================================================

def run_verification(command: str, timeout: int = 300) -> dict:
    """Run verification command and capture evidence."""
    start = datetime.now(timezone.utc)
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        end = datetime.now(timezone.utc)
        
        return {
            "command": command,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0,
            "started_at": start.isoformat(),
            "completed_at": end.isoformat(),
            "duration_seconds": (end - start).total_seconds()
        }
    
    except subprocess.TimeoutExpired:
        return {
            "command": command,
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Command timed out after {timeout}s",
            "success": False,
            "started_at": start.isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": timeout
        }
    
    except Exception as e:
        return {
            "command": command,
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e),
            "success": False,
            "started_at": start.isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "duration_seconds": 0
        }


def verify_claim(claim: str, command: str, evidence_path: Optional[Path] = None) -> dict:
    """
    Verify a claim by running command and checking output.
    
    BEFORE claiming any status:
    1. IDENTIFY: What command proves this claim?
    2. RUN: Execute the FULL command (fresh, complete)
    3. READ: Full output, check exit code, count failures
    4. VERIFY: Does output confirm the claim?
    """
    
    # 1. IDENTIFY
    if not command:
        return {
            "claim": claim,
            "verified": False,
            "error": "No verification command provided",
            "action": "STOP"
        }
    
    # 2. RUN
    result = run_verification(command)
    
    # 3. READ
    output = result["stdout"] + result["stderr"]
    exit_code = result["exit_code"]
    
    # 4. VERIFY
    # Check for failure indicators
    failure_patterns = [
        r"(?i)fail(ed|ure|s)?",
        r"(?i)error",
        r"(?i)exception",
        r"(?i)assert(ion)?\s*(error|fail)",
        r"(?i)traceback"
    ]
    
    failures_found = []
    for pattern in failure_patterns:
        matches = re.findall(pattern, output)
        if matches:
            failures_found.extend(matches)
    
    verified = result["success"] and len(failures_found) == 0
    
    # Save evidence
    evidence = {
        "claim": claim,
        "command": command,
        "exit_code": exit_code,
        "output_length": len(output),
        "failures_found": failures_found,
        "verified": verified,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stdout_tail": result["stdout"][-500:] if result["stdout"] else "",
        "stderr_tail": result["stderr"][-500:] if result["stderr"] else ""
    }
    
    if evidence_path:
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        with open(evidence_path, "w") as f:
            json.dump(evidence, f, indent=2)
    
    return {
        "claim": claim,
        "verified": verified,
        "exit_code": exit_code,
        "failures_found": failures_found,
        "evidence_location": str(evidence_path) if evidence_path else None,
        "action": "PROCEED" if verified else "STOP"
    }


# ============================================================================
# OUTPUT CHECKER
# ============================================================================

def check_output_for_unverified_claims(output: dict | str) -> dict:
    """
    Check agent output for completion claims without verification.
    """
    if isinstance(output, str):
        text = output
    else:
        text = json.dumps(output)
    
    claims = detect_completion_claim(text)
    speculation = detect_speculation(text)
    
    # Check if evidence is present
    evidence_patterns = [
        r"evidence",
        r"log[_\s]?(file|path|location)",
        r"exit[_\s]?code",
        r"stdout",
        r"verified.*true"
    ]
    
    has_evidence = any(re.search(p, text, re.IGNORECASE) for p in evidence_patterns)
    
    violations = []
    
    if claims and not has_evidence:
        violations.append({
            "type": "UNVERIFIED_CLAIM",
            "claims": claims,
            "error": "Completion claims made without verification evidence"
        })
    
    if speculation:
        violations.append({
            "type": "SPECULATIVE_LANGUAGE",
            "phrases": speculation,
            "error": "Speculative language used instead of verification"
        })
    
    return {
        "valid": len(violations) == 0,
        "claims_found": claims,
        "speculation_found": speculation,
        "has_evidence": has_evidence,
        "violations": violations,
        "action": "PROCEED" if len(violations) == 0 else "STOP"
    }


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Verification Before Completion")
    parser.add_argument("--claim", help="Claim to verify")
    parser.add_argument("--command", help="Verification command")
    parser.add_argument("--evidence", help="Evidence output path")
    parser.add_argument("--check-output", help="Check output JSON for unverified claims")
    parser.add_argument("--check-text", help="Check text for unverified claims")
    
    args = parser.parse_args()
    
    if args.claim and args.command:
        evidence_path = Path(args.evidence) if args.evidence else None
        result = verify_claim(args.claim, args.command, evidence_path)
        print(json.dumps(result, indent=2))
        return 0 if result["verified"] else 1
    
    elif args.check_output:
        with open(args.check_output) as f:
            output = json.load(f)
        result = check_output_for_unverified_claims(output)
        print(json.dumps(result, indent=2))
        return 0 if result["valid"] else 1
    
    elif args.check_text:
        result = check_output_for_unverified_claims(args.check_text)
        print(json.dumps(result, indent=2))
        return 0 if result["valid"] else 1
    
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
