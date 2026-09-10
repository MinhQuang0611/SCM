# SCoT2S

Reference: [3] C. Zhu, Y. Lin, Y. Cai, and Y. Li, "SCoT2S: Self-correcting Text-to-SQL parsing by leveraging LLMs," Computer Speech & Language, 2026.

Role: correction baseline.

Why it is relevant: the source paper cites SCoT2S as an execution/SQL-level iterative self-correction approach. It is a useful contrast because the current MAS paper argues that execution-only correction misses deeper intent, schema, and skeleton failures.

Run plan:

- Use the same Spider subset as the current pipeline.
- Feed initial SQL and execution feedback according to the SCoT2S protocol.
- Compare pre-correction and post-correction EX.
- Log whether correction changes the root-cause category or only fixes final syntax/execution symptoms.
