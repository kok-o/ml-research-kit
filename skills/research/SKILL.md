---
name: research
description: >-
  Compare technologies, formats, tools, or other alternatives for a decision. Investigate
  disputed claims across documents, issue reports, studies, or other evidence when the user
  needs a sourced explanation. For ML paper review, training experiments, or GPU benchmark
  scoring, prefer ml-research if available.
---

# Research

Start with the question the answer must settle. For a decision, identify the user's
constraints and the finding that would change the choice. For a factual question, define
the term, population, place, version, or time period wherever it changes the answer.
If a missing detail matters, investigate both plausible cases or ask one focused question.

## Follow the claim to its evidence

- Start with the supplied material. For each consequential claim, find the closest source
  of evidence: the original dataset or study, the applicable policy, the implementation,
  or an account from someone who observed the event. Use independent analysis when the
  original source has a stake in the outcome or leaves an important gap.
- Open the evidence and check what it actually covers. Track the passage, table, version,
  or file that supports the claim. Several articles repeating the same announcement count
  as one origin. For changing facts, check when the rule or change took effect.
- Seek the strongest exception or alternative explanation that could alter the answer.
- If a small, permitted check would settle a material uncertainty, run it and record
  the inputs and result. A test of today's behavior supports a claim about today's behavior.
  A claim about future guarantees needs a source that actually makes that commitment.

## Compare like with like

Whenever sources disagree, write down the conditions for each claim **before** choosing
which applies. Include only differences that could explain the conflict. For an I/O claim,
this might be block size, warm cache versus cold disk, library or driver version, and load.
For a policy or study, it might be jurisdiction, effective date, definitions, or population.
Mark a missing condition as unknown. State whether the difference explains the apparent
conflict and which conditions match the user's case.

## Conclude at the level the evidence supports

Lead with the answer. Put a source link or a local file reference beside each material
finding. Make it clear where a source reports an observation and where you draw an inference.
For an explanation, give the best-supported account and any unresolved disagreement that
affects it. If the decisive gap requires an ML experiment, hand off the hypothesis, baseline,
metric, and missing evidence to `ml-research` when available.

Stop once further searching is unlikely to change the answer or its stated limits.
If a decisive source is inaccessible, say what is missing and how it could be checked.
Use the sources and tools available in the current agent; local files alone can support
a bounded investigation. Never cite a source you only intended to inspect.

End the response with one line labeled **Decision Flip Trigger**. Name the concrete fact,
measurement, or changed requirement that would reverse the recommendation. For a factual
explanation, name the evidence that would overturn it. If the decision is still open,
identify the missing observation and how its possible outcomes select between the options.
