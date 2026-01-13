# External Review Templates

Prompts for external validation via GPT-5.2 or other LLMs. **NO ANCHORING** - present facts only, no conclusions.

## Template 1: Reasoning Validation

```markdown
## Independent Review Request

### Problem
{PROBLEM_STATEMENT}

### Positions Under Consideration
| Position | Supporting Arguments |
|----------|---------------------|
| A        | {ARGS_A}            |
| B        | {ARGS_B}            |

### Evidence Presented
{EVIDENCE_WITHOUT_CONCLUSIONS}

### Questions
1. What flaws exist in each position?
2. What evidence is missing?
3. Which position is stronger and why?
4. What alternative approaches weren't considered?

Provide independent assessment. Do not assume any position is correct.
```

## Template 2: Technical Decision Review

```markdown
## Technical Review Request

### Context
{TECHNICAL_CONTEXT}

### Options Being Evaluated
```yaml
option_a:
  description: {DESC}
  pros: {PROS}
  cons: {CONS}
  
option_b:
  description: {DESC}
  pros: {PROS}
  cons: {CONS}
```

### Constraints
{CONSTRAINTS_LIST}

### Questions
1. Are the pros/cons accurately stated?
2. What trade-offs are understated?
3. What failure modes are missed?
4. What would you recommend and why?

Provide independent technical assessment.
```

## Template 3: Assumption Stress Test

```markdown
## Assumption Review Request

### Decision Being Made
{DECISION_SUMMARY}

### Assumptions Underlying This Decision
1. {ASSUMPTION_1}
2. {ASSUMPTION_2}
3. {ASSUMPTION_3}

### Questions
1. Which assumptions are weakest?
2. What happens if each assumption is wrong?
3. How would you test each assumption?
4. What assumptions are missing from this list?

Challenge these assumptions rigorously.
```

## Template 4: Consensus Deadlock Resolution

```markdown
## Deadlock Resolution Request

### Question
{SPECIFIC_QUESTION}

### Position A
Held by: {PERSONAS}
Argument: {ARGUMENT}
Evidence: {EVIDENCE}

### Position B
Held by: {PERSONAS}
Argument: {ARGUMENT}
Evidence: {EVIDENCE}

### Why Deadlocked
{REASON_NO_CONSENSUS}

### Questions
1. Which position has stronger evidence?
2. Is there a synthesis that satisfies both?
3. What test would resolve this empirically?
4. What's your independent recommendation?

Break this deadlock with fresh perspective.
```

## Usage Notes

- Never include your conclusions in the prompt (anchoring bias)
- Present all positions neutrally
- Ask open-ended questions
- Request specific actionable feedback
- Include "Do not assume correctness" instruction
