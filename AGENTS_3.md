# AGENTS_3.md

**Keywords:** agent, workflow, procedural, MCP, evidence, gates  
**Created:** 2026-01-04T00:00:00Z  
**Modified:** 2026-01-04T07:00:00Z  
**References:** `CLAUDE_2.md`, `SCHEMAS.md`

---

```
################################################################################
# MAIN ENTRY POINT
################################################################################

PROCEDURE main(user_input):
    
    startup_result = startup()
    IF startup_result.status != "PASS":
        TERMINATE("Startup failed: {startup_result.error}")
    
    plan_result = plan(user_input)
    IF plan_result.status != "APPROVED":
        TERMINATE("Plan rejected: {plan_result.feedback}")
    
    LOOP:
        stage_result = execute_stage(current_stage)
        gate_result = quality_gate(current_stage, stage_result)
        
        IF gate_result.status == "FAIL":
            log_violation(gate_result)
            RESTART_AGENT(violation=gate_result.violation, stage=current_stage)
        
        IF gate_result.status == "PASS":
            current_stage = next_stage(current_stage)
        
        IF current_stage == "COMPLETE":
            BREAK
    
    RETURN final_output()

################################################################################
# 0. STARTUP
################################################################################

PROCEDURE startup():
    
    # 0.1 MCP VERIFICATION
    # INPUT: None
    # PROCESS: Ping each MCP server
    # OUTPUT: mcp_status object
    
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
    # INPUT: None
    # PROCESS: Create reprompt timer and compaction hook
    # OUTPUT: scheduler_status
    
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
    # INPUT: None
    # PROCESS: Read and write test
    # OUTPUT: memory_status
    
    CALL memory/write key="startup_test" value=TIMESTAMP()
    read_result = CALL memory/read key="startup_test"
    IF read_result.value == NULL:
        RETURN {status: "FAIL", error: "Memory read/write failed"}
    
    # 0.4 WORKFLOW DIRECTORY
    # INPUT: None
    # PROCESS: Create directory structure
    # OUTPUT: directory paths
    
    workflow_id = FORMAT("{YYYYMMDD}_{HHMMSS}_{chat_id}")
    base_path = "./.workflow/{workflow_id}/"
    
    directories = [
        "todo/",
        "docs/",
        "test/",
        "plans/",
        "evidence/",
        "logs/",
        "parallel/"
    ]
    
    FOR dir IN directories:
        MKDIR base_path + dir
        IF NOT EXISTS(base_path + dir):
            RETURN {status: "FAIL", error: "Failed to create {dir}"}
    
    RETURN {status: "PASS", workflow_id: workflow_id, base_path: base_path}

################################################################################
# 1. PLAN
################################################################################

PROCEDURE plan(user_input):
    
    # INPUT: user_input (string)
    # PROCESS: Research, create todos, design tests
    # OUTPUT: Templated plan (ONLY THIS FORMAT PERMITTED)
    
    # 1.1 RESEARCH
    # INPUT: user_input
    # PROCESS: Search semantic index, memory, web
    # OUTPUT: research_results
    
    semantic_results = CALL claude-context/search query=user_input
    memory_results = CALL memory/search query=user_input
    
    IF semantic_results.count == 0 AND memory_results.count == 0:
        web_results = CALL web_search query=user_input
    ELSE:
        web_results = NULL
    
    research_results = {
        semantic: semantic_results,
        memory: memory_results,
        web: web_results
    }
    
    # 1.2 CREATE TODOS
    # INPUT: user_input, research_results
    # PROCESS: Generate todos with ALL 17 fields
    # OUTPUT: todos array
    
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
                workflow: "PLANâ†’REVIEWâ†’DISRUPTâ†’IMPLEMENTâ†’TESTâ†’REVIEWâ†’VALIDATEâ†’LEARN",
                blocked_by: task.dependencies,
                parallel: task.can_parallel,
                workflow_stage: "PLAN",
                instructions_set: "AGENTS_3.md",
                time_budget: task.time_estimate,
                reviewer: "gpt-5.2"
            }
        }
        
        # VALIDATE TODO HAS ALL 17 FIELDS
        required_fields = [
            "id", "content", "status", "priority",
            "metadata.objective", "metadata.success_criteria", "metadata.fail_criteria",
            "metadata.evidence_required", "metadata.evidence_location", "metadata.agent_model",
            "metadata.workflow", "metadata.blocked_by", "metadata.parallel",
            "metadata.workflow_stage", "metadata.instructions_set", "metadata.time_budget",
            "metadata.reviewer"
        ]
        
        FOR field IN required_fields:
            IF GET_FIELD(todo, field) == NULL:
                RETURN {status: "FAIL", error: "Todo missing field: {field}"}
        
        APPEND(todos, todo)
    
    CALL todo/create_batch todos=todos
    
    # 1.3 DESIGN TESTS
    # INPUT: todos
    # PROCESS: Define test for each todo
    # OUTPUT: test_design
    
    test_design = []
    FOR todo IN todos:
        test = {
            todo_id: todo.id,
            what: "Verify {todo.metadata.objective}",
            how: "Execute and check {todo.metadata.success_criteria}",
            when: "After IMPLEMENT stage completes {todo.id}",
            pass_command: "grep -q '{todo.metadata.success_criteria}' {todo.metadata.evidence_location}",
            fail_command: "grep -q '{todo.metadata.fail_criteria}' {todo.metadata.evidence_location}"
        }
        APPEND(test_design, test)
    
    WRITE "{base_path}test/design.json" content=JSON(test_design)
    
    # 1.4 OUTPUT PLAN (MANDATORY TEMPLATE)
    # INPUT: All above
    # PROCESS: Format output
    # OUTPUT: Templated plan string
    
    output = FORMAT_PLAN_OUTPUT(
        startup_status: "PASS",
        user_input: user_input,
        objective: RESTATE(user_input),
        success_criteria: EXTRACT_CRITERIA(todos),
        evidence_required: EXTRACT_EVIDENCE(todos),
        evidence_locations: EXTRACT_LOCATIONS(todos),
        workflow_stages: WORKFLOW_TABLE(),
        quality_gates: GATES_TABLE(),
        todos: todos,
        third_party_status: "PENDING",
        changes: []
    )
    
    PRINT(output)
    
    # 1.5 QUALITY GATE: PLAN
    # INPUT: output
    # PROCESS: Validate output matches template
    # OUTPUT: gate_result
    
    gate_result = quality_gate("PLAN", output)
    IF gate_result.status == "FAIL":
        RESTART_AGENT(violation=gate_result.violation, stage="PLAN")
    
    # 1.6 AWAIT USER APPROVAL
    user_response = WAIT_FOR_INPUT()
    
    IF user_response == "APPROVED":
        RETURN {status: "APPROVED", todos: todos, test_design: test_design}
    ELSE:
        RETURN {status: "REJECTED", feedback: user_response}

################################################################################
# 2. QUALITY GATE (HOOK)
################################################################################

PROCEDURE quality_gate(stage, output):
    
    # INPUT: stage name, agent output
    # PROCESS: Validate output against template
    # OUTPUT: PASS or FAIL with violation details
    
    # 2.1 CHECK OUTPUT IS TEMPLATED
    template = GET_TEMPLATE(stage)
    
    IF NOT MATCHES_TEMPLATE(output, template):
        RETURN {
            status: "FAIL",
            violation: "OUTPUT_NOT_TEMPLATED",
            expected: template,
            actual: output,
            stage: stage
        }
    
    # 2.2 CHECK ALL REQUIRED SECTIONS PRESENT
    required_sections = GET_REQUIRED_SECTIONS(stage)
    
    FOR section IN required_sections:
        IF section NOT IN output:
            RETURN {
                status: "FAIL",
                violation: "MISSING_SECTION",
                section: section,
                stage: stage
            }
    
    # 2.3 CHECK EVIDENCE EXISTS FOR CLAIMS
    claims = EXTRACT_CLAIMS(output)
    
    FOR claim IN claims:
        IF claim.evidence_location != NULL:
            IF NOT EXISTS(claim.evidence_location):
                RETURN {
                    status: "FAIL",
                    violation: "MISSING_EVIDENCE",
                    claim: claim.text,
                    expected_path: claim.evidence_location,
                    stage: stage
                }
            
            evidence_content = READ(claim.evidence_location)
            IF NOT CONTAINS(evidence_content, claim.success_keywords):
                RETURN {
                    status: "FAIL",
                    violation: "EVIDENCE_NOT_PROVING",
                    claim: claim.text,
                    evidence_path: claim.evidence_location,
                    stage: stage
                }
    
    # 2.4 CHECK THIRD-PARTY APPROVAL (if required)
    IF stage IN ["DISRUPT", "VALIDATE"]:
        third_party_result = CALL openai-chat/complete {
            model: "gpt-5.2",
            prompt: FORMAT_THIRD_PARTY_PROMPT(stage, output)
        }
        
        IF "APPROVED" NOT IN third_party_result.response:
            RETURN {
                status: "FAIL",
                violation: "THIRD_PARTY_REJECTED",
                feedback: third_party_result.response,
                stage: stage
            }
    
    RETURN {status: "PASS", stage: stage}

################################################################################
# 3. RESTART AGENT (HOOK)
################################################################################

PROCEDURE RESTART_AGENT(violation, stage):
    
    # INPUT: violation details, current stage
    # PROCESS: Log violation, clear state, restart from stage
    # OUTPUT: None (restarts execution)
    
    # 3.1 LOG VIOLATION
    violation_log = {
        timestamp: TIMESTAMP(),
        stage: stage,
        violation_type: violation.type,
        details: violation,
        agent_state: CAPTURE_STATE()
    }
    
    WRITE "{base_path}logs/violations.json" content=APPEND_JSON(violation_log)
    
    # 3.2 NOTIFY USER
    PRINT("=" * 60)
    PRINT("â›” QUALITY GATE FAILED")
    PRINT("=" * 60)
    PRINT("Stage: {stage}")
    PRINT("Violation: {violation.type}")
    PRINT("Details: {violation.details}")
    PRINT("Action: RESTARTING AGENT FROM {stage}")
    PRINT("=" * 60)
    
    # 3.3 CLEAR INVALID STATE
    IF violation.type == "OUTPUT_NOT_TEMPLATED":
        # Clear the non-templated output
        CLEAR_LAST_OUTPUT()
    
    IF violation.type == "MISSING_EVIDENCE":
        # Mark todo as blocked
        CALL todo/update id=violation.todo_id status="blocked" blocked_by=["evidence_missing"]
    
    # 3.4 RESTART FROM STAGE
    GOTO stage

################################################################################
# 4. EXECUTE STAGE
################################################################################

PROCEDURE execute_stage(stage):
    
    SWITCH stage:
        
        CASE "REVIEW":
            RETURN execute_review()
        
        CASE "DISRUPT":
            RETURN execute_disrupt()
        
        CASE "IMPLEMENT":
            RETURN execute_implement()
        
        CASE "TEST":
            RETURN execute_test()
        
        CASE "REVIEW_POST":
            RETURN execute_review_post()
        
        CASE "VALIDATE":
            RETURN execute_validate()
        
        CASE "LEARN":
            RETURN execute_learn()

################################################################################
# 4.1 REVIEW STAGE
################################################################################

PROCEDURE execute_review():
    
    # CONFIG
    model = "Opus 4.5"
    agents = ["Reviewer"]
    skills = ["/verification-before-completion"]
    mcp = ["memory", "todo", "openai-chat"]
    
    # INPUT
    plan_file = READ("{base_path}plans/plan.md")
    todos_file = READ("{base_path}todo/todos.json")
    
    # PROCESS
    # 4.1.1 Validate todos have 17 fields
    todos = PARSE_JSON(todos_file)
    FOR todo IN todos:
        validation = validate_todo_fields(todo)
        IF validation.status == "FAIL":
            RETURN {status: "FAIL", error: validation.error}
    
    # 4.1.2 Check rule compliance
    rules = [R1, R2, R3, ..., R54]
    FOR rule IN rules:
        compliance = check_rule(rule, plan_file, todos)
        IF compliance.status == "FAIL":
            RETURN {status: "FAIL", error: "Rule {rule.id} violated: {compliance.reason}"}
    
    # 4.1.3 Identify gaps
    gaps = []
    FOR todo IN todos:
        IF todo.metadata.evidence_location == NULL:
            APPEND(gaps, {todo_id: todo.id, gap: "No evidence location"})
        IF todo.metadata.success_criteria == NULL:
            APPEND(gaps, {todo_id: todo.id, gap: "No success criteria"})
    
    # 4.1.4 Write review
    review = {
        timestamp: TIMESTAMP(),
        todos_validated: TRUE,
        rules_checked: LENGTH(rules),
        violations: 0,
        gaps: gaps
    }
    
    WRITE "{base_path}docs/REVIEW/review.json" content=JSON(review)
    
    # OUTPUT (TEMPLATED)
    output = FORMAT_REVIEW_OUTPUT(
        stage: "REVIEW",
        model: model,
        agents: agents,
        input_files: [plan_file, todos_file],
        todos_validated: TRUE,
        rules_checked: LENGTH(rules),
        gaps: gaps,
        evidence_location: "{base_path}docs/REVIEW/review.json",
        next_stage: "DISRUPT"
    )
    
    PRINT(output)
    RETURN {status: "PASS", output: output}

################################################################################
# 4.2 DISRUPT STAGE
################################################################################

PROCEDURE execute_disrupt():
    
    # CONFIG
    model = "Opus 4.5"
    agents = ["Debate", "Third-party"]
    skills = ["/brainstorming", "/planning"]
    mcp = ["sequential-thinking", "openai-chat"]
    
    # INPUT
    plan = READ("{base_path}plans/plan.md")
    todos = PARSE_JSON(READ("{base_path}todo/todos.json"))
    
    # PROCESS
    # 4.2.1 Extract assumptions
    assumptions = CALL sequential-thinking/analyze input=plan prompt="List all assumptions"
    
    # 4.2.2 Challenge each assumption
    challenges = []
    FOR assumption IN assumptions:
        counter = CALL sequential-thinking/analyze {
            input: assumption,
            prompt: "Generate counter-argument"
        }
        APPEND(challenges, {assumption: assumption, counter: counter})
    
    # 4.2.3 Reality test each assumption
    FOR challenge IN challenges:
        # Define verification
        verification = {
            claim: challenge.assumption,
            test_command: GENERATE_TEST_COMMAND(challenge.assumption),
            expected_output: GENERATE_EXPECTED(challenge.assumption)
        }
        
        # Execute verification
        result = EXECUTE(verification.test_command)
        
        # Check result
        IF result.stdout CONTAINS verification.expected_output:
            challenge.reality_status = "VERIFIED"
        ELSE:
            challenge.reality_status = "REFUTED"
            challenge.actual_output = result.stdout
    
    # 4.2.4 Third-party validation
    third_party_prompt = FORMAT("""
        SCOPE: Validate assumptions for plan
        SUCCESS CRITERIA: All assumptions verified or acknowledged
        
        ASSUMPTIONS:
        {challenges}
        
        TASK: Return APPROVED if assumptions valid, REJECTED with specifics if not.
    """)
    
    third_party_response = CALL openai-chat/complete {
        model: "gpt-5.2",
        prompt: third_party_prompt
    }
    
    # 4.2.5 Write debate output
    debate = {
        timestamp: TIMESTAMP(),
        assumptions: assumptions,
        challenges: challenges,
        third_party: third_party_response
    }
    
    WRITE "{base_path}docs/DISRUPT/debate.json" content=JSON(debate)
    
    # OUTPUT (TEMPLATED)
    output = FORMAT_DISRUPT_OUTPUT(
        stage: "DISRUPT",
        model: model,
        agents: agents,
        assumptions_count: LENGTH(assumptions),
        verified_count: COUNT(challenges WHERE reality_status == "VERIFIED"),
        refuted_count: COUNT(challenges WHERE reality_status == "REFUTED"),
        third_party_status: EXTRACT_STATUS(third_party_response),
        evidence_location: "{base_path}docs/DISRUPT/debate.json",
        next_stage: "IMPLEMENT"
    )
    
    PRINT(output)
    RETURN {status: "PASS", output: output}

################################################################################
# 4.3 IMPLEMENT STAGE
################################################################################

PROCEDURE execute_implement():
    
    # CONFIG
    model = "Sonnet 4.5"
    agents = ["Executor", "Observer"]
    skills = ["/executing-plans", "/using-git-worktrees"]
    mcp = ["git", "github", "memory", "todo"]
    
    # INPUT
    todos = PARSE_JSON(READ("{base_path}todo/todos.json"))
    
    # PROCESS
    FOR todo IN todos WHERE todo.status == "pending":
        
        # 4.3.1 Update todo status
        CALL todo/update id=todo.id status="in_progress"
        
        # 4.3.2 Write code
        code = GENERATE_CODE(todo)
        
        # 4.3.3 Validate code (no placeholders)
        placeholder_check = EXECUTE("grep -rn 'TODO\\|FIXME\\|pass\\|\\.\\.\\.' {code.filepath}")
        IF placeholder_check.exit_code == 0:
            # Placeholders found
            RETURN {
                status: "FAIL",
                error: "Placeholders found in {code.filepath}",
                matches: placeholder_check.stdout
            }
        
        # 4.3.4 Validate types
        type_check = EXECUTE("grep -c 'def.*->' {code.filepath}")
        IF type_check.stdout == "0":
            RETURN {
                status: "FAIL",
                error: "No type hints in {code.filepath}"
            }
        
        # 4.3.5 Validate docstrings
        docstring_check = EXECUTE("grep -c '\"\"\"' {code.filepath}")
        IF docstring_check.stdout == "0":
            RETURN {
                status: "FAIL",
                error: "No docstrings in {code.filepath}"
            }
        
        # 4.3.6 Execute code
        exec_result = EXECUTE("python {code.filepath} > {todo.metadata.evidence_location} 2>&1")
        
        # 4.3.7 Check for errors
        error_check = EXECUTE("grep -i 'error\\|exception\\|traceback' {todo.metadata.evidence_location}")
        IF error_check.exit_code == 0:
            # Errors found
            RETURN {
                status: "FAIL",
                error: "Execution errors in {todo.id}",
                log: READ(todo.metadata.evidence_location)
            }
        
        # 4.3.8 Capture evidence
        evidence = {
            todo_id: todo.id,
            filepath: code.filepath,
            log_path: todo.metadata.evidence_location,
            log_tail: EXECUTE("tail -100 {todo.metadata.evidence_location}").stdout,
            timestamp: TIMESTAMP()
        }
        
        WRITE "{base_path}evidence/{todo.id}.json" content=JSON(evidence)
        
        # 4.3.9 Update todo
        CALL todo/update id=todo.id status="completed" evidence_delivered=TRUE
    
    # OUTPUT (TEMPLATED)
    output = FORMAT_IMPLEMENT_OUTPUT(
        stage: "IMPLEMENT",
        model: model,
        agents: agents,
        todos_completed: COUNT(todos WHERE status == "completed"),
        files_created: LIST_FILES("{base_path}evidence/"),
        evidence_location: "{base_path}evidence/",
        next_stage: "TEST"
    )
    
    PRINT(output)
    RETURN {status: "PASS", output: output}

################################################################################
# 4.4 TEST STAGE
################################################################################

PROCEDURE execute_test():
    
    # CONFIG
    model = "Sonnet 4.5"
    agents = ["Tester"]
    skills = ["/test-driven-development", "/systematic-debugging"]
    mcp = ["git", "memory", "todo"]
    
    # INPUT
    test_design = PARSE_JSON(READ("{base_path}test/design.json"))
    todos = PARSE_JSON(READ("{base_path}todo/todos.json"))
    
    # PROCESS
    test_results = []
    
    # 4.4.1 Unit tests
    unit_log = "{base_path}test/logs/unit.log"
    unit_result = EXECUTE("pytest tests/unit/ -v > {unit_log} 2>&1")
    unit_passed = EXECUTE("grep -c 'PASSED' {unit_log}").stdout
    unit_failed = EXECUTE("grep -c 'FAILED' {unit_log}").stdout
    
    IF INT(unit_failed) > 0:
        RETURN {
            status: "FAIL",
            stage: "TEST",
            substage: "unit",
            failures: unit_failed,
            log: READ(unit_log)
        }
    
    # 4.4.2 Integration tests
    integration_log = "{base_path}test/logs/integration.log"
    integration_result = EXECUTE("pytest tests/integration/ -v > {integration_log} 2>&1")
    integration_passed = EXECUTE("grep -c 'PASSED' {integration_log}").stdout
    integration_failed = EXECUTE("grep -c 'FAILED' {integration_log}").stdout
    
    IF INT(integration_failed) > 0:
        RETURN {
            status: "FAIL",
            stage: "TEST",
            substage: "integration",
            failures: integration_failed,
            log: READ(integration_log)
        }
    
    # 4.4.3 Full tests
    full_log = "{base_path}test/logs/full.log"
    full_result = EXECUTE("pytest tests/ -v > {full_log} 2>&1")
    full_passed = EXECUTE("grep -c 'PASSED' {full_log}").stdout
    full_failed = EXECUTE("grep -c 'FAILED' {full_log}").stdout
    
    IF INT(full_failed) > 0:
        RETURN {
            status: "FAIL",
            stage: "TEST",
            substage: "full",
            failures: full_failed,
            log: READ(full_log)
        }
    
    # 4.4.4 Verify each todo's success criteria
    FOR todo IN todos:
        verify_result = EXECUTE("""
            grep -q '{todo.metadata.success_criteria}' {todo.metadata.evidence_location}
        """)
        
        IF verify_result.exit_code != 0:
            RETURN {
                status: "FAIL",
                stage: "TEST",
                substage: "verification",
                todo_id: todo.id,
                error: "Success criteria not found in evidence"
            }
    
    # OUTPUT (TEMPLATED)
    output = FORMAT_TEST_OUTPUT(
        stage: "TEST",
        model: model,
        agents: agents,
        unit_passed: unit_passed,
        unit_failed: unit_failed,
        integration_passed: integration_passed,
        integration_failed: integration_failed,
        full_passed: full_passed,
        full_failed: full_failed,
        evidence_location: "{base_path}test/logs/",
        log_tails: {
            unit: EXECUTE("tail -50 {unit_log}").stdout,
            integration: EXECUTE("tail -50 {integration_log}").stdout,
            full: EXECUTE("tail -50 {full_log}").stdout
        },
        next_stage: "REVIEW_POST"
    )
    
    PRINT(output)
    RETURN {status: "PASS", output: output}

################################################################################
# 4.5 REVIEW POST-IMPLEMENTATION STAGE
################################################################################

PROCEDURE execute_review_post():
    
    # CONFIG
    model = "Opus 4.5"
    agents = ["Reviewer"]
    skills = ["/verification-before-completion", "/requesting-code-review"]
    mcp = ["github", "openai-chat", "memory"]
    
    # INPUT
    todos = PARSE_JSON(READ("{base_path}todo/todos.json"))
    evidence_files = LIST_FILES("{base_path}evidence/")
    test_logs = LIST_FILES("{base_path}test/logs/")
    
    # PROCESS
    verification_results = []
    
    FOR todo IN todos:
        # 4.5.1 Check evidence file exists
        IF NOT EXISTS(todo.metadata.evidence_location):
            RETURN {
                status: "FAIL",
                error: "Evidence file missing for {todo.id}",
                expected: todo.metadata.evidence_location
            }
        
        # 4.5.2 Check evidence proves claim
        evidence_content = READ(todo.metadata.evidence_location)
        
        proof_search = EXECUTE("""
            grep -n '{todo.metadata.success_criteria}' {todo.metadata.evidence_location}
        """)
        
        IF proof_search.exit_code != 0:
            RETURN {
                status: "FAIL",
                error: "Evidence does not prove success criteria for {todo.id}",
                evidence_path: todo.metadata.evidence_location,
                success_criteria: todo.metadata.success_criteria
            }
        
        verification_results.append({
            todo_id: todo.id,
            evidence_exists: TRUE,
            proof_found: TRUE,
            proof_lines: proof_search.stdout
        })
    
    # 4.5.3 Write review
    review = {
        timestamp: TIMESTAMP(),
        todos_verified: LENGTH(verification_results),
        all_evidence_exists: TRUE,
        all_proofs_found: TRUE,
        verifications: verification_results
    }
    
    WRITE "{base_path}docs/REVIEW_POST/review.json" content=JSON(review)
    
    # OUTPUT (TEMPLATED)
    output = FORMAT_REVIEW_POST_OUTPUT(
        stage: "REVIEW_POST",
        model: model,
        agents: agents,
        todos_verified: LENGTH(verification_results),
        evidence_files: evidence_files,
        test_logs: test_logs,
        evidence_location: "{base_path}docs/REVIEW_POST/review.json",
        next_stage: "VALIDATE"
    )
    
    PRINT(output)
    RETURN {status: "PASS", output: output}

################################################################################
# 4.6 VALIDATE STAGE
################################################################################

PROCEDURE execute_validate():
    
    # CONFIG
    model = "gpt-5.2"
    agents = ["Third-party", "Morality"]
    skills = ["/verification-before-completion"]
    mcp = ["openai-chat", "memory"]
    
    # INPUT
    plan = READ("{base_path}plans/plan.md")
    todos = PARSE_JSON(READ("{base_path}todo/todos.json"))
    evidence_files = LIST_FILES("{base_path}evidence/")
    test_logs = LIST_FILES("{base_path}test/logs/")
    reviews = [
        READ("{base_path}docs/REVIEW/review.json"),
        READ("{base_path}docs/DISRUPT/debate.json"),
        READ("{base_path}docs/REVIEW_POST/review.json")
    ]
    
    # PROCESS
    # 4.6.1 Compile evidence package
    evidence_package = {
        plan: plan,
        todos: todos,
        evidence_count: LENGTH(evidence_files),
        test_log_count: LENGTH(test_logs),
        reviews: reviews
    }
    
    # 4.6.2 Third-party validation
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
        
        TASK: Return APPROVED if all criteria met, REJECTED with specific gaps if not.
    """)
    
    third_party_response = CALL openai-chat/complete {
        model: "gpt-5.2",
        prompt: third_party_prompt
    }
    
    WRITE "{base_path}logs/gpt52_validate.json" content=JSON(third_party_response)
    
    IF "APPROVED" NOT IN third_party_response.response:
        RETURN {
            status: "FAIL",
            error: "Third-party validation rejected",
            feedback: third_party_response.response
        }
    
    # 4.6.3 Morality check
    morality_issues = CHECK_ETHICS(plan, todos)
    IF LENGTH(morality_issues) > 0:
        RETURN {
            status: "FAIL",
            error: "Morality check failed",
            issues: morality_issues
        }
    
    # OUTPUT (TEMPLATED)
    output = FORMAT_VALIDATE_OUTPUT(
        stage: "VALIDATE",
        model: model,
        agents: agents,
        third_party_status: "APPROVED",
        morality_status: "PASS",
        evidence_location: "{base_path}logs/gpt52_validate.json",
        next_stage: "LEARN"
    )
    
    PRINT(output)
    RETURN {status: "PASS", output: output}

################################################################################
# 4.7 LEARN STAGE
################################################################################

PROCEDURE execute_learn():
    
    # CONFIG
    model = "Haiku 4.5"
    agents = ["Learn"]
    skills = ["/writing-skills", "/memory-search"]
    mcp = ["memory", "claude-context"]
    
    # INPUT
    todos = PARSE_JSON(READ("{base_path}todo/todos.json"))
    reviews = [
        READ("{base_path}docs/REVIEW/review.json"),
        READ("{base_path}docs/DISRUPT/debate.json"),
        READ("{base_path}docs/REVIEW_POST/review.json")
    ]
    violations = READ("{base_path}logs/violations.json") OR []
    
    # PROCESS
    # 4.7.1 Extract learnings
    learnings = {
        successes: [],
        failures: [],
        assumptions_tested: [],
        improvements: []
    }
    
    FOR todo IN todos:
        IF todo.status == "completed":
            APPEND(learnings.successes, {
                todo_id: todo.id,
                what_worked: todo.content
            })
        ELSE:
            APPEND(learnings.failures, {
                todo_id: todo.id,
                what_failed: todo.content,
                reason: todo.blocked_by
            })
    
    FOR violation IN violations:
        APPEND(learnings.improvements, {
            stage: violation.stage,
            violation: violation.violation_type,
            prevention: GENERATE_PREVENTION(violation)
        })
    
    # 4.7.2 Store to memory
    CALL memory/write {
        key: "{workflow_id}_learnings",
        value: JSON(learnings)
    }
    
    # 4.7.3 Index learnings
    CALL claude-context/index {
        content: JSON(learnings),
        metadata: {workflow_id: workflow_id, type: "learnings"}
    }
    
    # 4.7.4 Write learnings file
    WRITE "{base_path}docs/LEARN/learnings.json" content=JSON(learnings)
    
    # OUTPUT (TEMPLATED)
    output = FORMAT_LEARN_OUTPUT(
        stage: "LEARN",
        model: model,
        agents: agents,
        successes: LENGTH(learnings.successes),
        failures: LENGTH(learnings.failures),
        improvements: LENGTH(learnings.improvements),
        memory_key: "{workflow_id}_learnings",
        evidence_location: "{base_path}docs/LEARN/learnings.json",
        next_stage: "COMPLETE"
    )
    
    PRINT(output)
    RETURN {status: "PASS", output: output}

################################################################################
# 5. OUTPUT TEMPLATES
################################################################################

TEMPLATE FORMAT_PLAN_OUTPUT:
    """
    ==============================================================================
    PLAN OUTPUT
    ==============================================================================
    
    ## 1. Startup Checklist
    | Item | Status |
    |------|--------|
    | MCP Servers (10) | {startup_status} |
    | Reprompt Timer | {startup_status} |
    | Memory | {startup_status} |
    | Workflow Directory | {startup_status} |
    
    ## 2. Objective
    **User Request:** {user_input}
    **Restated:** {objective}
    
    ## 3. Success Criteria
    | # | Criterion | Pass | Fail |
    |---|-----------|------|------|
    {FOR i, c IN success_criteria}
    | {i} | {c.description} | {c.pass} | {c.fail} |
    {ENDFOR}
    
    ## 4. Evidence Required
    | Criterion | Type | Verify Command |
    |-----------|------|----------------|
    {FOR c IN success_criteria}
    | {c.description} | {c.evidence_type} | {c.verify_command} |
    {ENDFOR}
    
    ## 5. Evidence Locations
    | Evidence | Path |
    |----------|------|
    {FOR e IN evidence_locations}
    | {e.name} | {e.path} |
    {ENDFOR}
    
    ## 6. Workflow Stages
    | Stage | Agents | Skills | MCP |
    |-------|--------|--------|-----|
    | PLAN | Planner, Research | /writing-plans, /research | memory, todo, claude-context |
    | REVIEW | Reviewer | /verification-before-completion | memory, openai-chat |
    | DISRUPT | Debate, Third-party | /brainstorming | sequential-thinking, openai-chat |
    | IMPLEMENT | Executor, Observer | /executing-plans | git, github, memory |
    | TEST | Tester | /test-driven-development | git, memory |
    | REVIEW | Reviewer | /verification-before-completion | github, openai-chat |
    | VALIDATE | Third-party, Morality | /verification-before-completion | openai-chat |
    | LEARN | Learn | /writing-skills | memory, claude-context |
    
    ## 7. Quality Gates
    | Gate | Condition | Fail Action |
    |------|-----------|-------------|
    | Template Gate | Output matches template | RESTART_AGENT |
    | Evidence Gate | Evidence file exists | RESTART_AGENT |
    | Proof Gate | Evidence proves claim | RESTART_AGENT |
    | Third-party Gate | gpt-5.2 APPROVED | RESTART_AGENT |
    | Test Gate | All tests pass | Return to IMPLEMENT |
    
    ## 8. Todos
    | id | content | status | priority | objective | success_criteria | evidence_location | agent | stage | time |
    |---|---|---|---|---|---|---|---|---|---|
    {FOR t IN todos}
    | {t.id} | {t.content} | {t.status} | {t.priority} | {t.metadata.objective} | {t.metadata.success_criteria} | {t.metadata.evidence_location} | {t.metadata.agent_model} | {t.metadata.workflow_stage} | {t.metadata.time_budget} |
    {ENDFOR}
    
    ## 9. Third-Party Review
    **Status:** {third_party_status}
    **Reviewer:** gpt-5.2
    
    ## 10. Changes & Justifications
    | Change | Justification |
    |--------|---------------|
    {FOR c IN changes}
    | {c.description} | {c.justification} |
    {ENDFOR}
    
    ==============================================================================
    AWAITING USER APPROVAL: Reply APPROVED or REJECTED with feedback
    ==============================================================================
    """

TEMPLATE FORMAT_STAGE_OUTPUT:
    """
    ==============================================================================
    {stage} COMPLETE
    ==============================================================================
    
    **Model:** {model}
    **Agents:** {agents}
    **Skills:** {skills}
    **MCP:** {mcp}
    
    **Input:**
    {FOR f IN input_files}
    - {f}
    {ENDFOR}
    
    **Process:**
    {process_summary}
    
    **Output:**
    - Evidence: {evidence_location}
    - Status: {status}
    
    **Evidence Tail (last 50 lines):**
    ```
    {evidence_tail}
    ```
    
    **Next Stage:** {next_stage}
    ==============================================================================
    """

################################################################################
# 6. RULES (R1-R54) - EVALUATED AT QUALITY GATES
################################################################################

RULES = {
    R1:  {check: "semantic_search_before_grep", fail: "RESTART"},
    R2:  {check: "logging_present", fail: "RESTART"},
    R3:  {check: "no_error_hiding", fail: "RESTART"},
    R4:  {check: "paths_tracked", fail: "RESTART"},
    R5:  {check: "skills_used", fail: "RESTART"},
    R6:  {check: "types_present", fail: "RESTART"},
    R7:  {check: "absolute_paths", fail: "RESTART"},
    R8:  {check: "cross_platform_paths", fail: "RESTART"},
    R9:  {check: "evidence_exists", fail: "RESTART"},
    R10: {check: "no_placeholders", fail: "RESTART"},
    R11: {check: "no_fabrication", fail: "TERMINATE"},
    R12: {check: "parallel_for_3plus", fail: "RESTART"},
    R13: {check: "memory_stored", fail: "RESTART"},
    R14: {check: "auto_transition", fail: "RESTART"},
    R15: {check: "observer_for_complex", fail: "RESTART"},
    R16: {check: "sequential_thinking_used", fail: "RESTART"},
    R17: {check: "complete_scope", fail: "RESTART"},
    R18: {check: "workflow_followed", fail: "RESTART"},
    # ... R19-R54 follow same pattern
    R51: {check: "checklist_complete", fail: "TERMINATE"},
    R52: {check: "reprompt_timer_active", fail: "TERMINATE"},
    R53: {check: "review_gate_passed", fail: "RESTART"},
    R54: {check: "quality_100_percent", fail: "TERMINATE"}
}

################################################################################
# END OF INSTRUCTIONS
################################################################################
```
