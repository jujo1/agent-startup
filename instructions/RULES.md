# RULES.md

**Version:** 4.0.0  
**Modified:** 2026-01-04T07:30:00Z  
**References:** `CLAUDE.md`, `WORKFLOW.md`

---

## Rule Categories

| Category | Rules | Description |
|----------|-------|-------------|
| Search | R01 | Semantic before grep |
| Logging | R02-R03 | Logging, no error hiding |
| Paths | R04, R07-R08 | Track, absolute, cross-platform |
| Code | R05-R06, R09-R10 | Skills, types, evidence, no placeholders |
| Integrity | R11 | No fabrication |
| Execution | R12-R16 | Parallel, memory, transitions |
| Scope | R17-R18 | Complete scope, workflow |
| Evidence | R26-R30 | Verification |
| Third-Party | R31-R35 | External review |
| Memory | R36-R40 | Storage |
| Quality | R51-R54 | Final checks |

---

## Critical Rules (TERMINATE on fail)

| Rule | Name | Description |
|------|------|-------------|
| R11 | no_fabrication | Never claim without execution evidence |
| R51 | checklist_complete | All checklist items must pass |
| R52 | reprompt_timer_active | Reprompt timer must be running |
| R54 | quality_100_percent | 100% quality gate compliance |

---

## All Rules

```python
RULES = {
    # SEARCH
    "R01": {name: "semantic_search_before_grep", fail: "RESTART"},
    
    # LOGGING
    "R02": {name: "logging_present", fail: "RESTART"},
    "R03": {name: "no_error_hiding", fail: "RESTART"},
    
    # PATHS
    "R04": {name: "paths_tracked", fail: "RESTART"},
    "R07": {name: "absolute_paths", fail: "RESTART"},
    "R08": {name: "cross_platform_paths", fail: "RESTART"},
    
    # CODE
    "R05": {name: "skills_used", fail: "RESTART"},
    "R06": {name: "types_present", fail: "RESTART"},
    "R09": {name: "evidence_exists", fail: "RESTART"},
    "R10": {name: "no_placeholders", fail: "RESTART"},
    
    # INTEGRITY
    "R11": {name: "no_fabrication", fail: "TERMINATE"},
    
    # EXECUTION
    "R12": {name: "parallel_for_3plus", fail: "RESTART"},
    "R13": {name: "memory_stored", fail: "RESTART"},
    "R14": {name: "auto_transition", fail: "RESTART"},
    "R15": {name: "observer_for_complex", fail: "RESTART"},
    "R16": {name: "sequential_thinking_used", fail: "RESTART"},
    
    # SCOPE
    "R17": {name: "complete_scope", fail: "RESTART"},
    "R18": {name: "workflow_followed", fail: "RESTART"},
    
    # EVIDENCE
    "R26": {name: "evidence_before_claim", fail: "RESTART"},
    "R27": {name: "evidence_proves_claim", fail: "RESTART"},
    "R28": {name: "evidence_not_stale", fail: "RESTART"},
    "R29": {name: "evidence_hashed", fail: "RESTART"},
    "R30": {name: "evidence_schema_valid", fail: "RESTART"},
    
    # THIRD-PARTY
    "R31": {name: "no_self_review", fail: "RESTART"},
    "R32": {name: "third_party_at_disrupt", fail: "RESTART"},
    "R33": {name: "third_party_at_validate", fail: "RESTART"},
    "R34": {name: "third_party_logged", fail: "RESTART"},
    "R35": {name: "third_party_approval_required", fail: "RESTART"},
    
    # MEMORY
    "R36": {name: "memory_first_startup", fail: "RESTART"},
    "R37": {name: "memory_search_before_ask", fail: "RESTART"},
    "R38": {name: "credentials_from_store", fail: "RESTART"},
    "R39": {name: "store_discoveries", fail: "RESTART"},
    "R40": {name: "parallel_mandate", fail: "RESTART"},
    
    # QUALITY
    "R51": {name: "checklist_complete", fail: "TERMINATE"},
    "R52": {name: "reprompt_timer_active", fail: "TERMINATE"},
    "R53": {name: "review_gate_passed", fail: "RESTART"},
    "R54": {name: "quality_100_percent", fail: "TERMINATE"}
}
```

---

## Enforcement

```python
PROCEDURE check_rule(rule_id, context):
    rule = RULES[rule_id]
    
    SWITCH rule.name:
        CASE "no_placeholders":
            RETURN NOT grep(context.code, "TODO|FIXME|XXX|pass|\\.\\.\\.")
        
        CASE "no_fabrication":
            FOR claim IN context.claims:
                IF NOT exists(claim.evidence_location):
                    RETURN FALSE
                IF NOT proves(claim.evidence_location, claim.success_criteria):
                    RETURN FALSE
            RETURN TRUE
        
        CASE "parallel_for_3plus":
            RETURN len(context.tasks) < 3 OR context.executed_parallel
        
        CASE "evidence_proves_claim":
            evidence = read(context.evidence_location)
            RETURN context.success_criteria IN evidence
        
        CASE "no_self_review":
            RETURN context.reviewer != context.author
        
        DEFAULT:
            RETURN TRUE

PROCEDURE enforce_all_rules(context):
    violations = []
    
    FOR rule_id IN RULES:
        IF NOT check_rule(rule_id, context):
            violations.append(rule_id)
    
    # Check for TERMINATE violations
    terminate_rules = ["R11", "R51", "R52", "R54"]
    FOR v IN violations:
        IF v IN terminate_rules:
            TERMINATE(f"Critical rule violated: {v}")
    
    IF len(violations) > 0:
        RETURN {action: "RESTART", violations: violations}
    
    RETURN {action: "PROCEED"}
```

---

## Morality (Non-Negotiable)

```
NEVER fabricate evidence
NEVER hide errors
NEVER use placeholders (TODO, FIXME, ..., pass)
NEVER claim without execution
NEVER self-review
NEVER skip quality gates
ALWAYS execute before claim
ALWAYS validate against schema
ALWAYS use third-party review
ALWAYS provide evidence with claims
```

---

## END OF RULES.md
