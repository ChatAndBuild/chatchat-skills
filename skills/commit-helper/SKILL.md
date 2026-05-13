---
id: commit-helper
name: Commit Helper
description: Use this skill when turning actual code changes into focused commit plans or commit messages, splitting unrelated changes, applying Conventional Commits, or adding reviewer-ready scope and risk notes.
category: Development
---

# Commit Helper

Turn diffs into focused, review-friendly commits and messages that explain intent.

## When to Use

- You need a concise, meaningful commit message.
- A diff contains unrelated changes that should be split.
- You want commit text that helps reviewers and future debugging.

## Conventional Commits Deep Dive

**Type and scope:** Use `type(scope): subject` - e.g., `feat(auth): add OAuth callback`, `fix(api): handle null response`. Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `style`, `perf`. Scope is optional but helps group changes (module, package, or area).

**Breaking patterns:** Use `BREAKING CHANGE:` in the body or append `!` after type/scope: `feat(api)!: remove deprecated endpoint`. Always document migration steps in the body.

**Footer conventions:** Use `Refs: #123` or `Closes #123` for issue references. Use `Co-authored-by: Name <email>` for pair commits. Use `Signed-off-by:` when required by DCO.

## Commit Splitting Techniques

- **git add -p:** Stage hunks interactively (`git add -p <file>`) to separate logical changes. Review each hunk; split further with `s` (split) when needed.
- **Interactive rebase for reordering:** Use `git rebase -i HEAD~N` to reorder, squash, or edit commits. Use `edit` to pause, amend, then `git rebase --continue`. Never rebase shared branches without coordination.

## Commit Message Anti-Patterns and Fixes

| Anti-pattern | Fix |
|--------------|-----|
| "fix stuff", "update", "misc" | Use specific type and scope: `fix(login): resolve redirect loop` |
| Body repeats diff line-by-line | Describe intent, impact, and why; omit implementation detail |
| No breaking change note | Add `BREAKING CHANGE:` and migration steps when API/behavior changes |
| Subject over 72 chars | Shorten; move detail to body |
| Mixed languages | Use project default (usually English) consistently |

## Common Pitfalls

- **Giant commits mixing refactor+feature:** Split with `git add -p` or interactive rebase. One commit per logical change.
- **Misleading commit types:** Using `fix` for refactors or `feat` for config tweaks. Match type to actual impact.
- **Empty commit messages from squash merges:** Configure squash to preserve or combine commit messages; avoid single-line "Merge" when meaningful history matters.
- **Committing generated files:** Exclude build artifacts, lockfiles (when not intentional), and secrets. Use `.gitignore` and pre-commit hooks.

## Workflow

1. Inspect staged/unstaged changes and identify logical change groups.
2. Determine commit type and scope (feature, fix, refactor, docs, test, chore).
3. Draft subject line:
   - Imperative mood
   - Specific scope
   - No vague terms like "update stuff"
4. Add body for why/impact when change is non-trivial.
5. Include breaking change or migration notes when applicable.
6. Suggest commit splitting if changes mix unrelated concerns.
7. Verify message matches actual diff contents.

## Message Checklist

- [ ] Subject is under ~72 characters and unambiguous.
- [ ] Body explains intent and behavior impact, not line-by-line edits.
- [ ] Any risks, follow-ups, or migration steps are captured.
- [ ] Commit does not include accidental generated/secrets files.

## Output Format

Return:

- **Recommended commit grouping strategy:** Which changes belong together and in what order.
- **Final commit message(s):** One per logical commit, in Conventional Commits format with optional body and footers.
- **Optional alternative phrasings:** Shorter or more detailed variants.
- **Risks or missing checks:** Breaking changes, files to exclude, tests to run before push.
- **Splitting guidance:** If split needed, exact `git add -p` or rebase steps.

## Constraints

- Do not invent work not present in the diff.
- Avoid generic subjects ("misc fixes", "changes").
- Keep one commit focused on one logical purpose.