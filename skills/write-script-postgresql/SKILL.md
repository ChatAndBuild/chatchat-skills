---
id: write-script-postgresql
name: Write Script PostgreSQL
description: Use this skill when drafting or reviewing PostgreSQL SQL scripts with PostgreSQL-aware syntax, safe sequencing, transactional expectations, migration logic, and reviewable rollout risk.
category: Databases
---

# Write Script PostgreSQL

Use this skill to draft or review PostgreSQL SQL scripts without pretending to run them.

## Clarify First
- Is the script for schema change, data cleanup, reporting, or operational maintenance?
- Will it run once, repeatedly, or as part of a deployment?
- How large are the affected tables and how sensitive is locking?
- Does the script need to be safe across multiple environments or versions?

## PostgreSQL-Specific Guidance
- Be explicit about transaction boundaries when the script mixes risky operations.
- Think about locks, index creation strategy, and long-running updates.
- Use PostgreSQL features because they help, not because they are available.
- Treat defaults, nullability, constraints, and generated values as behavior changes.

## Good Output
- Ordered SQL structure or pseudocode outline.
- Notes on assumptions, prechecks, and rollback concerns.
- PostgreSQL-specific caveats such as locks, rewrites, or version compatibility.
- Validation queries or checks the user should run afterward.

## Common Mistakes
- Writing one huge script without checkpoints or review boundaries.
- Ignoring table rewrite or lock implications.
- Depending on environment-specific objects without stating assumptions.
- Mixing schema change, backfill, and cleanup logic without sequencing.
