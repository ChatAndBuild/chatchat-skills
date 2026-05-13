---
id: anndata
name: AnnData
description: Use this skill when working with AnnData in scalable single-cell workflows, including backed mode, layers, obs/var metadata, sparse matrices, batch processing, and Scanpy-style pipelines.
category: Data & AI
---

# AnnData

Help the agent provide practical guidance for AnnData modeling, storage, and analysis workflows.

## When to Use

- The user needs help structuring or manipulating AnnData objects.
- The user asks about memory usage, I/O formats, or interoperability.
- The user wants implementation details for robust single-cell pipelines.

## Instructions

1. Clarify data volume, schema, and downstream analysis goals.
2. Recommend AnnData layout conventions for `X`, `obs`, `var`, and layers.
3. Suggest efficient loading, slicing, and persistence patterns.
4. Highlight common pitfalls (shape mismatch, metadata drift, memory blowups).
5. End with a reproducible validation checklist.

## Output

- Recommended AnnData approach and rationale
- Step-by-step implementation checklist
- Validation and troubleshooting checks
