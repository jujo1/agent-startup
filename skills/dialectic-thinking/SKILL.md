---
name: dialectic-thinking
version: 1.1.0
description: Multi-agent deliberation protocol with persona-based debate, evidence-weighted consensus, and adaptive stopping. Use for complex reasoning requiring diverse perspectives, stress-testing decisions, or when single-viewpoint analysis is insufficient. NOT for simple lookups, routine tasks, or time-critical responses.
---

# Dialectic Thinking Protocol

Multi-agent deliberation through structured debate with grounded creativity.

## When to Use

| Use For | Avoid For |
|---------|-----------|
| Complex decisions with trade-offs | Single-fact lookups |
| Design choices needing stress-test | Routine code fixes |
| Problems where diverse views help | Time-critical responses |
| Uncertainty about best approach | Clear-path execution |

**Complex decision**: Multiple valid approaches exist, trade-offs are non-obvious, or stakeholders might disagree.

## Grounding Rules (ALL Agents)

Every agent, including creative ones, follows these rules:

| Rule | Description | Application |
|------|-------------|-------------|
| Search First | Check web/github/skills before building | Claim → search → cite |
| Cite or Caveat | Sources required, else mark hypothesis | `[cited]` or `[hypothesis]` |
| Test Path | Conclusions include verification method | "Verify by: {method}" |
| Creativity Valued | Intuition welcomed if labeled + testable | `[intuition]` + test |

## Personas

### Tiered Activation (Max 5 Simultaneous)

| Tier | Personas | When Active |
|------|----------|-------------|
| Always-On | skeptic, workflow_enforcer | Every deliberation |
| Phase 1: Problem Definition | questions, big_picture | First 3 thoughts |
| Phase 2: Solution Generation | minimalist, visionary, expert | Thoughts 4-9 |
| Phase 3: Resolution | mediator | Deadlock or final 3 thoughts |

### Core Personas

```yaml
skeptic:
  trigger: "Claims without evidence"
  stance: "Show me the data"
  weight: 2.0 (demands verification)
  tier: always-on

workflow_enforcer:
  trigger: "Every thought (always active)"
  stance: "Does this comply with user instructions?"
  behavior: |
    - Monitors against AGENT-INSTRUCTIONS.md rules
    - Flags fabrications, placeholders, missing evidence
    - Enforces WFD logging requirement
    - VETO power: blocks conclusions lacking evidence
  weight: 2.0 (hard constraint, non-negotiable)
  tier: always-on
  tools: rule checking, file verification, grep

questions:
  trigger: "Problem statement accepted without interrogation"
  stance: "What are we NOT asking?"
  behavior: |
    - Generates probing questions to expose blind spots
    - Identifies unstated assumptions
    - Forces clarity before solution-seeking
    - Uses brainstorming patterns
  weight: 1.5 (elevates early)
  tier: phase-1
  tools: brainstorming, user clarification

big_picture:
  trigger: "Discussion narrowing to local optimum"
  stance: "Zoom out - what actually matters here?"
  behavior: |
    - Top-down strategic lens
    - Compares to industry/world patterns
    - Prevents premature convergence
    - Forces lateral thinking: "How did X solve this?"
  weight: 1.5 (elevates during convergence)
  tier: phase-1
  tools: web_search (comparative), analogy generation

minimalist:
  trigger: "Complex proposals"
  stance: "Does this already exist?"
  weight: 1.5 (prefers proven solutions)
  tier: phase-2

visionary:
  trigger: "Risk-heavy or stuck analysis"
  stance: "What if we tried...?"
  weight: 1.0 (creative but must be testable)
  tier: phase-2

expert:
  trigger: "Technical or domain decisions"
  stance: "Domain authority"
  weight: 1.5 (higher on specialty topics)
  tier: phase-2

mediator:
  trigger: "Disagreement or deadlock"
  stance: "What does evidence balance show?"
  weight: 1.5 (synthesizes positions)
  tier: phase-3
```

### Domain Override

When problem domain is clear, add domain-specific persona:

```
[Domain: {DOMAIN}]
Override: Replace {PERSONA} with {DOMAIN_EXPERT}
Rationale: {WHY_THIS_EXPERTISE_MATTERS}
```

### Missing Perspective Check

If debate stalls, ask: "What perspective is missing from this analysis?"

## Protocol Structure

### Start

```
═══════════════════════════════════════════════════════
DELIBERATION: {problem}
Mode: multi-agent | Personas: {list} | Max: 12 thoughts
═══════════════════════════════════════════════════════

Grounding check:
├── Searched existing solutions? {yes|no|pending}
├── Domain expertise needed? {yes → which|no}
└── Success criteria defined? {yes|need to define}
```

### Thought Format

```
Thought {N}/{max} [{persona}]
────────────────────────────
{content}

Evidence: {[cited: source] | [hypothesis] | [intuition]}
Test path: {how to verify}

[Next: continue|challenge|vote|conclude|abort]
```

### Challenge (Persona vs Persona)

```
Thought {N}/{max} [{challenger}] ⚔️ challenges [{target}]
───────────────────────────────────────────────────────
Target claim: {what's being challenged}
Challenge: {the objection}
Evidence: {[cited] | [hypothesis]}

Response from [{target}]:
{address or acknowledge}

Resolution: {maintain|revise|defer to vote}
```

### Deliberation Round

When multiple perspectives needed on same question:

```
═══ DELIBERATION ROUND {R} ═══
Question: {specific question to resolve}

┌─────────────────────────────────────────────────────┐
│ SKEPTIC                                             │
│ Position: {position}                                │
│ Evidence: {[cited|hypothesis|intuition]}            │
│ Weight: {2|1|0.5}                                   │
├─────────────────────────────────────────────────────┤
│ MINIMALIST                                          │
│ Position: {position}                                │
│ Evidence: {[cited|hypothesis|intuition]}            │
│ Weight: {2|1|0.5}                                   │
├─────────────────────────────────────────────────────┤
│ VISIONARY                                           │
│ Position: {position}                                │
│ Evidence: {[cited|hypothesis|intuition]}            │
│ Weight: {2|1|0.5}                                   │
│ Test: {how to verify if correct}                    │
└─────────────────────────────────────────────────────┘

Rebuttals (1 each, evidence-required):
- {persona}: {rebuttal to another}
- {persona}: {rebuttal to another}

Synthesis: {evidence-weighted resolution}
```

### Consensus Protocol

```
═══ CONSENSUS CHECK ═══

Position Summary:
| Persona | Position | Evidence Type | Weight |
|---------|----------|---------------|--------|
| {p1}    | {pos}    | cited         | 2      |
| {p2}    | {pos}    | hypothesis    | 1      |
| {p3}    | {pos}    | intuition     | 0.5    |

Evidence Weights:
- Cited (verified source): 2
- Testable hypothesis: 1  
- Untestable intuition: 0.5

Weighted Result: {calculated}
Consensus: {reached|not reached}

IF not reached:
├── Deadlock resolution: {external review|user input|test it}
└── Escalate to: {GPT-5.2|human|empirical test}
```

### External Review

When internal deliberation insufficient:

```
Thought {N}/{max} ⚔️ External Review
────────────────────────────────────
Sent to: {GPT-5.2|domain expert}
Question: {specific question, no anchoring}
Context: {facts only, no conclusions}

Response: {external assessment}
Integration: {how incorporating}

[Next: continue]
```

See `references/external-review-templates.md` for prompt templates.

### Stopping Criteria

Deliberation stops when ANY condition met:

```
STOP CONDITIONS (first match wins):
├── ✓ Convergence: 2 consecutive matching conclusions
├── ✓ Iteration cap: thoughts >= 12
├── ✓ Confidence: HIGH + no active challenges
├── ✓ Diminishing: 3 thoughts with no new insight
├── ✓ Action-ready: decision executable + testable
└── ✓ Forced consensus: 6 thoughts without progress → vote

Current: {which condition applies}
```

### Convergence Forcing (Anti-Dilution)

When too many views risk non-convergence:

```yaml
convergence_rules:
  max_thoughts_without_progress: 6
  weight_threshold_for_decision: 6.0
  deadlock_escalation: 2 rounds → user clarification
  
  evidence_tiebreaker:
    - cited: 2.0
    - hypothesis: 1.0
    - intuition: 0.5
  
  forced_vote_format: |
    ═══ FORCED CONSENSUS (progress stalled) ═══
    | Position | Supporters | Total Weight |
    |----------|------------|--------------|
    | {pos_a}  | skeptic, minimalist | 3.5 |
    | {pos_b}  | visionary | 1.0 |
    
    Winner: {highest weight} (threshold 6.0)
    IF no winner → escalate to user
```

### User Clarification Protocol

```yaml
user_clarification:
  triggers:
    - Assumption cannot be reality-tested
    - Consensus not reached after 2 rounds
    - Ambiguity in user request detected
    - big_picture identifies missing context
  
  format: |
    ═══ USER CLARIFICATION NEEDED ═══
    Blocker: {what cannot be resolved internally}
    Questions:
    1. {specific question - binary or bounded}
    2. {specific question - binary or bounded}
    Impact: {what changes based on answer}
    ═══════════════════════════════════════════
  
  rules:
    - Max 3 questions per clarification
    - Must be binary or bounded choice
    - Cannot proceed on assumption if testable by asking
    - workflow_enforcer can force clarification
```

### Workflow Enforcer VETO

```yaml
veto_conditions:
  - Conclusion contains unverified claims
  - Evidence type "intuition" dominates decision
  - No test_path provided
  - Fabrication detected (claim without source)
  - Violates AGENT-INSTRUCTIONS.md rules

veto_format: |
  🛑 WORKFLOW_ENFORCER VETO
  ─────────────────────────
  Blocked: {what was blocked}
  Reason: {rule violated}
  Required: {what must change}
  
  Deliberation cannot conclude until resolved.
```

### Conclude

```
Thought {N}/{N} ✓ CONCLUSION
─────────────────────────────
Decision: {answer}
Confidence: {high|medium|low}
Consensus: {unanimous|majority|mediator-resolved}

Evidence Summary:
| Claim | Type | Source | Weight |
|-------|------|--------|--------|
| {c1}  | cited | {src} | 2 |
| {c2}  | hypothesis | - | 1 |

Dissent: {any unresolved minority position}
Test path: {how to verify decision}

📋 RETROSPECTIVE
────────────────
Process: {effective|mixed|poor}
What worked: {helpful patterns}
What didn't: {friction points}
Missing perspective: {what would have helped}

═══════════════════════════════════════════════════════
END DELIBERATION
═══════════════════════════════════════════════════════
```

### Abort

```
Thought {N}/{max} ❌ ABORT
──────────────────────────
Reason: {why stopping}
Blocker: {what prevents progress}
Recovery: {what would unblock}
Consensus: {agents agree to abort|mediator decision}

═══════════════════════════════════════════════════════
DELIBERATION ABORTED
═══════════════════════════════════════════════════════
```

### Workflow Handoff

```
═══════════════════════════════════════════════════════
HANDOFF: {next_agent}
═══════════════════════════════════════════════════════
From: Deliberation
Problem: {title}
Decision: {conclusion}
Confidence: {level}
Consensus: {type}
Evidence: {key sources}
Dissent: {minority view if any}
Action: {what next agent does}
Test: {how to verify}
═══════════════════════════════════════════════════════
```

## Tool Integration

Agents SHOULD use available tools:

| Action | Tool | When |
|--------|------|------|
| Check existing solutions | web_search | Before proposing new |
| Find implementations | github search | Technical proposals |
| Load domain knowledge | skills, project_knowledge | Domain decisions |
| External validation | GPT-5.2 via MCP | Deadlock or complex |
| Verify file existence | bash_tool, view | Evidence validation |
| Check rule compliance | grep | workflow_enforcer checks |

## WFD Integration

Deliberations MUST log to workflow directory:

```yaml
wfd_logging:
  on_start:
    path: "{WFD}/docs/debates/{YYYYMMDD_HHMMSS}-{topic}.md"
    content: |
      # Debate: {topic}
      Started: {ISO8601}
      Personas: {active list}
      Problem: {user request verbatim}
      
  on_each_thought:
    append: |
      ## Thought {N} [{persona}]
      Position: {position}
      Evidence: {type} | Weight: {weight}
      Source: {citation or "none"}
      
  on_consensus:
    append: |
      ## Consensus Check
      | Persona | Position | Evidence | Weight |
      |---------|----------|----------|--------|
      {rows}
      
      Total: {weighted sum}
      Result: {reached|not reached}
      
  on_conclusion:
    append: |
      ## Conclusion
      Decision: {decision}
      Confidence: {level}
      Test Path: {verification}
      Dissent: {any minority view}
      
    also_create: "{WFD}/docs/debates/{topic}-conclusion.md"
```

### Evidence File Requirements

All deliberation conclusions require:
1. Debate transcript in WFD
2. Evidence summary table
3. Test path for verification
4. Workflow_enforcer sign-off (no VETO active)

## Quick Reference

| Action | Syntax |
|--------|--------|
| Start | `DELIBERATION: {problem}` |
| Think as persona | `Thought N/M [{persona}]` |
| Challenge | `⚔️ challenges [{target}]` |
| Full round | `DELIBERATION ROUND` block |
| Check consensus | `CONSENSUS CHECK` block |
| External review | `External Review` block |
| Stop check | Review stop conditions |
| End | `✓ CONCLUSION` + handoff |

## Examples

### Example: Technical Decision

```
═══════════════════════════════════════════════════════
DELIBERATION: Database choice for new service
Mode: multi-agent | Personas: skeptic, minimalist, expert
═══════════════════════════════════════════════════════

Thought 1/12 [minimalist]
─────────────────────────
PostgreSQL. It's what we already use, team knows it,
and it handles 90% of use cases.

Evidence: [cited: internal tech radar, team survey]
Test path: Verify current Postgres can handle projected load

[Next: challenge]

Thought 2/12 [skeptic] ⚔️ challenges [minimalist]
─────────────────────────────────────────────────
Target claim: Postgres handles 90% of use cases
Challenge: This service needs time-series queries.
           Postgres CAN do it but not optimally.
Evidence: [cited: benchmark showing TimescaleDB 10x faster]

Response from [minimalist]:
TimescaleDB IS Postgres with extension. Keeps familiarity.

Resolution: revise → PostgreSQL + TimescaleDB extension

[Next: consensus]

═══ CONSENSUS CHECK ═══
Position: PostgreSQL + TimescaleDB
Consensus: reached (2/2 agree after revision)

Thought 3/3 ✓ CONCLUSION
─────────────────────────
Decision: PostgreSQL with TimescaleDB extension
Confidence: high
Consensus: unanimous after revision

Test path: Run benchmark with projected load profile
```
