# DAC

Reference: [11] D. Wang, L. Dou, X. Zhang, Q. Zhu, and W. Che, "DAC: Decomposed Automation Correction for Text-to-SQL," Findings of ACL: EMNLP 2025.

Role: decomposed correction baseline.

Why it is relevant: cited as decomposing correction into entity and skeleton subtasks. It is especially relevant because the current paper finds skeleton/structural errors dominate post-rerun failures.

Run plan:

- Run DAC on the Spider subset.
- Track entity/schema corrections separately from skeleton corrections.
- Compare against current pipeline rerun and attribution labels.
- Check whether DAC improves the dominant skeleton error category.
