# SKILLS.md

```yaml
VERSION: 5.0
MODIFIED: 2026-01-04T07:00:00Z
SOURCE: obra/superpowers
LOADER: hooks/skills_loader.py
```

---

## 0. SKILL USAGE

```python
def use_skill(skill_name: str):
    """Load and apply a skill."""
    
    # 1. Announce
    PRINT f"Using skill: {skill_name}"
    
    # 2. Load skill content
    skill = CALL skills_loader/load {name: skill_name}
    
    # 3. Create todos from checklist (if present)
    IF skill.checklist:
        FOR item IN skill.checklist:
            CALL todo/create {content: item, priority: "high"}
    
    # 4. Follow skill exactly
    EXECUTE skill.workflow
```

### Skill Selection by Stage

| Stage | Skills |
|-------|--------|
| PLAN | brainstorming, writing-plans |
| REVIEW | verification-before-completion |
| DISRUPT | brainstorming |
| IMPLEMENT | executing-plans, test-driven-development |
| TEST | test-driven-development, systematic-debugging |
| REVIEW | verification-before-completion, requesting-code-review |
| VALIDATE | verification-before-completion |
| LEARN | writing-skills |

---

## 1. VERIFICATION-BEFORE-COMPLETION

```yaml
name: verification-before-completion
description: Evidence before claims, always. Run verification before claiming work is complete.
triggers:
  - before claim
  - before commit
  - before PR
  - work complete
  - task done

core_principle: |
  If you haven't run the verification command in this message, 
  you cannot claim it passes. NO COMPLETION CLAIMS WITHOUT FRESH 
  VERIFICATION EVIDENCE.

checklist:
  - "IDENTIFY: What command proves this claim?"
  - "RUN: Execute the FULL command (fresh, complete)"
  - "READ: Full output, check exit code, count failures"
  - "VERIFY: Does output confirm the claim?"
  - "STATE: Actual status WITH evidence"

workflow:
  1. Before claiming ANY status:
     - Identify verification command
     - Run command fresh (not cached)
     - Read complete output
     - Check exit code
     - Count failures
  
  2. If verification fails:
     - State actual status
     - Include evidence
     - Do NOT claim success
  
  3. If verification passes:
     - State claim WITH evidence
     - Include command output

anti_patterns:
  - Claiming success without running command
  - Using cached results
  - Partial output review
  - Ignoring exit codes
```

---

## 2. EXECUTING-PLANS

```yaml
name: executing-plans
description: Execute plans in batches with verification at each step.
triggers:
  - execute plan
  - implement
  - follow plan
  - start implementation

workflow:
  1. Announce: "Using executing-plans skill"
  2. Read plan file
  3. Review critically - identify concerns
  4. If concerns: Raise with human before starting
  5. If no concerns: Create todos (default: first 3 tasks)
  
  6. For each task:
     - Mark as in_progress
     - Follow each step exactly
     - Run verifications as specified
     - Mark as completed
  
  7. When batch complete:
     - Show what was implemented
     - Show verification output
     - Say: "Ready for feedback."
  
  8. Based on feedback:
     - Apply changes if needed
     - Execute next batch
     - Repeat until complete
  
  9. After all tasks complete:
     - Use finishing-a-development-branch skill

rules:
  - Follow plan exactly (it has bite-sized steps)
  - Ask for clarification rather than guessing
  - Verify after each task
  - Get feedback after each batch
```

---

## 3. TEST-DRIVEN-DEVELOPMENT

```yaml
name: test-driven-development
description: "RED-GREEN-REFACTOR: Write failing test, make it pass, refactor."
triggers:
  - write test
  - TDD
  - test first
  - red-green

core_principle: |
  Write failing test FIRST, watch it fail, then write minimal code to pass.

phases:
  RED:
    - Write test for desired behavior
    - Run test
    - Watch it FAIL (this proves test works)
    - If test passes: test is wrong
  
  GREEN:
    - Write MINIMAL code to pass
    - No extra features
    - No premature optimization
    - Just make the test pass
  
  REFACTOR:
    - Clean up code
    - Run tests (must still pass)
    - No behavior changes
    - Improve structure only

rules:
  - Never write code without failing test first
  - Minimal code to pass (YAGNI)
  - Refactor only when tests pass
  - Commit after each green
```

---

## 4. SYSTEMATIC-DEBUGGING

```yaml
name: systematic-debugging
description: 4-phase root cause process for debugging.
triggers:
  - debug
  - fix bug
  - error
  - not working
  - broken
  - investigate

phases:
  ISOLATE:
    - Reproduce the issue consistently
    - Find minimal reproduction case
    - Document exact steps
    - Identify what changed
  
  ANALYZE:
    - Find ROOT CAUSE (not symptoms)
    - Trace execution path
    - Check assumptions
    - Use bisection if needed
  
  FIX:
    - Minimal targeted change
    - Fix root cause (not symptoms)
    - Don't fix unrelated issues
    - Add test for the bug
  
  VERIFY:
    - Confirm fix works
    - Check no regressions
    - Run full test suite
    - Document the fix

anti_patterns:
  - Fixing symptoms instead of root cause
  - Multiple changes at once
  - Not verifying fix
  - Skipping test for bug
```

---

## 5. BRAINSTORMING

```yaml
name: brainstorming
description: Refine rough ideas through questions, explore alternatives.
triggers:
  - brainstorm
  - design
  - plan
  - what should
  - how should
  - idea

workflow:
  1. Ask clarifying questions
     - What problem are we solving?
     - Who is the user?
     - What are constraints?
     - What's the success criteria?
  
  2. Explore alternatives
     - List 3+ approaches
     - Pros/cons of each
     - Identify risks
  
  3. Present design in sections
     - Break into digestible chunks
     - Get validation on each
     - Don't overload with details
  
  4. Document decisions
     - What was chosen
     - Why it was chosen
     - What was rejected
  
  5. Save design document
     - .workflow/designs/design.md

rules:
  - Don't jump to code
  - Explore alternatives
  - Get buy-in before implementing
  - Document decisions
```

---

## 6. REQUESTING-CODE-REVIEW

```yaml
name: requesting-code-review
description: Request code review with proper context.
triggers:
  - request review
  - PR ready
  - need review
  - ready for review

checklist:
  - "Summarize what changed and why"
  - "List areas needing attention"
  - "Provide testing evidence"
  - "Note any concerns or tradeoffs"
  - "Link to relevant docs/issues"

template: |
  ## Summary
  [What changed and why]
  
  ## Changes
  - [File 1]: [Description]
  - [File 2]: [Description]
  
  ## Testing
  - [Tests added/modified]
  - [Manual testing done]
  - [Evidence: command output]
  
  ## Areas of concern
  - [Any tricky parts]
  - [Tradeoffs made]
  
  ## Checklist
  - [ ] Tests pass
  - [ ] No placeholders
  - [ ] Documentation updated
  - [ ] No breaking changes
```

---

## 7. RECEIVING-CODE-REVIEW

```yaml
name: receiving-code-review
description: Handle code review feedback with technical rigor.
triggers:
  - review feedback
  - reviewer said
  - code review
  - feedback received

core_principle: |
  Verify before implementing. Ask before assuming. 
  Technical correctness over social comfort.

workflow:
  1. READ: Complete feedback without reacting
  
  2. UNDERSTAND: Restate requirement in own words
     - "You're asking me to..."
     - Ask if unclear
  
  3. VERIFY: Test claims independently
     - Don't blindly trust
     - Check for yourself
     - "Checking... [result]"
  
  4. IMPLEMENT: Only after understanding
     - Fix what's actually wrong
     - Don't over-fix
  
  5. CONFIRM: Run verification
     - "Fixed [X]. Verified with [command]"

responses:
  correct_feedback: |
    ✅ "You were right - I checked [X] and it does [Y]. Implementing now."
    ✅ "Verified and you're correct. Fixing."
  
  incorrect_feedback: |
    ✅ "I checked [X] and found [Y]. Here's the evidence: [output]. 
        Does this change your recommendation?"
  
  avoid:
    - Long apologies
    - Defending why you pushed back
    - Over-explaining
```

---

## 8. SUBAGENT-DRIVEN-DEVELOPMENT

```yaml
name: subagent-driven-development
description: Dispatch fresh subagents per task with two-stage review.
triggers:
  - dispatch agent
  - subagent
  - parallel tasks
  - delegate

workflow:
  1. Create task specification
     - Clear objective
     - Success criteria
     - Required context
     - Expected output
  
  2. Dispatch fresh subagent
     - New context (no history)
     - Task spec only
     - Time limit
  
  3. Two-stage review
     Stage 1: Spec compliance
       - Did it follow the spec?
       - Is output complete?
     
     Stage 2: Code quality
       - No placeholders?
       - Types present?
       - Tests pass?
  
  4. Aggregate results
     - Collect all outputs
     - Merge if needed
     - Verify integration

rules:
  - Fresh agent per task (no context bleed)
  - Clear specs (no assumptions)
  - Two-stage review required
  - Reject incomplete work
```

---

## 9. DISPATCHING-PARALLEL-AGENTS

```yaml
name: dispatching-parallel-agents
description: Coordinate multiple agents working in parallel.
triggers:
  - parallel
  - multiple agents
  - concurrent
  - parallelize

requirements:
  - Tasks must be independent (no dependencies)
  - Clear boundaries between tasks
  - Aggregation strategy defined
  - Observer agent monitors progress

workflow:
  1. Identify parallel tasks
     - No shared state
     - No dependencies
     - Clear boundaries
  
  2. Create task specs (one per agent)
     - Independent context
     - Clear deliverables
     - Time budget
  
  3. Dispatch agents
     - All start simultaneously
     - Observer tracks progress
     - Timeout handling
  
  4. Collect results
     - Wait for all or timeout
     - Handle failures
     - Aggregate outputs
  
  5. Merge and verify
     - Integration testing
     - Conflict resolution
     - Final validation

rules:
  - 3+ independent tasks → parallel
  - Observer required
  - Timeout mandatory
  - Merge strategy defined upfront
```

---

## 10. WRITING-SKILLS

```yaml
name: writing-skills
description: Create reusable skills for future Claude instances.
triggers:
  - create skill
  - write skill
  - document pattern
  - capture learning

structure:
  name: "Skill-Name-With-Hyphens"
  description: "Use when [triggers]"
  
  sections:
    - Overview (what is this, 1-2 sentences)
    - When to Use (triggers, symptoms)
    - Core Pattern (before/after comparison)
    - Quick Reference (table/bullets)
    - Implementation (code examples)
    - Common Mistakes (what goes wrong)

testing:
  - Watch agent fail without skill
  - Add skill
  - Watch agent succeed
  - Iterate until bulletproof

deployment:
  - Create SKILL.md
  - Test with subagent
  - Verify discovery works
  - Add to skills loader
```

---

## 11. SKILL LOADER

```python
def load_skills_for_stage(stage: str) -> list[Skill]:
    """Load all skills required for a stage."""
    
    STAGE_SKILLS = {
        "PLAN": ["brainstorming", "writing-plans"],
        "REVIEW": ["verification-before-completion"],
        "DISRUPT": ["brainstorming"],
        "IMPLEMENT": ["executing-plans", "test-driven-development"],
        "TEST": ["test-driven-development", "systematic-debugging"],
        "REVIEW_POST": ["verification-before-completion", "requesting-code-review"],
        "VALIDATE": ["verification-before-completion"],
        "LEARN": ["writing-skills"]
    }
    
    skill_names = STAGE_SKILLS.get(stage.upper(), [])
    skills = []
    
    FOR name IN skill_names:
        skill = load_skill(name)
        IF skill:
            skills.append(skill)
    
    RETURN skills
```
