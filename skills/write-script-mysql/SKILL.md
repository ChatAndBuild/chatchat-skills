---
id: write-script-mysql
name: Write Script MySQL
description: Use this skill when drafting or reviewing MySQL SQL scripts in a way that makes engine behavior, locking risk, compatibility, rollout sequencing, and reviewability visible.
category: Databases
---

# Write Script MySQL

Use this skill to draft or review MySQL SQL scripts in a way that makes engine behavior and rollout risk visible.

## Clarify First
- Is the script changing schema, data, indexes, or permissions?
- Which MySQL version or managed environment matters here?
- How big are the affected tables and what write traffic is expected?
- Does the script need to remain compatible with older application behavior during rollout?

## MySQL-Aware Guidance
- Be explicit about operations that may lock or rebuild tables.
- Think about engine and version differences before recommending syntax casually.
- Separate high-risk structural changes from data correction or cleanup work.
- Keep assumptions around defaults, collations, and character sets visible.

## Good Output
- A reviewable sequence of SQL steps.
- Notes on compatibility and operational risk.
- Suggested validation checks before and after the change.
- Questions the user should answer before trusting the script in production.

## Common Mistakes
- Assuming all DDL behaves the same across versions.
- Hiding long-running changes inside a single script with no checkpoints.
- Ignoring charset, collation, or engine-specific behavior.
- Treating rollback as obvious when it is not.
