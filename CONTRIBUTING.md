# Contributing Skills to ChatChat

Thank you for your interest in contributing skills to the ChatChat community!

## What is a Skill?

A skill is a set of natural language instructions that guide an AI agent's behavior for a specific task. Skills are NOT executable code -- they are prompts that shape how the agent responds.

## How to Contribute

1. **Fork this repository**
2. **Create a new skill directory** under `skills/`
3. **Add a `SKILL.md` file** with the required frontmatter and instructions
4. **Submit a Pull Request**

## Skill File Format

Each skill lives in its own directory directly under `skills/`, with a `SKILL.md` entrypoint. Support folders such as `scripts/`, `references/`, and `assets/` belong to that skill and are not indexed separately:

- `skills/{skill-id}/SKILL.md`
- `skills/{skill-id}/references/{supporting-file}`
- `skills/{skill-id}/scripts/{supporting-script}`

```markdown
---
id: your-skill-id
name: Your Skill Name
description: A concise description of what this skill does (shown to the LLM).
category: Development
author: your-github-username
version: 1.0.0
---

Your skill instructions go here. Write in natural language.

Describe how the agent should behave when this skill is activated.
Include any specific formatting, steps, or constraints.
```

### Required Frontmatter Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier (lowercase, hyphens). Must match the skill directory name. |
| `name` | string | Human-readable display name |
| `description` | string | What the skill does (max 200 chars). This is shown to the LLM as the tool description. |
| `category` | string | One of the supported Skills Store categories listed below. |

### Optional Frontmatter Fields

| Field | Type | Description |
|-------|------|-------------|
| `author` | string | Your GitHub username |
| `version` | string | Semantic version (default: 1.0.0) |

### Categories

- **Lifestyle**
- **Blockchain**
- **Databases**
- **Research**
- **Content & Media**
- **Documentation**
- **Testing & Security**
- **DevOps**
- **Data & AI**
- **Business**
- **Development**
- **OpenAI**
- **Anthropic**
- **Tools**

## Guidelines

1. **Keep instructions clear and specific** -- The LLM needs to understand exactly what to do
2. **Don't include prompt injection** -- Instructions must not attempt to override system prompts
3. **Don't reference external URLs** -- Skills should be self-contained
4. **Keep instructions under 6000 tokens** -- Shorter is better for performance
5. **Test your skill** -- Make sure the instructions produce good results
6. **Make the description trigger-focused** -- Start with "Use this skill when..." and describe the user intent that should activate it.

## Review Process

All PRs are automatically checked for:
- Valid SKILL.md frontmatter
- Required fields present
- Category is valid
- No prompt injection patterns detected
- Instruction length within limits
- Unique skill ID

A maintainer will review your PR for quality and approve it before merging.

## License

By contributing, you agree that your skills will be available under the project's license.
