#!/usr/bin/env python3
"""
Evidence Validator Hook
Enforces M3: No fabrication - Never claim without execution.

Validates that:
1. Evidence files exist at claimed locations
2. Evidence content proves the claim
3. Evidence is fresh (not stale)
4. Evidence format matches schema

Usage:
    python evidence_validator.py --evidence-path ./evidence/task.log --claim "Tests pass"
    python evidence_validator.py --validate-all .workflow/evidence/
    python evidence_validator.py --check-stale --max-age 3600
"""

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional


# ============================================================================
# EVIDENCE SCHEMA (from SCHEMAS.md)
# ============================================================================

EVIDENCE_SCHEMA = {
    "required": ["id", "type", "claim", "location", "timestamp", "verified", "verified_by"],
    "optional": ["hash", "verification_method"],
    "types": ["log", "output", "test_result", "diff", "screenshot", "api_response"],
    "verified_by": ["agent", "third-party", "user"],
    "id_pattern": r"^E-[A-Z]+-[\w.]+-\d{3}$"
}


# ============================================================================
# VALIDATORS
# ============================================================================

def validate_evidence_exists(location: str) -> tuple[bool, str]:
    """Check evidence file exists."""
    path = Path(location)
    if path.exists():
        return True, f"Evidence file exists: {location}"
    return False, f"Evidence file missing: {location}"


def validate_evidence_content(location: str, claim: str) -> tuple[bool, str]:
    """Check evidence content supports claim."""
    path = Path(location)
    
    if not path.exists():
        return False, "Evidence file does not exist"
    
    try:
        content = path.read_text()
    except Exception as e:
        return False, f"Cannot read evidence file: {e}"
    
    # Extract key terms from claim
    claim_terms = re.findall(r'\b\w{3,}\b', claim.lower())
    
    # Check for success indicators
    success_patterns = [
        r"(?i)(pass(ed)?|success(ful)?|complet(ed|e)|done)",
        r"(?i)exit\s*(code|status)?\s*[=:]\s*0",
        r"(?i)no\s*(errors?|failures?)",
        r"(?i)\d+\s+pass(ed)?.*0\s+fail"
    ]
    
    # Check for failure indicators
    failure_patterns = [
        r"(?i)(fail(ed|ure)?|error|exception)",
        r"(?i)exit\s*(code|status)?\s*[=:]\s*[1-9]",
        r"(?i)traceback",
        r"(?i)assert(ion)?\s*(error|fail)"
    ]
    
    has_success = any(re.search(p, content) for p in success_patterns)
    has_failure = any(re.search(p, content) for p in failure_patterns)
    
    # Determine if evidence proves claim
    if "pass" in claim.lower() or "success" in claim.lower() or "complete" in claim.lower():
        if has_failure:
            return False, "Evidence contains failure indicators"
        if has_success:
            return True, "Evidence confirms success"
        return False, "Evidence does not confirm claim"
    
    # For other claims, check term presence
    content_lower = content.lower()
    matching_terms = [t for t in claim_terms if t in content_lower]
    
    if len(matching_terms) >= len(claim_terms) * 0.5:
        return True, f"Evidence contains claim terms: {matching_terms}"
    
    return False, "Evidence does not support claim"


def validate_evidence_freshness(location: str, max_age_seconds: int = 3600) -> tuple[bool, str]:
    """Check evidence is not stale."""
    path = Path(location)
    
    if not path.exists():
        return False, "Evidence file does not exist"
    
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    now = datetime.now(timezone.utc)
    age = (now - mtime).total_seconds()
    
    if age > max_age_seconds:
        return False, f"Evidence is stale: {age:.0f}s old (max: {max_age_seconds}s)"
    
    return True, f"Evidence is fresh: {age:.0f}s old"


def compute_evidence_hash(location: str) -> str:
    """Compute SHA256 hash of evidence file."""
    path = Path(location)
    
    if not path.exists():
        return ""
    
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    
    return sha256.hexdigest()


def validate_evidence_schema(evidence: dict) -> tuple[bool, list[str]]:
    """Validate evidence against schema."""
    errors = []
    
    # Check required fields
    for field in EVIDENCE_SCHEMA["required"]:
        if field not in evidence:
            errors.append(f"Missing required field: {field}")
    
    # Check type enum
    if evidence.get("type") and evidence["type"] not in EVIDENCE_SCHEMA["types"]:
        errors.append(f"Invalid type: {evidence['type']}")
    
    # Check verified_by enum
    if evidence.get("verified_by") and evidence["verified_by"] not in EVIDENCE_SCHEMA["verified_by"]:
        errors.append(f"Invalid verified_by: {evidence['verified_by']}")
    
    # Check ID pattern
    if evidence.get("id"):
        if not re.match(EVIDENCE_SCHEMA["id_pattern"], evidence["id"]):
            errors.append(f"Invalid ID format: {evidence['id']}")
    
    return len(errors) == 0, errors


# ============================================================================
# FULL VALIDATION
# ============================================================================

def validate_evidence(
    evidence: dict,
    check_exists: bool = True,
    check_content: bool = True,
    check_fresh: bool = True,
    max_age: int = 3600
) -> dict:
    """
    Full evidence validation.
    """
    result = {
        "evidence_id": evidence.get("id", "unknown"),
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    # 1. Schema validation
    schema_valid, schema_errors = validate_evidence_schema(evidence)
    if not schema_valid:
        result["valid"] = False
        result["errors"].extend(schema_errors)
    
    location = evidence.get("location")
    claim = evidence.get("claim", "")
    
    if not location:
        result["valid"] = False
        result["errors"].append("No location specified")
        return result
    
    # 2. Existence check
    if check_exists:
        exists, msg = validate_evidence_exists(location)
        if not exists:
            result["valid"] = False
            result["errors"].append(msg)
            return result  # Can't continue without file
    
    # 3. Content check
    if check_content and claim:
        content_valid, msg = validate_evidence_content(location, claim)
        if not content_valid:
            result["valid"] = False
            result["errors"].append(msg)
    
    # 4. Freshness check
    if check_fresh:
        fresh, msg = validate_evidence_freshness(location, max_age)
        if not fresh:
            result["warnings"].append(msg)
    
    # 5. Compute hash
    result["hash"] = compute_evidence_hash(location)
    
    return result


def validate_all_evidence(directory: str, max_age: int = 3600) -> dict:
    """Validate all evidence in directory."""
    path = Path(directory)
    
    if not path.exists():
        return {"valid": False, "error": f"Directory not found: {directory}"}
    
    results = {
        "directory": str(path),
        "files_checked": 0,
        "valid_count": 0,
        "invalid_count": 0,
        "results": []
    }
    
    # Find evidence files
    for evidence_file in path.glob("*.json"):
        try:
            with open(evidence_file) as f:
                data = json.load(f)
            
            # Handle nested evidence
            if "evidence" in data:
                evidence = data["evidence"]
            else:
                evidence = data
            
            result = validate_evidence(evidence, max_age=max_age)
            result["file"] = str(evidence_file)
            results["results"].append(result)
            results["files_checked"] += 1
            
            if result["valid"]:
                results["valid_count"] += 1
            else:
                results["invalid_count"] += 1
        
        except json.JSONDecodeError as e:
            results["results"].append({
                "file": str(evidence_file),
                "valid": False,
                "errors": [f"Invalid JSON: {e}"]
            })
            results["invalid_count"] += 1
    
    # Also check log files
    for log_file in path.glob("*.log"):
        results["files_checked"] += 1
        
        # Check freshness only for logs
        fresh, msg = validate_evidence_freshness(str(log_file), max_age)
        
        results["results"].append({
            "file": str(log_file),
            "valid": fresh,
            "warnings": [] if fresh else [msg]
        })
        
        if fresh:
            results["valid_count"] += 1
        else:
            results["invalid_count"] += 1
    
    results["valid"] = results["invalid_count"] == 0
    
    return results


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Evidence Validator")
    parser.add_argument("--evidence-path", help="Single evidence file to validate")
    parser.add_argument("--claim", help="Claim the evidence should prove")
    parser.add_argument("--validate-all", help="Validate all evidence in directory")
    parser.add_argument("--check-stale", action="store_true", help="Check for stale evidence")
    parser.add_argument("--max-age", type=int, default=3600, help="Max age in seconds")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    
    args = parser.parse_args()
    
    if args.evidence_path:
        # Single evidence validation
        evidence = {
            "id": "E-CLI-001",
            "type": "log",
            "claim": args.claim or "Evidence valid",
            "location": args.evidence_path,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "verified": False,
            "verified_by": "agent"
        }
        
        result = validate_evidence(evidence, max_age=args.max_age)
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            status = "✅ VALID" if result["valid"] else "❌ INVALID"
            print(f"\n{status}: {args.evidence_path}")
            
            if result["errors"]:
                print("\nErrors:")
                for err in result["errors"]:
                    print(f"  ❌ {err}")
            
            if result["warnings"]:
                print("\nWarnings:")
                for warn in result["warnings"]:
                    print(f"  ⚠️  {warn}")
        
        return 0 if result["valid"] else 1
    
    elif args.validate_all:
        result = validate_all_evidence(args.validate_all, max_age=args.max_age)
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"\n{'='*60}")
            print(f"EVIDENCE VALIDATION: {args.validate_all}")
            print(f"{'='*60}")
            print(f"Files checked: {result['files_checked']}")
            print(f"Valid: {result['valid_count']}")
            print(f"Invalid: {result['invalid_count']}")
            
            for r in result["results"]:
                status = "✅" if r["valid"] else "❌"
                print(f"  {status} {r['file']}")
                for err in r.get("errors", []):
                    print(f"       ❌ {err}")
        
        return 0 if result["valid"] else 1
    
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
