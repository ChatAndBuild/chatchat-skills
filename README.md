# ChatChat Community Skills

Community-contributed skills for ChatChat AI agents. Try at chatchat.com. 
Skills are natural language instruction sets that guide agent behavior for specific tasks.

## What are Agent Skills?

Agent Skills are folders of instructions, scripts, and resources that agents can discover and use to perform tasks more accurately. Each skill is a directory with a `SKILL.md` entrypoint and optional supporting files.

```
my-skill/
├── SKILL.md          # Required: instructions + metadata
├── scripts/          # Optional: executable code
├── references/       # Optional: documentation
└── assets/           # Optional: templates, resources
```

Skills use **progressive disclosure**: agents load only the name and description at startup, then read full instructions when a task matches. This keeps context usage efficient while giving agents access to detailed knowledge on demand.

## Using Skills

Skills from this repository are automatically synced to the ChatChat Skills Store. To use a skill:

1. Open your agent's profile page
2. Click **Edit** next to the Skills section
3. Browse the Skills Store
4. Click **Install** on any skill

The installed skill will be available as a tool the LLM can automatically invoke when relevant.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed instructions on how to create and submit skills.

## Structure

```
skills/
  prep-meeting/
    SKILL.md
    scripts/
    references/
  react-performance/
    SKILL.md
    assets/
  ...
index.json          # Auto-generated manifest (do not edit manually)
```

Each skill directory lives directly under `skills/`. Support folders such as `scripts/`, `references/`, and `assets/` belong to that skill and are not indexed separately.

## Categories

Each skill declares a `category` in its frontmatter. Categories help users browse the Skills Store and should reflect the user-facing purpose of the skill.

Common categories you’ll see:
- Lifestyle
- Blockchain
- Databases
- Research
- Content & Media
- Documentation
- Testing & Security
- DevOps
- Data & AI
- Business
- Development
- OpenAI
- Tools

Use the most specific, user-friendly category that matches the skill’s primary intent. If a skill spans multiple domains, pick the category users would most likely search.
