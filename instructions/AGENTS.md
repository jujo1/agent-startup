# AGENTS.md

```yaml
VERSION: 5.0
MODIFIED: 2026-01-04T07:00:00Z
IMPORTS: SCHEMAS.md, SKILLS.md
HOOKS: stage_gate_validator.py, pre_compaction_hook.py, output_validator.py
```

---

## 0. CONSTANTS

```python
WORKFLOW = ["PLAN", "REVIEW", "DISRUPT", "IMPLEMENT", "TEST", "REVIEW", "VALIDATE", "LEARN"]

MODELS = {
    "planning": "Opus",
    "execution": "Sonnet", 
    "review": "gpt-5.2",
    "learn": "Haiku"
}

GATES = {
    "PLAN":      ["todo", "evidence"],
    "REVIEW":    ["review_gate", "evidence"],
    "DISRUPT":   ["conflict", "evidence"],
    "IMPLEMENT": ["todo", "evidence"],
    "TEST":      ["evidence", "metrics"],
    "VALIDATE":  ["review_gate", "evidence"],
    "LEARN":     ["skill", "metrics"]
}

MAX_RETRY = 3
TIMEOUT = "60m"
REPROMPT_INTERVAL = "5m"
```

---

## 1. MAIN WORKFLOW

```python
def main(user_input: str) -> Result:
    """Main workflow execution. All stages are MANDATORY."""
    
    # 1.1 STARTUP [BLOCKING]
    startup = startup_sequence()
    ASSERT startup.status == "PASS", f"Startup failed: {startup.error}"
    
    # 1.2 PLAN [BLOCKING]
    plan = create_plan(user_input)
    gate = quality_gate("PLAN", plan.outputs)
    ASSERT gate.action == "PROCEED", gate.errors
    
    # 1.3 USER APPROVAL [BLOCKING]
    approval = await_user("APPROVED|REJECTED")
    IF approval == "REJECTED":
        RETURN Result(status="REJECTED", feedback=approval.feedback)
    
    # 1.4 EXECUTE WORKFLOW STAGES
    FOR stage IN WORKFLOW[1:]:  # Skip PLAN (already done)
        
        # Execute stage
        output = execute_stage(stage)
        
        # Quality gate check
        gate = quality_gate(stage, output)
        
        # Handle gate result
        IF gate.action == "REVISE":
            output = retry_stage(stage, gate.errors, retry=1)
            gate = quality_gate(stage, output)
        
        IF gate.action == "ESCALATE":
            handoff = create_handoff(stage, gate)
            output = invoke_agent("Opus", handoff)
            gate = quality_gate(stage, output)
        
        IF gate.action == "STOP":
            recovery = create_recovery(stage, gate)
            RAISE WorkflowTerminated(recovery)
        
        ASSERT gate.action == "PROCEED", f"Gate failed: {gate.errors}"
    
    # 1.5 WORKFLOW COMPLETE
    RETURN Result(status="COMPLETE", evidence=collect_all_evidence())
```

---

## 2. STARTUP SEQUENCE

```python
def startup_sequence() -> StartupResult:
    """Initialize workflow. MUST pass before proceeding."""
    
    # 2.1 MCP PING (all servers)
    mcp_servers = [
        "memory", "todo", "sequential-thinking", "git", "github",
        "scheduler", "openai-chat", "credentials", "mcp-gateway"
    ]
    FOR server IN mcp_servers:
        response = CALL {server}/ping
        IF response.status != "ok":
            RETURN StartupResult(status="FAIL", error=f"MCP {server} down")
    
    # 2.2 SCHEDULER (timers)
    CALL scheduler/create {id: "reprompt_timer", interval: "5m", action: "quality_gate_check"}
    CALL scheduler/create {id: "compaction_hook", event: "pre_compact", action: "export_chat"}
    
    # 2.3 MEMORY (read/write test)
    test_key = f"startup_test_{SESSION.id}"
    CALL memory/write {key: test_key, value: TIMESTAMP()}
    result = CALL memory/read {key: test_key}
    IF result.value == NULL:
        RETURN StartupResult(status="FAIL", error="Memory read/write failed")
    
    # 2.4 WORKFLOW DIRECTORY
    workflow_id = FORMAT("{YYYYMMDD}_{HHMMSS}_{session}")
    FOR dir IN ["todo/", "evidence/", "logs/", "state/", "plans/", "test/"]:
        MKDIR f".workflow/{workflow_id}/{dir}"
    
    # 2.5 RETURN STARTUP RESULT [SCHEMA: startup]
    RETURN StartupResult(
        status="PASS",
        mcp_verified=True,
        scheduler_active=True,
        memory_ok=True,
        env_ready=True,
        workflow_dir=f".workflow/{workflow_id}/",
        timestamp=TIMESTAMP()
    )
```

---

## 3. CREATE PLAN

```python
def create_plan(user_input: str) -> PlanResult:
    """Create plan with todos and evidence. Output must match PLAN template."""
    
    # 3.1 RESEARCH (semantic search before grep)
    semantic = CALL semantic-index/search {query: user_input}
    memory = CALL memory/search {query: user_input}
    IF semantic.count == 0 AND memory.count == 0:
        web = CALL web_search {query: user_input}
    
    # 3.2 DECOMPOSE into tasks
    tasks = decompose_objective(user_input)
    
    # 3.3 CREATE TODOS [SCHEMA: todo × N]
    todos = []
    FOR i, task IN enumerate(tasks):
        todo = {
            "id": f"{i+1}.1",
            "content": task.description,
            "status": "pending",
            "priority": task.priority,
            "metadata": {
                "objective": task.objective,
                "success_criteria": task.success,
                "fail_criteria": task.fail,
                "evidence_required": task.evidence_type,
                "evidence_location": f".workflow/evidence/{i+1}.1.log",
                "agent_model": task.model,
                "workflow": "PLAN→REVIEW→DISRUPT→IMPLEMENT→TEST→REVIEW→VALIDATE→LEARN",
                "blocked_by": task.dependencies,
                "parallel": task.can_parallel,
                "workflow_stage": "PLAN",
                "instructions_set": "AGENTS.md",
                "time_budget": task.time,
                "reviewer": "gpt-5.2"
            }
        }
        VALIDATE todo AGAINST SCHEMAS.todo
        todos.append(todo)
    
    # 3.4 CREATE EVIDENCE [SCHEMA: evidence]
    evidence = {
        "id": f"E-PLAN-{SESSION.id[:8]}-001",
        "type": "output",
        "claim": f"Plan created with {len(todos)} todos",
        "location": ".workflow/plans/plan.json",
        "timestamp": TIMESTAMP(),
        "verified": True,
        "verified_by": "agent"
    }
    VALIDATE evidence AGAINST SCHEMAS.evidence
    
    # 3.5 SAVE AND OUTPUT
    WRITE ".workflow/plans/plan.json" todos
    WRITE ".workflow/evidence/plan.json" evidence
    
    PRINT format_plan_output(todos, evidence)  # Uses PLAN_OUTPUT_TEMPLATE
    
    RETURN PlanResult(outputs=[*todos, evidence])
```

---

## 4. QUALITY GATE

```python
def quality_gate(stage: str, outputs: list, retry: int = 0) -> GateResult:
    """Validate stage outputs against required schemas."""
    
    # 4.1 GET REQUIRED SCHEMAS for stage
    required = GATES[stage]
    
    # 4.2 VALIDATE EACH OUTPUT
    checked = []
    errors = []
    FOR output IN outputs:
        schema = detect_schema(output)
        IF schema:
            valid, errs = validate_schema(output, schema)
            checked.append(schema)
            IF NOT valid:
                errors.extend([f"[{schema}] {e}" FOR e IN errs])
    
    # 4.3 CHECK REQUIRED SCHEMAS PRESENT
    FOR req IN required:
        IF req NOT IN checked:
            errors.append(f"Missing required schema: {req}")
    
    # 4.4 CHECK EVIDENCE FILES EXIST
    FOR output IN outputs:
        IF "evidence" IN output:
            loc = output["evidence"].get("location")
            IF loc AND NOT FILE_EXISTS(loc):
                errors.append(f"Evidence file missing: {loc}")
    
    # 4.5 DETERMINE ACTION
    IF len(errors) == 0:
        action = "PROCEED"
    ELIF retry >= MAX_RETRY:
        action = "ESCALATE"
    ELIF len(errors) > 10:
        action = "STOP"
    ELSE:
        action = "REVISE"
    
    # 4.6 LOG GATE RESULT
    WRITE f".workflow/logs/gate_{stage.lower()}.json" {
        "stage": stage,
        "checked": checked,
        "errors": errors,
        "action": action,
        "retry": retry,
        "timestamp": TIMESTAMP()
    }
    
    # 4.7 GENERATE REPROMPT ON FAILURE
    IF action != "PROCEED":
        PRINT generate_reprompt(stage, errors, action, retry)
    
    RETURN GateResult(stage, checked, errors, action, retry)
```

---

## 5. AGENTS

### 5.1 Agent Definitions

```yaml
Planner:
  model: Opus
  stage: PLAN
  objective: Define complete solution path
  duties:
    - Research context (semantic search, memory, web)
    - Decompose objective into tasks
    - Create todos with 17 fields
    - Define success/fail criteria
    - Identify dependencies and parallel tasks
  success_criteria: All todos populated with evidence locations
  evidence: .workflow/plans/plan.json
  skills: [brainstorming, writing-plans]

Research:
  model: Opus
  stage: PLAN
  objective: Acquire domain knowledge
  duties:
    - Search semantic index
    - Search memory
    - Search web if needed
    - Identify relevant skills
  success_criteria: Knowledge gaps filled
  evidence: Search logs, sources
  skills: [brainstorming]

Reviewer:
  model: Opus
  stage: REVIEW
  objective: Validate plan/output quality
  duties:
    - Check schema compliance
    - Verify evidence exists
    - Check for gaps and assumptions
    - Approve or provide actionable feedback
  success_criteria: Plan approved or clear feedback
  evidence: .workflow/reviews/
  skills: [verification-before-completion]

Debate:
  model: Opus
  stage: DISRUPT
  objective: Stress-test assumptions
  duties:
    - List all assumptions
    - Generate counter-arguments
    - Challenge edge cases
    - Reality-test claims
  success_criteria: All assumptions tested
  evidence: .workflow/disrupt/
  skills: [brainstorming]

Third-party:
  model: gpt-5.2
  stage: [DISRUPT, VALIDATE]
  objective: External validation
  duties:
    - Independent review of plan/evidence
    - Check for blind spots
    - Approve or reject with reasons
  success_criteria: External approval
  evidence: API response log
  skills: [verification-before-completion]
  mcp: openai-chat

Executor:
  model: Sonnet
  stage: IMPLEMENT
  objective: Deliver working code
  duties:
    - Follow plan exactly
    - Write complete code (no placeholders)
    - Add logging to all operations
    - Run verification commands
  success_criteria: Code compiles, runs, tests pass
  evidence: Code + execution log
  skills: [executing-plans, test-driven-development]

Observer:
  model: Sonnet
  stage: IMPLEMENT
  objective: Monitor execution
  duties:
    - Track progress against plan
    - Flag deviations
    - Log all actions
  success_criteria: Deviations caught
  evidence: .workflow/observers/
  skills: [verification-before-completion]

Tester:
  model: Sonnet
  stage: TEST
  objective: Verify correctness
  duties:
    - Run unit tests
    - Run integration tests
    - Run full test suite
    - Capture all output
  success_criteria: All tests pass with evidence
  evidence: .workflow/test/logs/
  skills: [test-driven-development, systematic-debugging]

Morality:
  model: Opus
  stage: VALIDATE
  objective: Ensure ethical compliance
  duties:
    - Check for fabrication
    - Verify no placeholders
    - Confirm evidence matches claims
    - Check all rules followed
  success_criteria: All morality checks pass
  evidence: .workflow/morality/
  skills: [verification-before-completion]

Learn:
  model: Haiku
  stage: LEARN
  objective: Capture learnings
  duties:
    - Summarize successes and failures
    - Document improvements
    - Store in memory
    - Create skill if appropriate
  success_criteria: Learnings stored
  evidence: .workflow/learn/
  skills: [writing-skills]
```

### 5.2 Agents by Stage

| Stage | Agents | Model | Skills |
|-------|--------|-------|--------|
| PLAN | Planner, Research | Opus | brainstorming, writing-plans |
| REVIEW | Reviewer | Opus | verification-before-completion |
| DISRUPT | Debate, Third-party | Opus, gpt-5.2 | brainstorming |
| IMPLEMENT | Executor, Observer | Sonnet | executing-plans, TDD |
| TEST | Tester | Sonnet | TDD, systematic-debugging |
| REVIEW | Reviewer | Opus | verification-before-completion |
| VALIDATE | Third-party, Morality | gpt-5.2, Opus | verification-before-completion |
| LEARN | Learn | Haiku | writing-skills |

---

## 6. EXECUTE STAGE

```python
def execute_stage(stage: str) -> list:
    """Execute a workflow stage. Returns schema-validated outputs."""
    
    SWITCH stage:
    
    CASE "REVIEW":
        # Load and validate todos
        todos = LOAD ".workflow/todo/todos.json"
        FOR todo IN todos:
            VALIDATE todo AGAINST SCHEMAS.todo
        
        # Create review gate
        review = {
            "review_gate": {
                "stage": "REVIEW",
                "agent": "Opus",
                "timestamp": TIMESTAMP(),
                "criteria_checked": [
                    {"criterion": "17 fields present", "pass": True, "evidence": ".workflow/todo/"},
                    {"criterion": "No placeholders", "pass": NOT grep(todos, "TODO|FIXME|pass|\\.\\.\\.")}
                ],
                "approved": True,
                "action": "proceed"
            }
        }
        evidence = create_evidence("REVIEW", "Todos validated")
        RETURN [review, evidence]
    
    CASE "DISRUPT":
        # Challenge assumptions
        plan = LOAD ".workflow/plans/plan.json"
        assumptions = CALL sequential-thinking/analyze {input: plan, prompt: "List assumptions"}
        
        challenges = []
        FOR assumption IN assumptions:
            counter = CALL sequential-thinking/analyze {input: assumption, prompt: "Counter-argument"}
            test = EXECUTE verification_command(assumption)
            challenges.append({
                "assumption": assumption,
                "counter": counter,
                "verified": test.exit_code == 0
            })
        
        # Third-party review
        review = CALL openai-chat/complete {
            model: "gpt-5.2",
            prompt: f"Review this plan and assumptions: {plan}\n{assumptions}\nAPPROVED or REJECTED with reasons."
        }
        
        conflict = {
            "conflict": {
                "id": f"C-{TIMESTAMP_COMPACT()}",
                "type": "plan_disagreement",
                "parties": ["Planner", "Disruptor", "Third-party"],
                "positions": challenges,
                "resolution": {"decided_by": "gpt-5.2", "decision": review}
            }
        }
        evidence = create_evidence("DISRUPT", f"{len(challenges)} assumptions tested")
        RETURN [conflict, evidence]
    
    CASE "IMPLEMENT":
        todos = LOAD ".workflow/todo/todos.json"
        
        FOR todo IN todos WHERE todo.status == "pending":
            CALL todo/update {id: todo.id, status: "in_progress"}
            
            # Execute task
            code = generate_code(todo)
            
            # Validate code quality
            ASSERT NOT grep(code, "TODO|FIXME|pass|\\.\\.\\.")  # No placeholders
            ASSERT grep(code, "def.*->")  # Types present
            ASSERT grep(code, '"""')  # Docstrings present
            
            # Execute and capture output
            result = EXECUTE code
            WRITE todo.metadata.evidence_location result.log
            
            # Validate execution
            ASSERT NOT grep(result.log, "error|exception|traceback")
            
            CALL todo/update {id: todo.id, status: "completed"}
            
            evidence = create_evidence("IMPLEMENT", f"Todo {todo.id} complete",
                                       location=todo.metadata.evidence_location)
        
        RETURN [*todos, *evidences]
    
    CASE "TEST":
        # Run test suite
        unit = EXECUTE "pytest tests/unit/ -v"
        integration = EXECUTE "pytest tests/integration/ -v"
        full = EXECUTE "pytest tests/ -v"
        
        ASSERT unit.exit_code == 0, unit.stderr
        ASSERT integration.exit_code == 0, integration.stderr
        ASSERT full.exit_code == 0, full.stderr
        
        metrics = {
            "metrics": {
                "workflow_id": SESSION.workflow_id,
                "timestamp": TIMESTAMP(),
                "total_time_min": elapsed_minutes(),
                "stages": {"completed": 4, "failed": 0, "review_rejections": 0},
                "agents": {"tasks_assigned": len(todos), "tasks_completed": len(todos)},
                "evidence": {"claims": count_claims(), "verified": count_verified()},
                "quality": {"tests_passed": True, "rules_followed": 20}
            }
        }
        evidence = create_evidence("TEST", "All tests pass")
        RETURN [metrics, evidence]
    
    CASE "VALIDATE":
        # Third-party validation
        all_evidence = LOAD ".workflow/evidence/"
        
        response = CALL openai-chat/complete {
            model: "gpt-5.2",
            prompt: f"Validate this evidence. Return APPROVED or REJECTED with reasons.\n{all_evidence}"
        }
        
        review = {
            "review_gate": {
                "stage": "VALIDATE",
                "agent": "gpt-5.2",
                "timestamp": TIMESTAMP(),
                "criteria_checked": parse_criteria(response),
                "approved": "APPROVED" IN response,
                "action": "proceed" IF "APPROVED" IN response ELSE "revise",
                "feedback": response
            }
        }
        evidence = create_evidence("VALIDATE", "Third-party approved")
        RETURN [review, evidence]
    
    CASE "LEARN":
        # Capture learnings
        todos = LOAD ".workflow/todo/todos.json"
        violations = LOAD ".workflow/logs/violations.json" OR []
        
        learnings = {
            "successes": [t FOR t IN todos IF t.status == "completed"],
            "failures": [t FOR t IN todos IF t.status == "failed"],
            "improvements": [generate_prevention(v) FOR v IN violations]
        }
        
        # Store in memory
        CALL memory/write {key: f"{SESSION.id}_learnings", value: learnings}
        
        skill = {
            "skill": {
                "name": f"workflow_{SESSION.id[:8]}",
                "source": "LEARN stage",
                "purpose": "Captured learnings",
                "interface": "memory/read",
                "tested": True,
                "evidence_location": ".workflow/logs/learn.json"
            }
        }
        metrics = create_final_metrics()
        RETURN [skill, metrics]
```

---

## 7. RULES

```python
RULES = {
    # EVIDENCE (R01-R05)
    "R01": ("semantic_search_before_grep", "Always use semantic search before grep"),
    "R02": ("logging_present", "All operations must be logged"),
    "R03": ("no_error_hiding", "Never suppress or hide errors"),
    "R04": ("paths_tracked", "All file paths must be tracked"),
    "R05": ("evidence_exists", "Evidence file must exist at claimed location"),
    
    # CODE (R06-R10)
    "R06": ("types_present", "All functions must have type annotations"),
    "R07": ("absolute_paths", "Use absolute paths, not relative"),
    "R08": ("no_placeholders", "No TODO, FIXME, pass, or ... allowed"),
    "R09": ("no_fabrication", "Never claim without execution"),
    "R10": ("complete_code", "No partial implementations"),
    
    # WORKFLOW (R11-R15)
    "R11": ("parallel_for_3plus", "Use parallel execution for 3+ independent tasks"),
    "R12": ("memory_stored", "Store important discoveries in memory"),
    "R13": ("auto_transition", "Automatically transition to next stage"),
    "R14": ("observer_for_complex", "Complex tasks need Observer agent"),
    "R15": ("workflow_followed", "Must follow all 8 workflow stages"),
    
    # VALIDATION (R16-R20)
    "R16": ("checklist_complete", "All checklists must be completed"),
    "R17": ("reprompt_timer_active", "5-minute timer must be active"),
    "R18": ("review_gate_passed", "Review gate must pass before next stage"),
    "R19": ("quality_100_percent", "100% quality required"),
    "R20": ("third_party_approved", "gpt-5.2 must approve at DISRUPT and VALIDATE")
}

def check_rules(output: dict) -> list[str]:
    """Check all rules against output. Returns list of violations."""
    violations = []
    
    FOR rule_id, (rule_name, description) IN RULES.items():
        IF NOT check_rule(rule_name, output):
            violations.append(f"{rule_id}: {description}")
    
    RETURN violations

def check_rule(rule_name: str, output: dict) -> bool:
    """Check a single rule."""
    SWITCH rule_name:
        CASE "no_placeholders":
            RETURN NOT grep(str(output), r"TODO|FIXME|pass|\.\.\.")
        CASE "no_fabrication":
            RETURN output.get("evidence", {}).get("verified", False)
        CASE "complete_code":
            RETURN NOT grep(str(output), r"#\s*implement|#\s*add|#\s*todo")
        CASE "evidence_exists":
            loc = output.get("evidence", {}).get("location")
            RETURN NOT loc OR FILE_EXISTS(loc)
        DEFAULT:
            RETURN True
```

---

## 8. HELPER FUNCTIONS

```python
def create_evidence(stage: str, claim: str, location: str = None) -> dict:
    """Create evidence record with unique ID."""
    seq = get_next_seq(stage)
    evidence = {
        "evidence": {
            "id": f"E-{stage}-{SESSION.id[:8]}-{seq:03d}",
            "type": "log",
            "claim": claim,
            "location": location OR f".workflow/evidence/{stage.lower()}.log",
            "timestamp": TIMESTAMP(),
            "verified": True,
            "verified_by": "agent"
        }
    }
    VALIDATE evidence AGAINST SCHEMAS.evidence
    RETURN evidence


def create_handoff(stage: str, gate: GateResult) -> dict:
    """Create handoff for escalation to Opus."""
    handoff = {
        "handoff": {
            "from_agent": CURRENT_AGENT,
            "to_agent": "Opus",
            "timestamp": TIMESTAMP(),
            "context": {
                "user_objective": USER_OBJECTIVE,
                "current_stage": stage,
                "completed_stages": get_completed_stages(),
                "todos_remaining": get_pending_todos(),
                "evidence_collected": get_evidence_list(),
                "blockers": gate.errors,
                "assumptions": [],
                "memory_refs": []
            },
            "instructions": f"Quality gate failed at {stage}. Fix errors and continue.",
            "expected_output": f"Valid {stage} outputs passing quality gate",
            "deadline": TIMESTAMP(+30m)
        }
    }
    VALIDATE handoff AGAINST SCHEMAS.handoff
    RETURN handoff


def create_recovery(stage: str, gate: GateResult) -> dict:
    """Create recovery record for workflow termination."""
    recovery = {
        "recovery": {
            "id": f"R-{TIMESTAMP_COMPACT()}",
            "trigger": f"quality_gate_{gate.action}",
            "rollback_to": get_last_checkpoint(),
            "state_before": f".workflow/state/{stage}/before.json",
            "state_after": f".workflow/state/{stage}/after.json",
            "success": False,
            "resume_stage": stage
        }
    }
    VALIDATE recovery AGAINST SCHEMAS.recovery
    RETURN recovery


def generate_reprompt(stage: str, errors: list, action: str, retry: int) -> str:
    """Generate reprompt message for gate failure."""
    RETURN f"""
================================================================================
⛔ QUALITY GATE FAILED
================================================================================
STAGE:   {stage}
ATTEMPT: {retry + 1}/{MAX_RETRY}
ACTION:  {action}
--------------------------------------------------------------------------------
ERRORS ({len(errors)}):
{chr(10).join(f"  ❌ {e}" FOR e IN errors)}
--------------------------------------------------------------------------------
REQUIRED SCHEMAS: {GATES[stage]}
FIX: Address errors, resubmit with valid schemas
================================================================================
"""
```

---

## 9. MORALITY

```python
MORALITY = {
    "NEVER": [
        "fabricate",
        "hide errors",
        "use placeholders",
        "skip validation",
        "claim without evidence",
        "self-verify only",
        "break working systems"
    ],
    "ALWAYS": [
        "execute before claim",
        "validate against schema",
        "pass quality gate",
        "follow workflow stages",
        "store evidence",
        "get third-party review",
        "complete full request"
    ]
}
```
