# Who and When Failure Attribution

Reference: [12] S. Zhang et al., "Which agent causes task failures and when? On automated failure attribution of LLM multi-agent systems," ICML 2025.

Role: general MAS failure-attribution benchmark.

Runnable baseline suitability: not a Text-to-SQL generator baseline.

Why it is relevant: the current paper cites it as evidence that automated MAS failure attribution remains difficult. It is a conceptual comparator for the proposed Text-to-SQL-specific Logging Matrix.

Use in protocol:

- Compare attribution problem definitions.
- Check whether the current labels can be mapped to generic who/when attribution labels.
- Avoid treating its reported attribution accuracy as a Text-to-SQL generation baseline.
