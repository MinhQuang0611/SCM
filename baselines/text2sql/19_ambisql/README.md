# AmbiSQL

Reference: [19] Z. Ding et al., "AmbiSQL: Interactive Ambiguity Detection and Resolution for Text-to-SQL," 2025.

Role: ambiguity detection and intent-stage correction baseline.

Runnable baseline suitability: conditional. It is more suitable for interactive or ambiguity-heavy settings than for a static Spider batch run.

Why it is relevant: the current paper cites ambiguity handling in the intent-understanding heuristics. It can help evaluate intent_missing_condition and hallucinated-assumption cases.

Use later for:

- Intent-stage perturbation tests.
- Interactive clarification experiments.
- Comparing static pipeline logging against explicit ambiguity resolution.
