# Solid-SQL

Reference: [14] G. Liu et al., "Solid-SQL: Enhanced Schema-linking based In-context Learning for Robust Text-to-SQL," COLING 2025.

Role: schema-linking baseline candidate.

Why it is relevant: cited as a robustness-oriented schema-linking method. It is useful for testing whether the current pipeline's schema filtering agent and schema-error attribution outperform a focused schema-linking baseline.

Run plan:

- Run Solid-SQL on the shared Spider subset.
- Stratify results by schema-linking errors.
- Compare schema_missing_table and schema_hallucinated_element rates.
- Record prompt/model and schema representation details.
