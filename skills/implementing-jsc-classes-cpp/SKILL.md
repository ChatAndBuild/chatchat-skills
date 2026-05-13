---
id: implementing-jsc-classes-cpp
name: Implementing JSC Classes C++
description: Use this skill when implementing JavaScriptCore-backed classes in C++, including bindings, lifetime management, method exposure, property behavior, and runtime correctness.
category: Development
---

# Implementing JSC Classes C++

Guide JSC class implementation in C++ with focus on correctness, performance, and maintainability.

## When to Use

- You are exposing native C++ functionality to JavaScriptCore.
- You need safe binding patterns and lifecycle handling.

## Workflow

1. Define JS-facing class surface and native backing model.
2. Implement constructor/method/property bindings.
3. Ensure proper memory ownership and GC interaction.
4. Add error translation and exception-safe behavior.
5. Validate behavior with runtime integration tests.

## Output

- JSC class binding plan
- Memory and lifecycle guidance
- Verification checklist
