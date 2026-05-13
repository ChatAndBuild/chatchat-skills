---
id: develop-ai-functions-example
name: Develop AI Functions Example
description: Use this skill when designing or implementing AI function and tool interfaces with clear schemas, deterministic behavior, safe error handling, and examples for assistants or agent workflows.
category: Development
---

# Develop AI Functions Example

Build AI functions that are easy for models to call correctly and safe to operate in production.

## When to Use

- You are introducing function/tool calling for an assistant.
- Tool calls are failing due to weak schemas or ambiguous descriptions.
- You need a reference pattern for robust AI-action pipelines.

## Function-Calling Patterns

Use OpenAI function schema format: `name`, `description`, `parameters` (JSON Schema). The description is the primary signal for model disambiguation; write it as a single sentence stating when to call the tool and what it does. Example: "Fetch current weather for a given city. Call when the user asks about temperature, conditions, or forecast."

Parameter validation: use JSON Schema `required`, `type`, `enum`, and `const` for restricted values. Prefer `enum` over free-form strings when the set is small and known. Example: `"unit": { "type": "string", "enum": ["celsius", "fahrenheit"], "default": "celsius" }`. Use `minLength`, `maxLength`, and `pattern` for strings; `minimum`/`maximum` for numbers. Always mark optional parameters explicitly; omit from `required` and provide `default` when sensible.

Concrete schema example:

```json
{
  "type": "function",
  "function": {
    "name": "get_weather",
    "description": "Fetch current weather for a city. Call when user asks about temperature, conditions, or forecast.",
    "parameters": {
      "type": "object",
      "properties": {
        "city": { "type": "string", "description": "City name, e.g. San Francisco" },
        "unit": { "type": "string", "enum": ["celsius", "fahrenheit"], "default": "celsius" }
      },
      "required": ["city"]
    }
  }
}
```

## Error Handling Design

Return structured error responses: `{ "error": true, "code": "RATE_LIMITED", "message": "API limit reached", "retryable": true }`. Use `retryable` so the caller can decide whether to retry. For non-retryable errors (e.g. invalid input), set `retryable: false`. Never expose stack traces or internal paths to the model. Implement graceful degradation: if a non-critical sub-operation fails, return partial success with a `warnings` array instead of failing the entire call.

## Common Pitfalls

- **Overloaded functions**: A single "do-everything" tool confuses models. Split by intent (e.g. `search_docs` vs `create_draft`).
- **Vague descriptions**: "Get data" is useless. "Fetch user's order history by order ID. Call when user asks about past orders or order status."
- **Missing required fields**: Omitting `required` leads to incomplete calls. Always specify required inputs.
- **Not testing with diverse prompts**: Test with paraphrased requests, typos, and multi-turn contexts to catch selection and argument errors.
- **Side effects without confirmation**: For destructive actions, require an explicit confirmation parameter or two-step flow; never execute on first call.

## Workflow

1. Define each function by intent, inputs, side effects, and failure modes.
2. Create strict JSON schemas with required fields, enums, and constraints.
3. Write concise, disambiguation-focused descriptions.
4. Implement runtime validation before any external side effect.
5. Return structured errors with `code`, `message`, `retryable`.
6. Add idempotency and guardrails for write operations.
7. Test with realistic and diverse prompts.

## Quality Checklist

- [ ] Function boundaries are single-purpose and composable.
- [ ] Input schema prevents ambiguous or unsafe arguments.
- [ ] Failures are explicit and non-silent.
- [ ] Observability logs tool usage and outcome.

## Output Format

Return:

- **Function catalog**: Name, description, parameters (with types and enums), required fields, example values.
- **Validation and error-handling strategy**: Schema validation layer, error codes, retry semantics.
- **Example call/response pairs**: Valid request, success response, and at least two error responses (retryable and non-retryable).
- **Risks, safeguards, and test coverage gaps**: Known failure modes, mitigations, and missing test scenarios.

## Constraints

- Avoid overloaded "do-everything" functions.
- Never execute side effects without validated inputs.
- Do not leak internal stack traces in model-facing errors.
