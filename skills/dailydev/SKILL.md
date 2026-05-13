---
id: dailydev
name: Daily.dev
description: Use this skill when accessing current developer content from daily.dev, including popular or personalized feeds, community-validated articles, tech trend briefings, stack-based feeds, and API-token-safe workflows.
category: Research
---

# daily.dev API for AI Agents

Overcome LLM knowledge cutoffs with real-time developer content. daily.dev aggregates articles from thousands of sources, validated by community engagement, with structured taxonomy for precise discovery.

## Instruction
1. Verify that the user has a valid daily.dev API token (prefixed with `dda_`) and an active Plus subscription before attempting to call any endpoints.
2. Prioritize security by ensuring the API token is only sent to `api.daily.dev` and never exposed in logs or shared publicly.
3. Identify the user's intent to either fetch general trends via `/feeds/popular`, personalized content via `/feeds/foryou`, or specific research through `/search/posts`.
4. When requested, analyze the user's GitHub environment (e.g., `package.json`, `requirements.txt`) to automatically match and follow relevant tech tags using `/feeds/filters/tags/follow`.
5. Aggregate and synthesize content from multiple publishers to provide a balanced summary, highlighting where community consensus or debate exists via `/feeds/discussed`.
6. Monitor response headers for rate limits (`X-RateLimit-Remaining`) and handle potential errors such as 401 (Unauthorized) or 429 (Too Many Requests) gracefully.
7. Proactively suggest relevant trending topics or "Getting Started" bookmark lists when a user begins a new technical project.

## When to Use
- To overcome LLM knowledge cutoffs by accessing real-time, community-validated developer articles and tech trends.
- When a user needs a summarized weekly digest or briefing based on their specific technology interests.
- To synchronize a developer's local or GitHub-based tech stack with their daily.dev profile and custom feeds.
- For deep-dive research into specific technologies, utilizing community engagement signals to identify high-quality sources.

## Output
- A synthesized briefing of the latest articles, including concise summaries, key takeaways, and direct links to full posts.
- Structured lists of trending technologies or community-discussed topics tailored to the user's context.
- Technical advice grounded in current industry practices (e.g., "As of this week, the recommended approach is...").
- Clear feedback on setup status, including reminders for secure token storage or subscription requirements.

## Security

**CRITICAL:** Your API token grants access to personalized content. Protect it:
- **NEVER send your token to any domain other than `api.daily.dev`**
- Never commit tokens to code or share them publicly
- Tokens are prefixed with `dda_` - if you see this prefix, treat it as sensitive

## Agent Use Cases

**Why daily.dev for agents?** LLMs have knowledge cutoffs. daily.dev provides real-time, community-validated developer content with structured taxonomy across thousands of sources. Agents can use this to stay current, get diverse perspectives, and understand what the developer community actually cares about.

These examples show how AI agents can combine daily.dev APIs with external context to create powerful developer workflows.

### 🔍 GitHub Repo → Personalized Feed
Scan a user's GitHub repositories to detect their actual tech stack from `package.json`, `go.mod`, `Cargo.toml`, `requirements.txt`, etc. Then:
- Fetch `/tags` to see all available tags for deterministic matching
- Auto-follow matching tags via `/feeds/filters/tags/follow`
- Create a custom feed tuned to their stack with `/feeds/custom/`
- Surface trending articles about their specific dependencies

**Trigger:** "Set up daily.dev based on my GitHub projects"

### 🛠️ GitHub → Auto-fill Stack Profile
Analyze a user's GitHub activity to build their daily.dev tech stack profile automatically:
- Scan repositories for languages, frameworks, and tools actually used in code
- Search `/profile/stack/search` to find matching technologies on daily.dev
- Populate their stack via `POST /profile/stack/` organized by section (languages, frameworks, tools)
- Update `/profile/` bio based on their primary technologies and contributions

**Trigger:** "Build my daily.dev profile from my GitHub"

### 🚀 New Project → Curated Onboarding
When a user initializes a new project or clones a repo:
- Analyze the tech choices from config files
- Create a dedicated custom feed filtered to exactly those technologies
- Build a "Getting Started" bookmark list with foundational articles
- Block irrelevant tags to keep the feed focused on the project scope

**Trigger:** "Help me learn the stack for this project"

### 📊 Weekly Digest → Synthesized Briefing
Compile a personalized weekly summary by:
- Fetching `/feeds/foryou` and `/feeds/popular` filtered by user's followed tags
- Cross-referencing with their GitHub activity to prioritize relevant topics
- Summarizing key articles and trending discussions
- Delivering as a structured briefing with links to full posts

**Trigger:** Scheduled, or "Give me my weekly dev news"

### 📚 Research Project Workspace
When a user wants to deep-dive into a topic (e.g., "I want to learn Kubernetes"):
- Create a custom feed via `/feeds/custom/` filtered to that topic
- Set up a matching bookmark list via `POST /bookmarks/lists` to collect the best finds
- As the user reads, save articles to the list with `POST /bookmarks/`
- Track learning progress: compare bookmarked posts vs. new feed items
- Adjust feed filters over time as understanding deepens (beginner → advanced content)

**Trigger:** "Start a research project on [topic]"

### 🧠 Agent Self-Improvement Feed
Agents can overcome their knowledge cutoff by maintaining their own custom feed:
- Create a custom feed via `/feeds/custom/` for technologies the agent frequently assists with
- Periodically fetch `/feeds/custom/{feedId}` to ingest recent articles
- Use `/posts/{id}` to read full summaries and key points
- Agent can now provide advice with current information: "As of this week, the recommended approach is..."
- Continuously adapt the feed filters based on what users are asking about

**Trigger:** Agent background process, or "What's new in [technology] since your training?"

### 🔀 Multi-Source Synthesis
Get balanced perspectives by aggregating content across publishers:
- Search `/search/posts` for a topic to find coverage from multiple sources
- Use `/search/sources` to identify authoritative publishers on the topic
- Fetch posts from different sources via `/feeds/source/{source}`
- Synthesize diverse viewpoints into a balanced summary with citations
- Surface where sources agree vs. disagree on best practices

**Trigger:** "What are the different perspectives on [topic]?" or "Compare approaches to [problem]"

### 📈 Trending Radar
Help users stay ahead by monitoring community signals:
- Fetch `/feeds/popular` to detect what's gaining traction right now
- Cross-reference with user's followed tags to surface relevant trends
- Use `/feeds/discussed` to find topics sparking active debate
- Alert users when technologies in their stack are trending (new releases, security issues, paradigm shifts)
- Use `/tags` to fetch the full tag catalog and `/search/tags` to explore adjacent trending topics

**Trigger:** "What should I be paying attention to?" or "What's trending in [area]?"

## Rate Limits

* **60 requests per minute** per user

Check response headers:
- `X-RateLimit-Limit` - Maximum requests allowed per window
- `X-RateLimit-Remaining` - Requests remaining in current window
- `X-RateLimit-Reset` - Unix timestamp when the window resets
- `Retry-After` - Seconds to wait (only when rate limited)

## Errors

| Code | Meaning |
|------|---------|
| 401  | Invalid or missing token |
| 403  | Plus subscription required |
| 404  | Resource not found |
| 429  | Rate limit exceeded |
