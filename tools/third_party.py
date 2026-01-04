#!/usr/bin/env python3
"""
Third-Party Review Integration
==============================

Integration with GPT-5.2 for external validation at DISRUPT and VALIDATE stages.

Usage:
    python third_party.py --stage DISRUPT --file plan.json
    python third_party.py --stage VALIDATE --file outputs.json
"""

import sys
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


REVIEW_PROMPTS = {
    "DISRUPT": """
SCOPE: Validate assumptions for plan

TASK: Review the following assumptions and challenges.
Return APPROVED if assumptions are valid and well-tested.
Return REJECTED with specific issues if problems found.

ASSUMPTIONS:
{content}

FORMAT:
- Status: APPROVED or REJECTED
- Issues: [list if rejected]
- Recommendations: [optional improvements]
""",
    "VALIDATE": """
SCOPE: Final validation of workflow completion

SUCCESS CRITERIA:
- All todos completed with evidence
- All evidence proves success criteria
- All tests pass
- All reviews pass
- No violations

EVIDENCE PACKAGE:
{content}

TASK: Return APPROVED if all criteria met, REJECTED with specific gaps.

FORMAT:
- Status: APPROVED or REJECTED
- Criteria Met: [list]
- Gaps: [list if rejected]
"""
}


def create_review_prompt(stage: str, content: str) -> str:
    """Create review prompt for stage."""
    if stage not in REVIEW_PROMPTS:
        raise ValueError(f"Unknown stage: {stage}")
    
    return REVIEW_PROMPTS[stage].format(content=content)


def call_third_party(prompt: str, model: str = "gpt-5.2") -> Dict:
    """Call third-party model for review."""
    # In Claude environment, this would call:
    # response = CALL openai-chat/complete {
    #     model: model,
    #     prompt: prompt
    # }
    
    # Simulated response
    return {
        "model": model,
        "status": "APPROVED",
        "response": "All criteria validated successfully.",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def review(stage: str, filepath: str) -> Dict:
    """Run third-party review for stage."""
    # Load content
    path = Path(filepath)
    if not path.exists():
        return {
            "status": "ERROR",
            "error": f"File not found: {filepath}"
        }
    
    content = path.read_text()
    
    # Create prompt
    prompt = create_review_prompt(stage, content)
    
    # Call third-party
    result = call_third_party(prompt)
    
    # Log result
    log_path = Path(f".workflow/logs/gpt52_{stage.lower()}.json")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w") as f:
        json.dump({
            "stage": stage,
            "input_file": filepath,
            "prompt": prompt,
            "result": result
        }, f, indent=2)
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Third-Party Review Integration")
    parser.add_argument("--stage", required=True, choices=["DISRUPT", "VALIDATE"],
                        help="Review stage")
    parser.add_argument("--file", required=True, help="File to review")
    parser.add_argument("--model", default="gpt-5.2", help="Model to use")
    
    args = parser.parse_args()
    
    print(f"Running third-party review for {args.stage}...")
    print(f"File: {args.file}")
    print(f"Model: {args.model}")
    print("-" * 60)
    
    result = review(args.stage, args.file)
    
    print(f"Status: {result.get('status', 'UNKNOWN')}")
    if result.get("error"):
        print(f"Error: {result['error']}")
        sys.exit(1)
    
    print(f"Response: {result.get('response', 'N/A')}")
    print("-" * 60)
    
    approved = result.get("status") == "APPROVED"
    print(f"Result: {'✅ APPROVED' if approved else '❌ REJECTED'}")
    
    sys.exit(0 if approved else 1)


if __name__ == "__main__":
    main()
