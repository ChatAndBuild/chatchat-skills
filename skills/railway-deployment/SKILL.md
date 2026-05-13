---
id: railway-deployment
name: Railway Deployment
description: Use this skill when deploying to Railway, including environment checks, service configuration, health verification, rollout observation, logs, and rollback readiness.
category: DevOps
---

# Railway Deployment

Guide Railway deployments from preflight validation to post-deploy verification.

## When to Use

- You are preparing to deploy or update an application on Railway.
- You need a repeatable deployment checklist with explicit verification.
- You want to minimize release risk with rollback planning.

## Workflow

1. **Confirm deployment target and intended version/change scope.** Identify the project and service(s). Choose deployment region (e.g., US West, EU) if relevant. Note whether this is a new deploy or an update.

2. **Validate runtime and configuration.** Use `railway.json` or `Procfile` to define build and start commands explicitly; do not rely on Nixpacks guessing. Example `railway.json`: `{"build": {"builder": "NIXPACKS"}, "deploy": {"startCommand": "npm run start", "restartPolicyType": "ON_FAILURE", "restartPolicyMaxRetries": 3}}`. For databases, ensure TCP proxy is enabled if connecting from external clients; Railway exposes `DATABASE_URL` with internal hostnames.

3. **Configure volume mounts and environment groups.** If the app needs persistent storage, add a volume and mount path in the Railway dashboard. Use environment variable groups to separate staging from production. Reference variables with `$VAR` syntax in `railway.json` or dashboard.

4. **Identify risky changes.** Review schema migrations, breaking env changes, and external API dependencies. Plan migration order (e.g., run migrations before deploy or use backward-compatible migrations).

5. **Define verification plan.** Ensure a health check endpoint exists and returns 200. Railway does not require a health check path for basic deploys, but configuring one improves reliability. Plan checks for critical user flows and error rate.

6. **Execute deploy and monitor.** Use `railway up` or connect a GitHub repo for automatic deploys. Watch build and deploy logs in the dashboard or via `railway logs`. On Starter plan, services may sleep after inactivity; document this behavior.

7. **Trigger rollback if checks fail.** Use Railway's deployment history: Dashboard -> Service -> Deployments -> select previous deploy -> Redeploy. Capture incident notes for post-mortem.

## Common Pitfalls

- **Not setting start command.** Nixpacks may guess incorrectly (e.g., wrong entry point or missing flags). Always set `startCommand` in `railway.json`, `Procfile`, or dashboard.
- **Missing health check endpoint.** Without a health endpoint, Railway cannot detect unhealthy instances; consider adding `/health` or similar for monitoring and load balancer checks.
- **Ignoring Railway sleep on Starter plan.** Services sleep after inactivity; first requests after sleep can be slow. Use a paid plan or external cron to keep services warm for production.
- **Database connection pooling with serverless.** If using serverless runtimes (e.g., serverless functions), connection pooling can exhaust database connections. Use connection poolers (e.g., PgBouncer) or serverless-friendly drivers.

## Railway CLI and Configuration

```bash
railway login
railway link          # Link to existing project
railway up            # Deploy from current directory
railway logs          # Stream logs
railway run <cmd>     # Run command with env vars injected
railway variables     # List env vars
```

Example `railway.json`:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "npm run build"
  },
  "deploy": {
    "startCommand": "npm run start",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 30,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

Example `Procfile`: `web: npm run start`

## Rollback and Monitoring

Railway stores deployment history per service. Rollback: Dashboard -> select service -> Deployments -> choose previous successful deploy -> Redeploy. Use `railway logs` for real-time debugging. Integrate with external monitoring (e.g., Sentry, Datadog) for error tracking and performance.

## Output Format

```markdown
## Deployment Plan
- Target service: <name>
- Change scope: <summary>
- Region: <if applicable>
- Start command: <explicit command>

## Preflight Checklist
- [ ] Required env vars validated
- [ ] Runtime/build settings confirmed (railway.json or Procfile)
- [ ] Migration risk reviewed
- [ ] Health check endpoint configured
- [ ] Volume mounts configured if needed

## Commands
1. railway up
2. railway logs

## Verification
- [ ] Health endpoint passes
- [ ] Key user flow validated
- [ ] Error rate and logs normal
- [ ] Sleep behavior documented (Starter plan)

## Rollback
- Trigger: <condition>
- Action: Dashboard -> Deployments -> select prior deploy -> Redeploy
- Notes: <incident capture>
```

## Constraints

- Prefer deterministic checklists and explicit pass/fail criteria.
- Do not assume deploy success until verification steps are complete.
- Highlight unknowns instead of guessing environment details.
- Always set startCommand explicitly; do not rely on Nixpacks detection alone.
- Document sleep behavior for Starter plan services.
