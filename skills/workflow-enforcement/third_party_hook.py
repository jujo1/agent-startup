#!/usr/bin/env python3
"""
Third-Party Review Hook
Enforces M7: No self-review - Third-party reviews all.

Integrates with GPT-5.2 (or other models) for external validation.

Usage:
    python third_party_hook.py --review outputs.json --stage VALIDATE
    python third_party_hook.py --review-plan plan.json
    python third_party_hook.py --mock (for testing without API)
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ============================================================================
# REVIEW TEMPLATES
# ============================================================================

REVIEW_PROMPTS = {
    "PLAN": """
SCOPE: Validate plan for completeness and feasibility
SUCCESS CRITERIA:
- All todos have 17 fields
- Evidence locations defined
- No circular dependencies
- Time budgets realistic

PLAN:
{content}

TASK: Return APPROVED if criteria met, REJECTED with specific issues if not.
Format: APPROVED/REJECTED: <reason>
""",
    
    "REVIEW": """
SCOPE: Validate review stage output
SUCCESS CRITERIA:
- All todos validated
- No placeholder values
- Evidence files exist

REVIEW OUTPUT:
{content}

TASK: Return APPROVED if criteria met, REJECTED with specific issues if not.
Format: APPROVED/REJECTED: <reason>
""",
    
    "DISRUPT": """
SCOPE: Validate assumption testing
SUCCESS CRITERIA:
- All assumptions identified
- Counter-arguments provided
- Reality tests executed

DISRUPT OUTPUT:
{content}

TASK: Return APPROVED if criteria met, REJECTED with specific issues if not.
Format: APPROVED/REJECTED: <reason>
""",
    
    "VALIDATE": """
SCOPE: Final validation of workflow completion
SUCCESS CRITERIA:
- All todos completed with evidence
- All evidence proves success criteria
- All tests pass
- No violations

EVIDENCE PACKAGE:
{content}

TASK: Return APPROVED if all criteria met, REJECTED with specific gaps if not.
Format: APPROVED/REJECTED: <reason>
""",
    
    "LEARN": """
SCOPE: Validate learnings capture
SUCCESS CRITERIA:
- Successes documented
- Failures analyzed
- Improvements proposed

LEARNINGS:
{content}

TASK: Return APPROVED if criteria met, REJECTED with specific issues if not.
Format: APPROVED/REJECTED: <reason>
"""
}


# ============================================================================
# API CLIENTS
# ============================================================================

def call_openai(prompt: str, model: str = "gpt-4") -> dict:
    """Call OpenAI API for review."""
    try:
        import openai
        
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return {"error": "OPENAI_API_KEY not set", "success": False}
        
        client = openai.OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a strict code reviewer. Only approve if ALL criteria are met."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0
        )
        
        return {
            "success": True,
            "response": response.choices[0].message.content,
            "model": model
        }
    
    except ImportError:
        return {"error": "openai package not installed", "success": False}
    except Exception as e:
        return {"error": str(e), "success": False}


def call_anthropic(prompt: str, model: str = "claude-3-sonnet-20240229") -> dict:
    """Call Anthropic API for review."""
    try:
        import anthropic
        
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return {"error": "ANTHROPIC_API_KEY not set", "success": False}
        
        client = anthropic.Anthropic(api_key=api_key)
        
        response = client.messages.create(
            model=model,
            max_tokens=500,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return {
            "success": True,
            "response": response.content[0].text,
            "model": model
        }
    
    except ImportError:
        return {"error": "anthropic package not installed", "success": False}
    except Exception as e:
        return {"error": str(e), "success": False}


def mock_review(content: str, stage: str) -> dict:
    """Mock review for testing."""
    has_issues = False
    issues = []
    
    content_str = json.dumps(content) if isinstance(content, dict) else content
    
    # Check for common issues
    if "TODO" in content_str or "FIXME" in content_str:
        has_issues = True
        issues.append("Contains placeholder TODO/FIXME")
    
    if "error" in content_str.lower():
        if "fail_criteria" not in content_str.lower() and "stderr" not in content_str.lower():
            has_issues = True
            issues.append("Contains error indicators")
    
    if "..." in content_str and "workflow" not in content_str.lower():
        has_issues = True
        issues.append("Contains ellipsis placeholder")
    
    if has_issues:
        return {
            "success": True,
            "response": f"REJECTED: {'; '.join(issues)}",
            "model": "mock"
        }
    
    return {
        "success": True,
        "response": f"APPROVED: {stage} output meets all criteria",
        "model": "mock"
    }


# ============================================================================
# REVIEW EXECUTION
# ============================================================================

def execute_review(
    content: dict | str,
    stage: str,
    reviewer: str = "gpt-4",
    mock: bool = False
) -> dict:
    """
    Execute third-party review.
    
    M7: No self-review - must use external reviewer.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Get review prompt
    prompt_template = REVIEW_PROMPTS.get(stage, REVIEW_PROMPTS["VALIDATE"])
    
    content_str = json.dumps(content, indent=2) if isinstance(content, dict) else content
    prompt = prompt_template.format(content=content_str)
    
    # Execute review
    if mock:
        api_result = mock_review(content_str, stage)
    elif reviewer.startswith("gpt"):
        api_result = call_openai(prompt, model=reviewer)
    elif reviewer.startswith("claude"):
        api_result = call_anthropic(prompt, model=reviewer)
    else:
        api_result = mock_review(content_str, stage)
    
    # Parse result
    if not api_result.get("success"):
        return {
            "stage": stage,
            "reviewer": reviewer,
            "approved": False,
            "error": api_result.get("error"),
            "timestamp": timestamp
        }
    
    response = api_result["response"]
    approved = "APPROVED" in response.upper()
    
    # Extract reason
    if ":" in response:
        reason = response.split(":", 1)[1].strip()
    else:
        reason = response
    
    result = {
        "review_gate": {
            "stage": stage,
            "agent": api_result.get("model", reviewer),
            "timestamp": timestamp,
            "criteria_checked": [
                {"criterion": "Third-party review", "pass": approved, "evidence": "API response"}
            ],
            "approved": approved,
            "action": "proceed" if approved else "revise",
            "feedback": reason
        }
    }
    
    return result


def save_review(result: dict, output_path: Optional[Path] = None) -> Path:
    """Save review result to file."""
    if not output_path:
        output_path = Path(".workflow/logs") / f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    
    return output_path


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Third-Party Review Hook")
    parser.add_argument("--review", help="File to review")
    parser.add_argument("--stage", default="VALIDATE", choices=["PLAN", "REVIEW", "DISRUPT", "VALIDATE", "LEARN"])
    parser.add_argument("--reviewer", default="gpt-4", help="Reviewer model")
    parser.add_argument("--mock", action="store_true", help="Use mock reviewer")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--json", action="store_true", help="Output JSON only")
    
    args = parser.parse_args()
    
    if args.review:
        with open(args.review) as f:
            content = json.load(f)
        
        result = execute_review(
            content=content,
            stage=args.stage,
            reviewer=args.reviewer,
            mock=args.mock
        )
        
        if args.output:
            output_path = save_review(result, Path(args.output))
        else:
            output_path = save_review(result)
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            review = result.get("review_gate", result)
            approved = review.get("approved", False)
            
            print("=" * 60)
            print(f"THIRD-PARTY REVIEW: {args.stage}")
            print("=" * 60)
            print(f"Reviewer: {review.get('agent', args.reviewer)}")
            print(f"Status: {'✅ APPROVED' if approved else '❌ REJECTED'}")
            print(f"Feedback: {review.get('feedback', 'N/A')}")
            print(f"Output: {output_path}")
        
        return 0 if result.get("review_gate", {}).get("approved", False) else 1
    
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
