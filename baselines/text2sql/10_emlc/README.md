# EMLC

Reference: [10] J. Lei, Y. Tan, and Y. Wang, "EMLC: An extensible multi-level correction framework for Text-to-SQL," Information Processing & Management, 2026.

Role: multi-level correction baseline.

Why it is relevant: cited as applying correction across schema, skeleton, and executability layers. This is directly comparable to the current paper's claim that failures must be attributed beyond final execution.

Run plan:

- Run EMLC on the same Spider subset.
- Compare correction effectiveness by layer.
- Map EMLC levels to current categories: intent, schema, skeleton, execution.
- Evaluate whether EMLC exposes enough intermediate state for failure attribution.
