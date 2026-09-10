# Text-to-SQL Error Correction with Language Models of Code

Reference: [18] Z. Chen et al., "Text-to-SQL Error Correction with Language Models of Code," ACL 2023 Short Papers.

Role: error-correction baseline.

Why it is relevant: cited under skeleton/subquery and SQL error correction. It provides an older correction baseline focused on improving SQL outputs using code language models.

Run plan:

- Use generated SQL from a matched initial model or the current pipeline pre-rerun output.
- Apply the correction method on the same Spider subset.
- Compare before/after EX and syntax error reduction.
- Check whether semantic skeleton errors remain after correction.
