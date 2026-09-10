# SQL-to-Schema

Reference: [17] S. Yang et al., "SQL-to-Schema Enhances Schema Linking in Text-to-SQL," 2024.

Role: schema-linking component baseline.

Runnable baseline suitability: suitable as a component baseline if the current MAS pipeline can swap or wrap schema-selection modules.

Why it is relevant: the current paper cites it in the schema filtering stage and schema-alignment threshold discussion. It is directly tied to schema_missing_table and schema_hallucinated_element failures.

Run plan:

- Evaluate on the same Spider subset.
- Compare schema candidate recall and precision before final SQL generation.
- Measure downstream EX impact if the component can be integrated.
- Log mappings to `x5` filtered schema and `x6` schema alignment.
