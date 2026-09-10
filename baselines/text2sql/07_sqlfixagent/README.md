# SQLFixAgent

Reference: [7] J. Cen, J. Liu, Z. Li, and J. Wang, "SQLFixAgent: Towards Semantic-Accurate Text-to-SQL Parsing via Consistency-Enhanced Multi-Agent Collaboration," AAAI 2025.

Role: multi-agent correction baseline candidate.

Why it is relevant: cited as a multi-agent system for semantic-accurate Text-to-SQL via consistency-enhanced collaboration. It is useful for testing whether the current pipeline's attribution logs add value beyond multi-agent correction.

Run plan:

- Confirm official implementation or prompt details.
- Run on the shared Spider subset.
- Compare corrected SQL EX/EM and semantic failure categories.
- Capture consistency/candidate traces if exposed.
