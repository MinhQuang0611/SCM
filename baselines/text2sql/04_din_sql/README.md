# DIN-SQL

Reference: [4] M. Pourreza and D. Rafiei, "DIN-SQL: Decomposed In-Context Learning of Text-to-SQL with Self-Correction," NeurIPS 2023.

Role: primary baseline system candidate.

Why it is relevant: the source paper states that DIN-SQL decomposes Text-to-SQL into schema linking, query classification, and self-correction, yielding roughly 10 percent gains over monolithic prompting. This makes it the closest clean baseline for the current multi-stage MAS pipeline.

Run plan:

- Reproduce DIN-SQL on the same Spider subset.
- Use the same LLM backbone where possible, or record model differences explicitly.
- Compare EX and EM against the current pipeline.
- Add adapter logging for schema linking, classification, generated SQL, execution result, and correction trace.

Decision: run first unless implementation access blocks progress.
