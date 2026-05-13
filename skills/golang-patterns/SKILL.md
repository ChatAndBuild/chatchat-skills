---
id: golang-patterns
name: Golang Patterns
description: Use this skill when implementing or reviewing Go code that needs idiomatic concurrency, error handling, interface design, package structure, service patterns, readability, correctness, or maintainability.
category: Development
---

# Golang Patterns

Apply idiomatic Go patterns that keep code explicit, testable, and production-safe.

## When to Use

- You are writing or reviewing production Go code.
- You need safer concurrency and cancellation behavior.
- You want cleaner package structure and testability.

## Core Patterns

**Error wrapping:** Use `fmt.Errorf("context: %w", err)` to wrap errors and preserve the chain. Use `errors.Is` and `errors.As` for unwrapping.

```go
if err != nil {
    return fmt.Errorf("fetch user %s: %w", id, err)
}
if errors.Is(err, ErrNotFound) { /* handle */ }
```

**Sentinel errors:** Define package-level `var ErrX = errors.New("x")` for expected conditions. Use `errors.Is` for checks.

**Context patterns:** Use `context.WithCancel` when you need to signal stop; use `context.WithTimeout` or `context.WithDeadline` for bounded work. Always pass context as first parameter.

```go
ctx, cancel := context.WithTimeout(parent, 5*time.Second)
defer cancel()
result, err := doWork(ctx)
```

**sync.WaitGroup and errgroup:** Use `errgroup.Group` when you need to run goroutines and collect the first error. Use `WaitGroup` for fire-and-forget parallelism with explicit sync.

```go
g, ctx := errgroup.WithContext(ctx)
g.Go(func() error { return fetchA(ctx) })
g.Go(func() error { return fetchB(ctx) })
if err := g.Wait(); err != nil { return err }
```

**Table-driven tests:** Structure tests as a slice of cases with inputs and expected outputs. Loop over cases and run subtests.

```go
for _, tc := range []struct{ name string; input int; want int }{
    {"zero", 0, 0}, {"positive", 1, 1},
} {
    t.Run(tc.name, func(t *testing.T) {
        if got := fn(tc.input); got != tc.want { t.Errorf("got %d", got) }
    })
}
```

**Interface segregation at call site:** Define interfaces where they are used, with only the methods needed. Avoid large shared interfaces.

## Concurrency Patterns

**Worker pool:** Use a buffered channel as a job queue; spawn N workers that read from the channel. Close the channel when done; workers exit when channel is closed.

**Fan-out/fan-in:** Start multiple goroutines that produce into a channel; one goroutine (or a merge function) reads from all and aggregates. Use `sync.WaitGroup` to know when producers are done.

**Channel select with timeout:** Use `select` with `<-time.After(d)` or `<-ctx.Done()` to avoid blocking forever.

```go
select {
case result := <-ch:
    return result, nil
case <-ctx.Done():
    return nil, ctx.Err()
case <-time.After(10 * time.Second):
    return nil, ErrTimeout
}
```

## Common Pitfalls

- **Goroutine leaks:** Goroutines that block on channels or I/O without a cancellation path leak. Always provide `context` or a done channel.
- **Shared state without mutex:** Accessing maps or slices from multiple goroutines without sync causes data races. Use `sync.Mutex` or channels.
- **defer in loops:** `defer` in a loop defers until the enclosing function returns, not each iteration. Use an explicit function call or wrap in a closure.
- **Interface pollution:** Large interfaces that many types implement create unnecessary coupling. Prefer small, focused interfaces.
- **init() side effects:** Avoid global state or I/O in `init()`. Makes testing and reasoning harder. Prefer explicit setup.

## Workflow

1. Identify code path and performance/reliability constraints.
2. Select patterns that directly solve the current problem.
3. Implement minimal changes with clear ownership boundaries.
4. Add table-driven tests and race-aware coverage where relevant.
5. Validate with linting, static checks, and targeted benchmarks.
6. Confirm cancellation and shutdown paths under failure conditions.

## Output Format

```markdown
## Pattern Choices and Rationale
- <pattern>: <why it fits>

## Before/After Architecture
- <structural changes>
- <ownership boundaries>

## Error and Concurrency Guarantees
- Error wrapping: <locations and chain>
- Context propagation: <boundaries>
- Goroutine lifecycle: <start, stop, leak check>

## Concurrency Pattern Applied
- <worker pool | fan-out/fan-in | select timeout | other>
- Code sketch: <snippet if applicable>

## Pitfall Check
- Goroutine leaks: <assessment>
- Shared state: <mutex/channel usage>
- defer/init: <issues if any>

## Test Additions
- Table-driven cases: <coverage>
- Race detector: <recommendation>

## Residual Risks
- <remaining concerns>
```

## Constraints

- Avoid premature abstractions that hide control flow.
- Do not launch goroutines without cancellation and shutdown strategy.
- Prefer explicit dependencies over global mutable state.
- Avoid panics in library code; return typed errors where possible.