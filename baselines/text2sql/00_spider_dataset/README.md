# Spider Dataset

Reference: [1] T. Yu et al., "Spider: A Large-Scale Human-Labeled Dataset for Complex and Cross-Domain Semantic Parsing and Text-to-SQL Task," EMNLP 2018.

Role: shared dataset and metric basis, not a model baseline.

Why it matters: `Text2SQL_Hallucination.pdf` evaluates the current MAS pipeline on 7,000 Spider train instances and reports EX before and after rerun. Any baseline comparison should reuse the same Spider subset, SQLite databases, and metric implementation.

First setup target:

- Build a small deterministic subset.
- Preserve original question, db_id, schema, gold SQL, and difficulty.
- Run all candidate baselines and the current pipeline on exactly this subset.
- Report EX, EM, syntax error rate, and failed execution count.

Local placeholders:

- `data/`: Spider subset manifest and database links.
- `code/`: metric wrappers and subset generation scripts.
- `results/`: baseline-independent metric outputs.
- `logs/`: dataset preparation logs.
