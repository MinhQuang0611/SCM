# SelECT-SQL

Reference: [16] K. Shen and M. Kejriwal, "SelECT-SQL: Self-correcting ensemble Chain-of-Thought for Text-to-SQL," 2024.

Role: ensemble self-correction baseline.

Why it is relevant: cited for reasoning hallucinations and self-correcting ensemble chain-of-thought. It can test whether ensemble correction improves EX without stage-level attribution.

Run plan:

- Run on the same Spider subset.
- Keep candidate count and model settings explicit.
- Compare EX/EM and token cost against current MAS rerun.
- Record whether ensemble disagreement provides useful failure-attribution signal.
