---
id: skill-creator
name: skill-creator
description: Create new skills, modify and improve existing skills, and measure skill performance. Use when users want to create a skill from scratch, edit, or optimize an existing skill, run evals to test a skill, benchmark skill performance with variance analysis, or optimize a skill's description for better triggering accuracy.
category: Anthropic
author: anthropic
license: Complete terms in LICENSE.txt
---

# Skill Creator

Use this skill to create new agent skills, revise existing skills, evaluate whether a skill improves outcomes, benchmark skill performance, and optimize frontmatter descriptions for better trigger accuracy.

The full upstream Anthropic instructions are preserved in [references/upstream-skill-creator.md](references/upstream-skill-creator.md). Load that file when you need the complete detailed workflow. Keep this `SKILL.md` as the quick dispatcher so the repo validation limit is respected.

## Core Workflow

1. Capture the intended skill behavior, trigger situations, expected output, dependencies, and success criteria.
2. Draft or revise the skill with a concise `SKILL.md`, clear frontmatter, and progressive disclosure through `references/`, `scripts/`, or `assets/` when needed.
3. Create realistic test prompts before writing assertions.
4. Run with-skill and baseline comparisons when evaluation is useful.
5. Grade outputs, aggregate benchmark results, and review qualitative differences.
6. Improve the skill based on user feedback and benchmark findings.
7. Optimize the description if trigger accuracy matters.

If the user wants to work informally without evals, skip the benchmark loop and help draft or revise the skill directly.

## Skill Authoring Guidance

- Keep `SKILL.md` focused on operational instructions the agent needs at trigger time.
- Put large details in reference files and tell the agent exactly when to load them.
- Use scripts for deterministic or repeated work instead of asking the model to rewrite fragile code every time.
- Use assets for output resources such as templates, icons, fonts, boilerplate, or sample files.
- Descriptions should say what the skill does and when to use it. Include realistic trigger phrases, file types, systems, or task contexts.
- Avoid misleading, harmful, or surprising skills.

For the complete upstream writing guide, evaluation loop, benchmark schema, description optimization process, Claude.ai adaptations, and cowork-specific instructions, read [references/upstream-skill-creator.md](references/upstream-skill-creator.md).

## Bundled Resources

- `agents/grader.md` - rubric-based grading guidance for eval outputs.
- `agents/analyzer.md` - benchmark analysis guidance.
- `agents/comparator.md` - blind comparison guidance.
- `assets/eval_review.html` - HTML template for reviewing trigger eval queries.
- `eval-viewer/` - viewer for qualitative output review and benchmark summaries.
- `references/schemas.md` - expected eval, grading, benchmark, and feedback schemas.
- `scripts/aggregate_benchmark.py` - aggregate graded runs into benchmark outputs.
- `scripts/generate_report.py` - generate reports from evaluation data.
- `scripts/improve_description.py` and `scripts/run_loop.py` - trigger-description optimization workflow.
- `scripts/package_skill.py` - package a completed skill when packaging is supported.
- `scripts/quick_validate.py` and `scripts/run_eval.py` - validation and eval helpers.

## Evaluation Notes

When running skill evals:

- Save workspaces beside the skill directory, grouped by iteration and eval case.
- Run with-skill and baseline cases in the same iteration so timing and environment are comparable.
- Use objective assertions where possible, and keep subjective outputs available for human review.
- Preserve timing and token metadata from run notifications when available.
- Use `eval-viewer/generate_review.py` for review instead of writing a custom viewer.

For exact commands, directory structures, JSON formats, and viewer behavior, load [references/upstream-skill-creator.md](references/upstream-skill-creator.md) and [references/schemas.md](references/schemas.md).
