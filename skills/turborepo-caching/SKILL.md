---
id: turborepo-caching
name: Turborepo Caching
description: Use this skill when configuring or debugging Turborepo local and remote caching, including task outputs, cache keys, CI reproducibility, cache misses, and developer build performance.
category: DevOps
---

# Turborepo Caching

Improve monorepo build performance through reliable Turborepo caching.

## When to Use

- You need to speed up repeated builds, tests, or lint jobs in a monorepo.
- You are setting up or validating remote cache behavior in CI.
- You need to debug low cache hit rates or stale artifact issues.

## Workflow

1. **Identify cacheable tasks.** Ensure tasks are deterministic: same inputs must produce identical outputs. Exclude tasks that use timestamps, random IDs, or external APIs. Audit each task's `inputs` and `outputs` in `turbo.json`.

2. **Configure inputs and outputs.** Define explicit `inputs` (glob patterns for files that affect the task) and `outputs` (directories or files the task produces). Omit `outputs` only for tasks with no artifacts (e.g., lint). Include environment variables that affect output via `globalEnv` or per-task `env`.

3. **Set up remote cache.** Use `TURBO_TOKEN` and `TURBO_TEAM` (Vercel Remote Cache) or self-hosted options. In CI, set these as secrets. Run `turbo run build --summarize` to verify cache hits in the summary.

4. **Handle environment variables.** Add any env var that changes task output to `globalEnv` in `turbo.json` or to a task's `env` array. Common culprits: `NODE_ENV`, `CI`, `VERCEL_ENV`, custom feature flags. Missing env vars cause incorrect cache hits.

5. **Add cache observability.** Use `turbo run <task> --dry-run=json` to inspect the hash inputs. Run `turbo run build --summarize` and check "Cache hit, replaying output" vs "Cache miss, executing". Add a CI step that fails or warns if cache hit rate drops below a threshold.

6. **Document invalidation rules.** Document when cache is invalidated: input file changes, env changes, `turbo.json` changes. Ensure `.turbo/cache` is in `.gitignore` and that CI does not persist it across unrelated runs.

## turbo.json Configuration Patterns

```json
{
  "$schema": "https://turbo.build/schema.json",
  "globalEnv": ["NODE_ENV", "CI", "CUSTOM_ENV"],
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", ".next/**"],
      "inputs": ["src/**", "package.json", "tsconfig.json"],
      "env": ["PUBLIC_API_URL"]
    },
    "test": {
      "dependsOn": ["build"],
      "outputs": ["coverage/**"],
      "inputs": ["src/**", "test/**"]
    },
    "lint": {
      "outputs": []
    }
  }
}
```

- Use `^build` for internal dependency builds; use `build` for same-package deps.
- Keep `outputs` minimal; avoid `**` if a subset suffices to reduce cache size.
- Add `inputs` when default (all files) is too broad and causes unnecessary misses.

## Cache Debugging Commands

- `turbo run build --summarize` - human-readable summary with cache hit/miss.
- `turbo run build --dry-run=json` - JSON with hash inputs and task graph.
- `turbo run build --force` - bypass cache to verify fresh output.
- `turbo daemon stop` - stop local daemon if cache behavior seems stuck.
- Inspect `node_modules/.cache/turbo` or `.turbo/cache` for local cache location.

## Output Format

```markdown
## Cache Strategy
- Tasks: build, test, lint
- Remote cache: enabled (TURBO_TEAM=team-name)
- Key inputs: src/**, package.json, tsconfig.json
- Key env vars: NODE_ENV, CI, PUBLIC_API_URL

## Config Changes
- turbo.json: added outputs for build, inputs for test
- CI: set TURBO_TOKEN, TURBO_TEAM; add --summarize to turbo run

## Validation Checklist
- [ ] Cache hits observed on repeat runs (no input changes)
- [ ] Cache miss on input change (e.g., edit src file)
- [ ] No stale artifacts in dependent tasks
- [ ] CI and local behavior consistent
- [ ] .turbo/cache in .gitignore
```

## Common Pitfalls

- **Caching non-deterministic outputs.** Builds that embed timestamps, `process.env.GIT_SHA`, or random IDs produce different outputs for same inputs. Cache replays wrong artifacts. Make outputs deterministic or exclude the task from caching.

- **Missing env vars in hash inputs.** If `NODE_ENV=production` changes build output but is not in `globalEnv`, production and development builds can incorrectly share cache. Add all env vars that affect output.

- **Oversized cache artifacts.** Including `node_modules`, `.next/cache`, or large generated assets bloats cache. Restrict `outputs` to what downstream tasks need. Use `.turboignore` or narrow globs.

- **Ignoring .turbo/cache locality.** Local cache lives in `.turbo/cache` or `node_modules/.cache/turbo`. CI runners typically start fresh; remote cache must be configured for CI hits. Ensure TURBO_TOKEN and TURBO_TEAM are set in CI.

- **Wrong dependency graph.** `dependsOn` errors (e.g., missing `^build` for internal deps) cause tasks to run before dependencies complete, producing invalid cache entries.

## Constraints

- Do not recommend caching nondeterministic task outputs.
- Keep guidance compatible with standard Turborepo workflows.
- Avoid provider-specific assumptions unless explicitly requested.
- Always include env vars that affect task output in hash inputs.
- Prefer explicit `inputs` and `outputs` over relying on defaults.
- Document cache invalidation behavior for any new or modified tasks.