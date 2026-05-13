---
id: implementing-agent-modes
name: Implementing Agent Modes
description: Use this skill when adding mode-aware behavior to an AI agent, including explicit triggers, permissions, response contracts, and plan, ask, debug, or execute style interaction modes.
category: Development
---

# Implementing Agent Modes

Design and implement explicit agent modes so behavior is predictable, safe, and testable.

## When to Use

- You are designing an AI assistant with multiple interaction modes.
- You need strict boundaries between planning, read-only analysis, and execution.
- You want consistent mode transitions and user-visible expectations.

## Core Mode Model

For each mode, define:

- Allowed actions (read, write, execute, external calls)
- Required evidence level before conclusions
- User confirmation requirements
- Output style and expected artifacts
- Failure behavior (what to do when intent is ambiguous or tools fail)

## Mode Design Patterns

**State machine for mode transitions.** Model modes as states and transitions as edges. Each transition has a trigger (user command, explicit button, timeout) and optional guard (e.g., "only if user confirmed"). Invalid transitions return an error or prompt for clarification. Document the state machine as a table: Current Mode x Requested Mode -> Allowed (Y/N) + Action.

**Permission matrix implementation.** Maintain a matrix: Mode x Action Type (read_file, write_file, run_command, call_api) -> Allowed. Check this matrix before every tool invocation. Reject with a clear message ("Execute mode required for file writes") when the action is disallowed. Log blocked attempts for drift detection.

**Confirmation dialogs for mode escalation.** When transitioning from a lower-risk mode (ask, plan) to a higher-risk mode (execute), require explicit user confirmation. Present a summary of planned actions and a single "Proceed" or "Cancel" choice. Do not auto-escalate based on inferred intent.

## Mode Transition Examples

- **ask -> plan:** User says "I want to add a feature." Allowed; no confirmation.
- **plan -> execute:** User says "Do it." Require confirmation with action summary.
- **execute -> ask:** User says "Stop" or "Switch to ask." Allowed; cancel pending actions if any.
- **debug -> execute:** User approves a fix. Require confirmation; execute only the approved fix.
- **execute -> execute:** Same mode; no transition. Reject if user tries to switch to plan mid-execution without explicit cancel.

## Mode Testing Strategies

**Scenario scripts.** Write scripts that simulate user flows: "User in ask mode requests file edit" -> expect blocked. "User in plan mode requests execution" -> expect confirmation prompt. "User confirms" -> expect execution. Run these as automated tests.

**Boundary testing between modes.** Test transitions at boundaries: first message in a session, mode switch mid-conversation, rapid successive mode changes. Ensure no state leakage (e.g., execute permissions carrying over after switch to ask).

**Permission drift detection.** Add regression tests that assert the permission matrix. When a new tool or action type is added, the test suite must explicitly allow or deny it per mode. Fail the build if an action is invoked in a mode where it is not explicitly permitted.

## Common Pitfalls

**Implicit mode changes from context.** Do not infer mode from phrasing like "go ahead" or "fix it" without explicit mode keywords or UI actions. Treat ambiguous requests as staying in the current mode or prompting for clarification.

**Modes with overlapping permissions.** If plan and execute both allow file reads, ensure they differ clearly on writes. Overlapping semantics cause inconsistent behavior when users expect one mode but get another.

**No fallback for ambiguous intent.** When the user's intent is unclear, default to the safest mode (ask or plan). Never default to execute. Provide a short disambiguation prompt: "Did you want me to (a) plan the changes or (b) execute them?"

**Testing only happy paths.** Include failure cases: tool errors, timeouts, user cancel, invalid transitions. Verify that the agent degrades gracefully and does not silently fall back to execute.

## Workflow

1. Enumerate modes and responsibilities (e.g., plan, ask, debug, execute).
2. Specify transition rules and who can initiate transitions.
3. Implement guardrails:
   - Prevent writes in read-only modes
   - Require explicit approval before risky actions
   - Enforce validation/checks in execution modes
4. Add telemetry for mode entry, exit, and blocked actions.
5. Test with scenario scripts that include mis-clicks and ambiguous requests.
6. Add regression tests to ensure mode permissions do not drift over time.

## Output Format

Return a structured specification:

```markdown
## Mode Matrix
| Mode   | read | write | execute | external | confirmation |
|--------|------|-------|---------|----------|--------------|
| ask    | Y    | N     | N       | N        | -            |
| plan   | Y    | N     | N       | N        | -            |
| debug  | Y    | N     | N       | Y (read) | -            |
| execute| Y    | Y     | Y       | Y        | before first write |

## Transition Graph
| From   | To      | Trigger        | Guard              |
|--------|---------|----------------|--------------------|
| ask    | plan    | "plan" keyword  | -                  |
| plan   | execute | "execute" + UI  | user confirmation  |
| execute| ask     | "stop" keyword  | cancel pending     |

## Safety Controls
- Confirmation points: <list>
- Blocked action handling: <message and log>
- Ambiguous intent: <default mode + prompt>

## Test Scenarios
- Scenario 1: <setup> -> <action> -> <expected outcome>
- Scenario 2: <setup> -> <action> -> <expected outcome>
- Boundary: <edge case> -> <expected outcome>
```

## Constraints

- No hidden mode changes; transitions must be explicit.
- Avoid overlapping mode semantics that cause inconsistent behavior.
- Treat uncertain intent as plan/ask, not execute.
- Deny-by-default for write/execute capabilities in new modes until explicitly allowed.