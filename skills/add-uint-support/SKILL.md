---
id: add-uint-support
name: Add UInt Support
description: Use this skill when introducing unsigned integer handling into an existing codebase, covering parsing, validation, storage, serialization, APIs, arithmetic boundaries, and overflow compatibility risks.
category: Development
---

# Add UInt Support

Use this skill when introducing unsigned integer handling into an existing codebase.

## When to Use

- A new field should accept only non-negative integers.
- Existing signed types need migration to unsigned types.
- You need safe type conversion across API, business logic, and persistence layers.

## Workflow

1. Identify all boundaries: request parsing, DTOs, domain models, DB schema, and serialization.
2. Define exact range constraints (e.g., uint32 vs uint64).
3. Add validation for negative and out-of-range inputs.
4. Update conversion logic to avoid silent casts and overflow.
5. Update DB/schema types and migration scripts where needed.
6. Add API contract notes (breaking vs non-breaking behavior).
7. Add tests for min/max values, negative inputs, and overflow attempts.

## Common Pitfalls

- Implicit casts from signed to unsigned types
- Inconsistent validation between API and DB
- JSON number precision issues in JS clients
- Missing migration strategy for existing negative values

## Output

- Type migration plan
- Validation and conversion checklist
- Boundary test cases (min/max/invalid)

- Brief plan or checklist
- Key recommendations and caveats
