# WORKFLOW.md

**Version:** 4.0.0  
**Modified:** 2026-01-04T07:30:00Z  
**References:** `CLAUDE.md`, `SCHEMAS.md`, `RULES.md`

---

## Overview

```python
WORKFLOW = ["PLAN", "REVIEW", "DISRUPT", "IMPLEMENT", "TEST", "REVIEW", "VALIDATE", "LEARN"]
```

Each stage has:
- **CONFIG**: Model, agents, skills, MCP servers
- **INPUT**: Required files/data
- **PROCESS**: Step-by-step procedure
- **OUTPUT**: Templated output format
- **GATE**: Quality gate validation

---

## 0. STARTUP

```python
PROCEDURE startup():
    CONFIG:
        blocking = TRUE
        timeout = 60s
    
    # 0.1 MCP VERIFICATION
    mcp_servers = [
        "claude-context",
        "memory",
        "todo",
        "sequential-thinking",
        "git",
        "github",
        "scheduler",
        "openai-chat",
        "credentials",
        "mcp-gateway"
    ]
    
    FOR server IN mcp_servers:
        response = CALL {server}/ping
        IF response.status != "ok":
            RETURN {status: "FAIL", error: "MCP {server} not responding"}
    
    # 0.2 SCHEDULER SETUP
    CALL scheduler/create {
        id: "reprompt_timer",
        interval: "5m",
        action: "quality_gate_check"
    }
    
    CALL compaction/register_hook {
        event: "on_compact",
        action: "quality_gate_check"
    }
    
    verify = CALL scheduler/list
    IF "reprompt_timer" NOT IN verify.timers:
        RETURN {status: "FAIL", error: "Reprompt timer not created"}
    
    # 0.3 MEMORY TEST
    CALL memory/write key="startup_test" value=TIMESTAMP()
    read_result = CALL memory/read key="startup_test"
    IF read_result.value == NULL:
        RETURN {status: "FAIL", error: "Memory read/write failed"}
    
    # 0.4 WORKFLOW DIRECTORY
    workflow_id = FORMAT("{YYYYMMDD}_{HHMMSS}_{chat_id}")
    base_path = ".workflow/{workflow_id}/"
    
    directories = ["todo", "docs", "test", "plans", "evidence", "logs", "parallel"]
    
    FOR dir IN directories:
        MKDIR base_path + dir
        IF NOT EXISTS(base_path + dir):
            RETURN {status: "FAIL", error: "Failed to create {dir}"}
    
    RETURN {status: "PASS", workflow_id: workflow_id, base_path: base_path}
```

**Hook:** `hooks/startup_validator.py`  
**Exit:** PASS → continue, FAIL → TERMINATE

---

## 1. PLAN

```python
PROCEDURE plan(user_input):
    CONFIG:
        model = "Opus 4.5"
        agents = ["Planner", "Research"]
        skills = ["planning", "research"]
        mcp = ["memory", "todo", "claude-context"]
        timeout = 3m
    
    INPUT:
        user_input: string
    
    # 1.1 RESEARCH
    semantic_results = CALL claude-context/search query=user_input
    memory_results = CALL memory/search query=user_input
    
    IF semantic_results.count == 0 AND memory_results.count == 0:
        web_results = CALL web_search query=user_input
    ELSE:
        web_results = NULL
    
    research = {semantic: semantic_results, memory: memory_results, web: web_results}
    
    # 1.2 CREATE TODOS (17 fields each)
    todos = []
    FOR task IN decompose(user_input):
        todo = {
            id: GENERATE_ID(),
            content: task.description,
            status: "pending",
            priority: task.priority,
            metadata: {
                objective: task.objective,
                success_criteria: task.success_criteria,
                fail_criteria: task.fail_criteria,
                evidence_required: task.evidence_type,
                evidence_location: "{base_path}evidence/{todo.id}.log",
                agent_model: task.model,
                workflow: "PLAN→REVIEW→DISRUPT→IMPLEMENT→TEST→REVIEW→VALIDATE→LEARN",
                blocked_by: task.dependencies,
                parallel: task.can_parallel,
                workflow_stage: "PLAN",
                instructions_set: "CLAUDE.md",
                time_budget: task.time_estimate,
                reviewer: "gpt-5.2"
            }
        }
        
        # VALIDATE 17 FIELDS
        required = ["id", "content", "status", "priority",
                   "metadata.objective", "metadata.success_criteria", 
                   "metadata.fail_criteria", "metadata.evidence_required",
                   "metadata.evidence_location", "metadata.agent_model",
                   "metadata.workflow", "metadata.blocked_by", "metadata.parallel",
                   "metadata.workflow_stage", "metadata.instructions_set",
                   "metadata.time_budget", "metadata.reviewer"]
        
        FOR field IN required:
            IF GET_FIELD(todo, field) == NULL:
                RETURN {status: "FAIL", error: "Missing field: {field}"}
        
        APPEND(todos, todo)
    
    CALL todo/create_batch todos=todos
    
    # 1.3 DESIGN TESTS
    test_design = []
    FOR todo IN todos:
        test = {
            todo_id: todo.id,
            what: "Verify {todo.metadata.objective}",
            how: "Execute and check {todo.metadata.success_criteria}",
            when: "After IMPLEMENT completes {todo.id}",
            pass_command: "grep -q '{success_criteria}' {evidence_location}",
            fail_command: "grep -q '{fail_criteria}' {evidence_location}"
        }
        APPEND(test_design, test)
    
    WRITE "{base_path}test/design.json" content=JSON(test_design)
    
    # 1.4 OUTPUT (MANDATORY TEMPLATE)
    output = {
        startup_status: "PASS",
        user_input: user_input,
        objective: RESTATE(user_input),
        success_criteria: EXTRACT_CRITERIA(todos),
        evidence_required: EXTRACT_EVIDENCE(todos),
        evidence_locations: EXTRACT_LOCATIONS(todos),
        workflow_stages: WORKFLOW_TABLE,
        quality_gates: GATES_TABLE,
        todos: todos,
        third_party_status: "PENDING",
        changes: []
    }
    
    PRINT(FORMAT_PLAN_OUTPUT(output))
    
    # 1.5 AWAIT USER APPROVAL
    user_response = WAIT_FOR_INPUT()
    
    IF user_response == "APPROVED":
        RETURN {status: "APPROVED", todos: todos, test_design: test_design}
    ELSE:
        RETURN {status: "REJECTED", feedback: user_response}
```

**Gate:** User approval required  
**Exit:** APPROVED → REVIEW, REJECTED → revise PLAN

---

## 2. REVIEW

```python
PROCEDURE execute_review():
    CONFIG:
        model = "Opus 4.5"
        agents = ["Reviewer"]
        skills = ["verification-before-completion"]
        mcp = ["memory", "todo", "openai-chat"]
        timeout = 2m
    
    INPUT:
        plan = READ("{base_path}plans/plan.md")
        todos = PARSE_JSON(READ("{base_path}todo/todos.json"))
    
    # 2.1 VALIDATE TODOS HAVE 17 FIELDS
    FOR todo IN todos:
        validation = validate_todo_fields(todo)
        IF validation.status == "FAIL":
            RETURN {status: "FAIL", error: validation.error}
    
    # 2.2 CHECK RULE COMPLIANCE
    rules = LOAD_RULES("docs/RULES.md")
    FOR rule IN rules:
        compliance = check_rule(rule, plan, todos)
        IF compliance.status == "FAIL":
            RETURN {status: "FAIL", error: "Rule {rule.id} violated: {compliance.reason}"}
    
    # 2.3 IDENTIFY GAPS
    gaps = []
    FOR todo IN todos:
        IF todo.metadata.evidence_location == NULL:
            APPEND(gaps, {todo_id: todo.id, gap: "No evidence location"})
        IF todo.metadata.success_criteria == NULL:
            APPEND(gaps, {todo_id: todo.id, gap: "No success criteria"})
    
    # 2.4 WRITE REVIEW
    review = {
        timestamp: TIMESTAMP(),
        todos_validated: TRUE,
        rules_checked: LENGTH(rules),
        violations: 0,
        gaps: gaps
    }
    
    WRITE "{base_path}docs/REVIEW/review.json" content=JSON(review)
    
    OUTPUT:
        stage: "REVIEW"
        model: "Opus 4.5"
        agents: ["Reviewer"]
        todos_validated: TRUE
        rules_checked: LENGTH(rules)
        gaps: gaps
        evidence_location: "{base_path}docs/REVIEW/review.json"
        next_stage: "DISRUPT"
    
    RETURN {status: "PASS", output: output}
```

**Gate:** Stage gate validator  
**Exit:** PROCEED → DISRUPT, REVISE → retry REVIEW

---

## 3. DISRUPT

```python
PROCEDURE execute_disrupt():
    CONFIG:
        model = "Opus 4.5"
        agents = ["Disruptor", "Third-party"]
        skills = ["brainstorming", "planning"]
        mcp = ["sequential-thinking", "openai-chat"]
        timeout = 3m
    
    INPUT:
        plan = READ("{base_path}plans/plan.md")
        todos = PARSE_JSON(READ("{base_path}todo/todos.json"))
    
    # 3.1 EXTRACT ASSUMPTIONS
    assumptions = CALL sequential-thinking/analyze {
        input: plan,
        prompt: "List all assumptions"
    }
    
    # 3.2 CHALLENGE EACH ASSUMPTION
    challenges = []
    FOR assumption IN assumptions:
        counter = CALL sequential-thinking/analyze {
            input: assumption,
            prompt: "Generate counter-argument"
        }
        APPEND(challenges, {assumption: assumption, counter: counter})
    
    # 3.3 REALITY TEST EACH ASSUMPTION
    FOR challenge IN challenges:
        verification = {
            claim: challenge.assumption,
            test_command: GENERATE_TEST_COMMAND(challenge.assumption),
            expected_output: GENERATE_EXPECTED(challenge.assumption)
        }
        
        result = EXECUTE(verification.test_command)
        
        IF result.stdout CONTAINS verification.expected_output:
            challenge.reality_status = "VERIFIED"
        ELSE:
            challenge.reality_status = "REFUTED"
            challenge.actual_output = result.stdout
    
    # 3.4 THIRD-PARTY VALIDATION (BLOCKING)
    third_party_prompt = FORMAT("""
        SCOPE: Validate assumptions for plan
        SUCCESS CRITERIA: All assumptions verified or acknowledged
        
        ASSUMPTIONS:
        {challenges}
        
        TASK: Return APPROVED if valid, REJECTED with specifics if not.
    """)
    
    third_party_response = CALL openai-chat/complete {
        model: "gpt-5.2",
        prompt: third_party_prompt
    }
    
    IF "APPROVED" NOT IN third_party_response:
        RETURN {status: "FAIL", error: "Third-party rejected", feedback: third_party_response}
    
    # 3.5 WRITE DEBATE OUTPUT
    debate = {
        timestamp: TIMESTAMP(),
        assumptions: assumptions,
        challenges: challenges,
        third_party: third_party_response
    }
    
    WRITE "{base_path}docs/DISRUPT/debate.json" content=JSON(debate)
    
    OUTPUT:
        stage: "DISRUPT"
        model: "Opus 4.5"
        agents: ["Disruptor", "Third-party"]
        assumptions_count: LENGTH(assumptions)
        verified_count: COUNT(challenges WHERE reality_status == "VERIFIED")
        refuted_count: COUNT(challenges WHERE reality_status == "REFUTED")
        third_party_status: "APPROVED"
        evidence_location: "{base_path}docs/DISRUPT/debate.json"
        next_stage: "IMPLEMENT"
    
    RETURN {status: "PASS", output: output}
```

**Gate:** Third-party (GPT-5.2) approval required  
**Exit:** PROCEED → IMPLEMENT, REVISE → retry DISRUPT

---

## 4. IMPLEMENT

```python
PROCEDURE execute_implement():
    CONFIG:
        model = "Sonnet 4.5"
        agents = ["Executor", "Observer"]
        skills = ["executing-plans", "using-git-worktrees"]
        mcp = ["git", "github", "memory", "todo"]
        timeout = 5m
    
    INPUT:
        todos = PARSE_JSON(READ("{base_path}todo/todos.json"))
    
    # 4.1 PARALLEL EXECUTION (M40)
    pending_todos = FILTER(todos, status == "pending")
    
    IF LENGTH(pending_todos) >= 3:
        # MUST parallelize
        WITH ThreadPoolExecutor(max_workers=5) AS executor:
            futures = [executor.submit(implement_todo, t) FOR t IN pending_todos]
            results = [f.result() FOR f IN futures]
    ELSE:
        results = [implement_todo(t) FOR t IN pending_todos]
    
    # 4.2 IMPLEMENT EACH TODO
    PROCEDURE implement_todo(todo):
        CALL todo/update id=todo.id status="in_progress"
        
        # Generate code
        code = GENERATE_CODE(todo)
        
        # Validate no placeholders (M09)
        placeholder_check = EXECUTE("grep -rn 'TODO\\|FIXME\\|pass\\|\\.\\.\\.' {code.filepath}")
        IF placeholder_check.exit_code == 0:
            RETURN {status: "FAIL", error: "Placeholders found", matches: placeholder_check.stdout}
        
        # Validate types
        type_check = EXECUTE("grep -c 'def.*->' {code.filepath}")
        IF INT(type_check.stdout) == 0:
            RETURN {status: "FAIL", error: "No type hints"}
        
        # Validate docstrings
        docstring_check = EXECUTE("grep -c '\"\"\"' {code.filepath}")
        IF INT(docstring_check.stdout) == 0:
            RETURN {status: "FAIL", error: "No docstrings"}
        
        # Execute code
        exec_result = EXECUTE("python {code.filepath} > {todo.metadata.evidence_location} 2>&1")
        
        # Check for errors
        error_check = EXECUTE("grep -i 'error\\|exception\\|traceback' {evidence_location}")
        IF error_check.exit_code == 0:
            RETURN {status: "FAIL", error: "Execution errors", log: READ(evidence_location)}
        
        # Capture evidence
        evidence = {
            todo_id: todo.id,
            filepath: code.filepath,
            log_path: todo.metadata.evidence_location,
            log_tail: EXECUTE("tail -100 {evidence_location}").stdout,
            timestamp: TIMESTAMP()
        }
        
        WRITE "{base_path}evidence/{todo.id}.json" content=JSON(evidence)
        
        CALL todo/update id=todo.id status="completed" evidence_delivered=TRUE
        
        RETURN {status: "PASS", todo_id: todo.id}
    
    OUTPUT:
        stage: "IMPLEMENT"
        model: "Sonnet 4.5"
        agents: ["Executor", "Observer"]
        todos_completed: COUNT(results WHERE status == "PASS")
        files_created: LIST_FILES("{base_path}evidence/")
        evidence_location: "{base_path}evidence/"
        next_stage: "TEST"
    
    RETURN {status: "PASS", output: output}
```

**Gate:** Stage gate validator + verification hook  
**Exit:** PROCEED → TEST, REVISE → retry IMPLEMENT

---

## 5. TEST

```python
PROCEDURE execute_test():
    CONFIG:
        model = "Sonnet 4.5"
        agents = ["Tester"]
        skills = ["test-driven-development", "systematic-debugging"]
        mcp = ["git", "memory", "todo"]
        timeout = 3m
    
    INPUT:
        test_design = PARSE_JSON(READ("{base_path}test/design.json"))
        todos = PARSE_JSON(READ("{base_path}todo/todos.json"))
    
    # 5.1 UNIT TESTS
    unit_log = "{base_path}test/logs/unit.log"
    unit_result = EXECUTE("pytest tests/unit/ -v > {unit_log} 2>&1")
    unit_passed = INT(EXECUTE("grep -c 'PASSED' {unit_log}").stdout)
    unit_failed = INT(EXECUTE("grep -c 'FAILED' {unit_log}").stdout)
    
    IF unit_failed > 0:
        RETURN {status: "FAIL", stage: "TEST", substage: "unit", log: READ(unit_log)}
    
    # 5.2 INTEGRATION TESTS
    integration_log = "{base_path}test/logs/integration.log"
    integration_result = EXECUTE("pytest tests/integration/ -v > {integration_log} 2>&1")
    integration_passed = INT(EXECUTE("grep -c 'PASSED' {integration_log}").stdout)
    integration_failed = INT(EXECUTE("grep -c 'FAILED' {integration_log}").stdout)
    
    IF integration_failed > 0:
        RETURN {status: "FAIL", stage: "TEST", substage: "integration", log: READ(integration_log)}
    
    # 5.3 FULL TESTS
    full_log = "{base_path}test/logs/full.log"
    full_result = EXECUTE("pytest tests/ -v > {full_log} 2>&1")
    full_passed = INT(EXECUTE("grep -c 'PASSED' {full_log}").stdout)
    full_failed = INT(EXECUTE("grep -c 'FAILED' {full_log}").stdout)
    
    IF full_failed > 0:
        RETURN {status: "FAIL", stage: "TEST", substage: "full", log: READ(full_log)}
    
    # 5.4 VERIFY SUCCESS CRITERIA
    FOR todo IN todos:
        verify_result = EXECUTE("grep -q '{todo.metadata.success_criteria}' {todo.metadata.evidence_location}")
        IF verify_result.exit_code != 0:
            RETURN {status: "FAIL", todo_id: todo.id, error: "Success criteria not in evidence"}
    
    OUTPUT:
        stage: "TEST"
        model: "Sonnet 4.5"
        agents: ["Tester"]
        unit_passed: unit_passed
        unit_failed: unit_failed
        integration_passed: integration_passed
        integration_failed: integration_failed
        full_passed: full_passed
        full_failed: full_failed
        evidence_location: "{base_path}test/logs/"
        next_stage: "REVIEW"
    
    RETURN {status: "PASS", output: output}
```

**Gate:** All tests must pass  
**Exit:** PROCEED → REVIEW, FAIL → return to IMPLEMENT

---

## 6. REVIEW (Post-Implementation)

```python
PROCEDURE execute_review_post():
    CONFIG:
        model = "Opus 4.5"
        agents = ["Reviewer"]
        skills = ["verification-before-completion", "requesting-code-review"]
        mcp = ["github", "openai-chat", "memory"]
        timeout = 2m
    
    INPUT:
        todos = PARSE_JSON(READ("{base_path}todo/todos.json"))
        evidence_files = LIST_FILES("{base_path}evidence/")
        test_logs = LIST_FILES("{base_path}test/logs/")
    
    verification_results = []
    
    FOR todo IN todos:
        # 6.1 CHECK EVIDENCE EXISTS
        IF NOT EXISTS(todo.metadata.evidence_location):
            RETURN {status: "FAIL", error: "Evidence missing for {todo.id}"}
        
        # 6.2 CHECK EVIDENCE PROVES CLAIM
        evidence_content = READ(todo.metadata.evidence_location)
        
        proof_search = EXECUTE("grep -n '{todo.metadata.success_criteria}' {evidence_location}")
        
        IF proof_search.exit_code != 0:
            RETURN {status: "FAIL", error: "Evidence does not prove claim for {todo.id}"}
        
        APPEND(verification_results, {
            todo_id: todo.id,
            evidence_exists: TRUE,
            proof_found: TRUE,
            proof_lines: proof_search.stdout
        })
    
    # 6.3 WRITE REVIEW
    review = {
        timestamp: TIMESTAMP(),
        todos_verified: LENGTH(verification_results),
        all_evidence_exists: TRUE,
        all_proofs_found: TRUE,
        verifications: verification_results
    }
    
    WRITE "{base_path}docs/REVIEW_POST/review.json" content=JSON(review)
    
    OUTPUT:
        stage: "REVIEW"
        model: "Opus 4.5"
        agents: ["Reviewer"]
        todos_verified: LENGTH(verification_results)
        evidence_files: evidence_files
        test_logs: test_logs
        evidence_location: "{base_path}docs/REVIEW_POST/review.json"
        next_stage: "VALIDATE"
    
    RETURN {status: "PASS", output: output}
```

**Gate:** Evidence validator  
**Exit:** PROCEED → VALIDATE, REVISE → retry REVIEW

---

## 7. VALIDATE

```python
PROCEDURE execute_validate():
    CONFIG:
        model = "GPT-5.2"
        agents = ["Third-party", "Morality"]
        skills = ["verification-before-completion"]
        mcp = ["openai-chat", "memory"]
        timeout = 1m
    
    INPUT:
        plan = READ("{base_path}plans/plan.md")
        todos = PARSE_JSON(READ("{base_path}todo/todos.json"))
        evidence_files = LIST_FILES("{base_path}evidence/")
        test_logs = LIST_FILES("{base_path}test/logs/")
        reviews = [
            READ("{base_path}docs/REVIEW/review.json"),
            READ("{base_path}docs/DISRUPT/debate.json"),
            READ("{base_path}docs/REVIEW_POST/review.json")
        ]
    
    # 7.1 COMPILE EVIDENCE PACKAGE
    evidence_package = {
        plan: plan,
        todos: todos,
        evidence_count: LENGTH(evidence_files),
        test_log_count: LENGTH(test_logs),
        reviews: reviews
    }
    
    # 7.2 THIRD-PARTY VALIDATION (BLOCKING)
    third_party_prompt = FORMAT("""
        SCOPE: Final validation of workflow completion
        
        SUCCESS CRITERIA:
        - All todos completed with evidence
        - All evidence proves success criteria
        - All tests pass
        - All reviews pass
        - No violations
        
        EVIDENCE PACKAGE:
        {JSON(evidence_package)}
        
        TASK: Return APPROVED if all criteria met, REJECTED with specific gaps.
    """)
    
    third_party_response = CALL openai-chat/complete {
        model: "gpt-5.2",
        prompt: third_party_prompt
    }
    
    WRITE "{base_path}logs/gpt52_validate.json" content=JSON(third_party_response)
    
    IF "APPROVED" NOT IN third_party_response:
        RETURN {status: "FAIL", error: "Third-party rejected", feedback: third_party_response}
    
    # 7.3 MORALITY CHECK
    morality_issues = CHECK_ETHICS(plan, todos)
    IF LENGTH(morality_issues) > 0:
        RETURN {status: "FAIL", error: "Morality check failed", issues: morality_issues}
    
    OUTPUT:
        stage: "VALIDATE"
        model: "GPT-5.2"
        agents: ["Third-party", "Morality"]
        third_party_status: "APPROVED"
        morality_status: "PASS"
        evidence_location: "{base_path}logs/gpt52_validate.json"
        next_stage: "LEARN"
    
    RETURN {status: "PASS", output: output}
```

**Gate:** Third-party (GPT-5.2) approval + morality check  
**Exit:** PROCEED → LEARN, REVISE → retry VALIDATE

---

## 8. LEARN

```python
PROCEDURE execute_learn():
    CONFIG:
        model = "Haiku 4.5"
        agents = ["Learner"]
        skills = ["writing-skills", "memory-search"]
        mcp = ["memory", "claude-context"]
        timeout = 1m
    
    INPUT:
        todos = PARSE_JSON(READ("{base_path}todo/todos.json"))
        reviews = [
            READ("{base_path}docs/REVIEW/review.json"),
            READ("{base_path}docs/DISRUPT/debate.json"),
            READ("{base_path}docs/REVIEW_POST/review.json")
        ]
        violations = READ("{base_path}logs/violations.json") OR []
    
    # 8.1 EXTRACT LEARNINGS
    learnings = {
        successes: [],
        failures: [],
        assumptions_tested: [],
        improvements: []
    }
    
    FOR todo IN todos:
        IF todo.status == "completed":
            APPEND(learnings.successes, {todo_id: todo.id, what_worked: todo.content})
        ELSE:
            APPEND(learnings.failures, {todo_id: todo.id, what_failed: todo.content, reason: todo.blocked_by})
    
    FOR violation IN violations:
        APPEND(learnings.improvements, {
            stage: violation.stage,
            violation: violation.violation_type,
            prevention: GENERATE_PREVENTION(violation)
        })
    
    # 8.2 STORE TO MEMORY
    CALL memory/write {
        key: "{workflow_id}_learnings",
        value: JSON(learnings)
    }
    
    # 8.3 INDEX LEARNINGS
    CALL claude-context/index {
        content: JSON(learnings),
        metadata: {workflow_id: workflow_id, type: "learnings"}
    }
    
    # 8.4 WRITE LEARNINGS FILE
    WRITE "{base_path}docs/LEARN/learnings.json" content=JSON(learnings)
    
    OUTPUT:
        stage: "LEARN"
        model: "Haiku 4.5"
        agents: ["Learner"]
        successes: LENGTH(learnings.successes)
        failures: LENGTH(learnings.failures)
        improvements: LENGTH(learnings.improvements)
        memory_key: "{workflow_id}_learnings"
        evidence_location: "{base_path}docs/LEARN/learnings.json"
        next_stage: "COMPLETE"
    
    RETURN {status: "PASS", output: output}
```

**Gate:** Memory stored successfully  
**Exit:** COMPLETE

---

## Quality Gate Procedure

```python
PROCEDURE quality_gate(stage, output):
    # 1. CHECK TEMPLATE
    template = GET_TEMPLATE(stage)
    IF NOT MATCHES_TEMPLATE(output, template):
        RETURN {action: "REVISE", violation: "OUTPUT_NOT_TEMPLATED"}
    
    # 2. CHECK REQUIRED SECTIONS
    required_sections = GET_REQUIRED_SECTIONS(stage)
    FOR section IN required_sections:
        IF section NOT IN output:
            RETURN {action: "REVISE", violation: "MISSING_SECTION", section: section}
    
    # 3. CHECK EVIDENCE
    claims = EXTRACT_CLAIMS(output)
    FOR claim IN claims:
        IF claim.evidence_location != NULL:
            IF NOT EXISTS(claim.evidence_location):
                RETURN {action: "REVISE", violation: "MISSING_EVIDENCE", claim: claim.text}
            
            evidence_content = READ(claim.evidence_location)
            IF NOT CONTAINS(evidence_content, claim.success_keywords):
                RETURN {action: "REVISE", violation: "EVIDENCE_NOT_PROVING", claim: claim.text}
    
    # 4. THIRD-PARTY APPROVAL (DISRUPT, VALIDATE)
    IF stage IN ["DISRUPT", "VALIDATE"]:
        third_party = CALL openai-chat/complete {
            model: "gpt-5.2",
            prompt: FORMAT_REVIEW_PROMPT(stage, output)
        }
        
        IF "APPROVED" NOT IN third_party.response:
            RETURN {action: "REVISE", violation: "THIRD_PARTY_REJECTED", feedback: third_party.response}
    
    RETURN {action: "PROCEED"}
```

---

## Restart Agent Procedure

```python
PROCEDURE RESTART_AGENT(violation, stage):
    # 1. LOG VIOLATION
    violation_log = {
        timestamp: TIMESTAMP(),
        stage: stage,
        violation_type: violation.type,
        details: violation,
        agent_state: CAPTURE_STATE()
    }
    
    WRITE "{base_path}logs/violations.json" content=APPEND_JSON(violation_log)
    
    # 2. NOTIFY USER
    PRINT("""
    ================================================================================
    ⛔ QUALITY GATE FAILED
    ================================================================================
    Stage: {stage}
    Violation: {violation.type}
    Details: {violation.details}
    Action: RESTARTING AGENT FROM {stage}
    ================================================================================
    """)
    
    # 3. CLEAR INVALID STATE
    IF violation.type == "OUTPUT_NOT_TEMPLATED":
        CLEAR_LAST_OUTPUT()
    
    IF violation.type == "MISSING_EVIDENCE":
        CALL todo/update id=violation.todo_id status="blocked" blocked_by=["evidence_missing"]
    
    # 4. RESTART FROM STAGE
    GOTO stage
```

---

## END OF WORKFLOW.md
