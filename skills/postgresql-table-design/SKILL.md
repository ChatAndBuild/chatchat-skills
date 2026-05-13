---
id: postgresql-table-design
name: PostgreSQL Table Design
description: Use this skill when reasoning about individual PostgreSQL tables and nearby relationships, including keys, constraints, column types, normalization, query-aware indexes, and migration-ready schema decisions.
category: Databases
---

# PostgreSQL Table Design

Use this skill to reason about individual PostgreSQL tables and their immediate neighbors.

## Key Questions
- What does one row represent?
- What makes a row unique?
- Which columns are required at creation time versus later?
- Which queries will hit this table most often?
- What relationships or lifecycle events affect it?

## Design Rules
- Choose a primary key strategy that fits the system and debugging needs.
- Keep columns atomic when the data is queried independently.
- Use check constraints for simple invariants close to the data.
- Design indexes around read paths, not theoretical completeness.
- Include timestamps and status fields only when they serve a real lifecycle purpose.

## Output
- Suggested columns and types.
- Primary key and uniqueness decisions.
- Foreign keys and delete/update behavior.
- Recommended indexes and caveats.
- Notes on future migration pressure.

## Common Errors
- Tables that mix metadata, state, and unrelated aggregates.
- Surrogate keys without any business uniqueness protection.
- Too many nullable columns hiding multiple record types in one table.
- Indexing every column instead of the actual access paths.
