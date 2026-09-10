# SQL2NL Evaluation

Reference: [15] M. Safarzadeh, A. Oroojlooyjadid, and D. Roth, "Evaluating NL2SQL via SQL2NL," 2025.

Role: evaluation-side diagnostic comparator.

Runnable baseline suitability: not a competing Text-to-SQL generator.

Why it is relevant: it can be used as an auxiliary metric or diagnostic check for whether generated SQL preserves the natural-language meaning, especially when EM is low but EX passes.

Use later for:

- Evaluation robustness checks.
- Cases where SQL differs structurally from gold SQL but may be semantically equivalent.
- Logging quality analysis for explanation/faithfulness.
