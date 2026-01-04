# HOOKS.md

```yaml
VERSION: 5.0
MODIFIED: 2026-01-04T07:00:00Z
LOCATION: ~/.claude/hooks/
PYTHON: 3.13+
```

---

## 0. HOOK OVERVIEW

```python
HOOKS = {
    "startup_validator":    {"file": "startup_validator.py",    "trigger": "session_start"},
    "reprompt_timer":       {"file": "reprompt_timer.py",       "trigger": "interval_5m"},
    "pre_compaction_hook":  {"file": "pre_compaction_hook.py",  "trigger": "pre_compact"},
    "skills_loader":        {"file": "skills_loader.py",        "trigger": "stage_enter"},
    "stage_gate_validator": {"file": "stage_gate_validator.py", "trigger": "stage_exit"},
    "evidence_validator":   {"file": "evidence_validator.py",   "trigger": "evidence_create"},
    "output_validator":     {"file": "output_validator.py",     "trigger": "output_create"}
}

def run_hook(hook_name: str, *args, **kwargs) -> HookResult:
    """Execute a hook."""
    hook = HOOKS[hook_name]
    path = f"~/.claude/hooks/{hook['file']}"
    
    result = EXECUTE f"python {path} {' '.join(args)}"
    
    RETURN HookResult(
        hook=hook_name,
        exit_code=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr
    )
```

---

## 1. STARTUP_VALIDATOR

```yaml
file: startup_validator.py
trigger: session_start
purpose: Validate all startup requirements before workflow begins
exit_codes:
  0: All checks pass
  1: Critical failure (abort)
  2: Non-critical warnings (continue)
```

### Checks

| # | Check | Type | Fail Action |
|---|-------|------|-------------|
| S01 | MCP memory | ping | ABORT |
| S02 | MCP todo | ping | ABORT |
| S03 | MCP sequential-thinking | ping | ABORT |
| S04 | MCP git | ping | WARN |
| S05 | MCP github | ping | WARN |
| S06 | MCP scheduler | ping | ABORT |
| S07 | MCP openai-chat | ping | WARN |
| S08 | MCP credentials | ping | WARN |
| S09 | MCP mcp-gateway | ping | WARN |
| S10 | Reprompt timer | create | ABORT |
| S11 | Compaction hook | create | WARN |
| S12 | Memory read/write | test | ABORT |
| S13 | Workflow directory | mkdir | ABORT |
| S14 | Skills available | check | WARN |
| S15 | Credentials | exists | WARN |

### Usage

```bash
# Run all checks
python startup_validator.py --check

# Create workflow directory only
python startup_validator.py --create-workflow

# Output to file
python startup_validator.py --check --output startup_result.json
```

### Output Schema

```json
{
  "startup": {
    "mcp_verified": true,
    "scheduler_active": true,
    "memory_ok": true,
    "env_ready": true,
    "workflow_dir": ".workflow/20260104_070000_abc12345/",
    "timestamp": "2026-01-04T07:00:00Z",
    "status": "PASS",
    "errors": [],
    "warnings": []
  }
}
```

---

## 2. REPROMPT_TIMER

```yaml
file: reprompt_timer.py
trigger: interval_5m
purpose: Periodic quality gate checks
exit_codes:
  0: Gate passed (PROCEED)
  1: Gate failed (REVISE/STOP)
  2: Escalation required (ESCALATE)
```

### Features

- 5-minute default interval (configurable)
- Triggers on compaction events
- Generates reprompt on failure
- Logs all gate results to `.workflow/logs/`

### Usage

```bash
# Start background timer
python reprompt_timer.py --start --interval 5

# Run single check
python reprompt_timer.py --check

# Check specific stage
python reprompt_timer.py --stage IMPLEMENT --outputs outputs.json

# Show status
python reprompt_timer.py --status
```

### Reprompt Output

```
================================================================================
⛔ QUALITY GATE FAILED
================================================================================

STAGE:        IMPLEMENT
ATTEMPT:      2/3
TIMESTAMP:    2026-01-04T07:30:00Z
ACTION:       REVISE

--------------------------------------------------------------------------------
ERRORS (3):
--------------------------------------------------------------------------------
  ❌ [todo] Missing: metadata.evidence_location
  ❌ [evidence] Evidence file missing: /path/to/evidence.log
  ❌ Missing required schema: evidence

--------------------------------------------------------------------------------
REQUIRED SCHEMAS: ['todo', 'evidence']
SCHEMAS CHECKED:  ['todo']
--------------------------------------------------------------------------------

================================================================================
CORRECTIVE ACTION REQUIRED
================================================================================

INSTRUCTION: Fix errors and resubmit stage output.

CHECKLIST:
  [ ] All required fields present
  [ ] Enum values valid
  [ ] Paths absolute
  [ ] Evidence file exists at location
  [ ] Timestamps ISO8601

RESUBMIT COMMAND:
  python reprompt_timer.py --check

================================================================================
```

---

## 3. PRE_COMPACTION_HOOK

```yaml
file: pre_compaction_hook.py
trigger: pre_compact
purpose: Export state before context compaction
exit_codes:
  0: Export successful
  1: Export failed
```

### Exports

| Export | Format | Description |
|--------|--------|-------------|
| Chat history | CSV (36 columns) | All messages with metadata |
| Workflow archive | ZIP | Complete .workflow/ directory |
| Handoff context | JSON | State for continuation |
| Memory update | JSON | Session summary for memory |
| Manifest | JSON | Export inventory with checksums |

### CSV Columns (36)

```
timestamp, duration_seconds, response_time_ms, session_start, elapsed_from_start,
role, agent_model, agent_persona, user_id, session_id, chat_id, message,
message_type, word_count, token_count, language, tools_invoked, tool_count,
mcp_servers_used, files_created, files_modified, workflow_stage, todo_ids,
parent_message_id, thread_depth, contains_code, contains_evidence, violations,
u1_u8_compliance, compaction_occurred, context_tokens_used, attachments,
references, action_taken, user_approved, requires_followup, blockers
```

### Usage

```bash
# Auto-trigger based on threshold
python pre_compaction_hook.py --auto

# Manual export
python pre_compaction_hook.py --export --output ./exports/

# Force export regardless of threshold
python pre_compaction_hook.py --force --tokens 180000

# Custom threshold
python pre_compaction_hook.py --auto --threshold 0.7
```

### Output Directory

```
~/.claude/exports/{timestamp}/
├── combined_messages.csv
├── user_messages.csv
├── agent_messages.csv
├── workflow_archive.zip
├── handoff.json
├── memory_update.json
└── manifest.json
```

---

## 4. SKILLS_LOADER

```yaml
file: skills_loader.py
trigger: stage_enter
purpose: Load superpowers skills per stage
exit_codes:
  0: Skills loaded
  1: Skill not found
```

### Stage-to-Skills Mapping

| Stage | Skills |
|-------|--------|
| PLAN | brainstorming, writing-plans |
| REVIEW | verification-before-completion |
| DISRUPT | brainstorming |
| IMPLEMENT | executing-plans, test-driven-development |
| TEST | test-driven-development, systematic-debugging |
| REVIEW_POST | verification-before-completion, requesting-code-review |
| VALIDATE | verification-before-completion |
| LEARN | writing-skills |

### Usage

```bash
# Load all skills
python skills_loader.py --load-all

# Load skills for stage
python skills_loader.py --stage IMPLEMENT

# Check skill availability
python skills_loader.py --check

# Get skill prompt
python skills_loader.py --prompt verification-before-completion

# Save loaded skills to file
python skills_loader.py --load-all --output skills.json
```

### Output

```
=== Skills for IMPLEMENT Stage ===

## Using Skill: executing-plans

**Description:** Execute plans in batches with verification at each step.

**Triggers:** execute plan, implement, follow plan

**Workflow:**
  1. Announce: Using executing-plans skill
  2. Read plan file
  3. Review critically - identify concerns
  ...

---

## Using Skill: test-driven-development

**Description:** RED-GREEN-REFACTOR: Write failing test, make it pass, refactor.

**Core Principle:** Write failing test FIRST, watch it fail, then write minimal code to pass.

**Phases:**
  - RED: Write failing test
  - GREEN: Write minimal code to pass
  - REFACTOR: Clean up
```

---

## 5. STAGE_GATE_VALIDATOR

```yaml
file: stage_gate_validator.py
trigger: stage_exit
purpose: Validate stage outputs against required schemas
exit_codes:
  0: PROCEED (gate passed)
  1: REVISE/STOP (gate failed)
  2: ESCALATE (max retries exceeded)
```

### Validation Steps

1. Load required schemas for stage (from QUALITY_GATES)
2. Detect schema type for each output
3. Validate each output against its schema
4. Check all required schemas are present
5. Check evidence files exist
6. Determine action (PROCEED/REVISE/ESCALATE/STOP)

### Usage

```bash
# Validate stage
python stage_gate_validator.py --stage IMPLEMENT --output outputs.json

# Validate from file
python stage_gate_validator.py --stage PLAN --file plan_output.json

# With retry count
python stage_gate_validator.py --stage TEST --output test.json --retry 2
```

### Output

```json
{
  "stage": "IMPLEMENT",
  "valid": false,
  "checked": ["todo", "evidence"],
  "errors": [
    "[todo] Missing: metadata.reviewer",
    "Evidence file missing: /path/to/evidence.log"
  ],
  "retry": 1,
  "action": "REVISE",
  "exit_code": 1
}
```

---

## 6. EVIDENCE_VALIDATOR

```yaml
file: evidence_validator.py
trigger: evidence_create
purpose: Validate evidence records
exit_codes:
  0: Valid
  1: Invalid
```

### Validations

- ID matches pattern: `E-{STAGE}-{SESSION}-{SEQ:03d}`
- Type is valid enum
- Location is absolute path
- File exists at location
- Timestamp is ISO8601
- verified is boolean
- verified_by is valid enum

### Usage

```bash
# Validate evidence
python evidence_validator.py --evidence evidence.json

# Validate and create file
python evidence_validator.py --claim "Test passed" --location /path/to/log --create
```

---

## 7. OUTPUT_VALIDATOR

```yaml
file: output_validator.py
trigger: output_create
purpose: Validate any output against detected schema
exit_codes:
  0: Valid
  1: Invalid
  2: Unknown schema
```

### Usage

```bash
# Validate output (auto-detect schema)
python output_validator.py --output output.json

# Validate with specific schema
python output_validator.py --output output.json --schema todo

# Validate multiple outputs
python output_validator.py --outputs outputs.json --stage IMPLEMENT
```

---

## 8. HOOK INTEGRATION

```python
def on_session_start():
    """Run startup hooks."""
    run_hook("startup_validator", "--check")

def on_stage_enter(stage: str):
    """Run stage entry hooks."""
    run_hook("skills_loader", f"--stage {stage}")

def on_stage_exit(stage: str, outputs: list):
    """Run stage exit hooks."""
    run_hook("stage_gate_validator", f"--stage {stage}", f"--output {json.dumps(outputs)}")

def on_evidence_create(evidence: dict):
    """Run evidence hooks."""
    run_hook("evidence_validator", f"--evidence {json.dumps(evidence)}")

def on_pre_compaction():
    """Run compaction hooks."""
    run_hook("pre_compaction_hook", "--export", "--force")

def on_timer_tick():
    """Run timer hooks (every 5 minutes)."""
    run_hook("reprompt_timer", "--check")
```
