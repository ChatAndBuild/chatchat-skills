---
id: migrate-frontend-forms
name: Migrate Frontend Forms
description: Use this skill when migrating frontend forms, form libraries, validation schemas, submission flows, or accessibility behavior while minimizing regressions in production systems.
category: Development
---

# Migrate Frontend Forms

Migrate forms incrementally, preserve user-visible behavior, and verify submission reliability before rollout.

## When to Use

- You are changing form frameworks, validation engines, or schema formats.
- You need to reduce migration risk across many forms without halting delivery.
- You want a repeatable checklist for behavior parity and rollout safety.

## Migration Patterns

**Formik to React Hook Form**: Replace `useFormik` with `useForm`; map `values` to `watch`, `errors` to `formState.errors`, `handleChange` to `register` or `Controller`. Use `Controller` for custom components that need `value`/`onChange`. Preserve `submitCount` and `touched` semantics if used for UX; RHF uses `formState.isSubmitted` and `formState.touchedFields`.

**Yup to Zod**: Convert `yup.object({ ... })` to `z.object({ ... })`. Yup's `string().required()` becomes `z.string().min(1)` or `z.string().nonempty()`. For async validation, use `z.refine()` or `z.superRefine()`. Map nested objects and arrays; preserve `transform` logic in Zod's `.transform()` or preprocessors. Run both schemas in parallel during migration to catch divergence.

**Controlled vs uncontrolled**: Formik is controlled; RHF supports both. For large forms, prefer uncontrolled with `register` for performance. If migrating to uncontrolled, ensure `defaultValues` match prior initial values and that refs are attached correctly for validation.

**API payload adapter**: Isolate submission logic in an adapter: `(formData) => toLegacyPayload(formData)` or `(formData) => toNewPayload(formData)`. Ensures backend contract stays stable during migration; swap adapter when backend is ready.

## Common Pitfalls

- **Breaking form state during migration**: Changing `defaultValues` or field names mid-session can reset or corrupt state. Migrate one form at a time; avoid changing field names without a data migration step.
- **Validation timing differences**: Formik validates on blur/submit by default; RHF can validate on change, blur, or submit. Align `mode` (e.g. `onBlur` or `onSubmit`) to match prior behavior.
- **Accessibility regressions**: Swapping `Input` for a different component can break `aria-describedby`, `aria-invalid`, or label association. Verify `id`/`htmlFor` and error announcement hooks; test with screen reader.
- **Feature flag overhead**: Per-form flags add complexity. Prefer route-based or user-segment flags; limit flag count and document removal timeline.
- **CSS/layout breakage**: New component structure (different wrapper divs, class names) can break layout. Snapshot or diff layout before/after; preserve outer structure if needed.

## Migration Checklist

- [ ] Validation behavior matches prior implementation or approved spec.
- [ ] API payload shape is unchanged or backend-compatible.
- [ ] Error and loading states are visible and actionable.
- [ ] Tests cover critical paths and edge cases.
- [ ] Schema parity verified (Yup vs Zod output same errors for same inputs).
- [ ] Accessibility: labels, error announcements, keyboard focus.
- [ ] Layout and CSS unchanged or intentionally updated.

## Workflow

1. Inventory forms by complexity, traffic, and business criticality.
2. Define parity contract: field defaults, validation timing, error messaging, submission payload.
3. Migrate one representative form first; document reusable patterns and adapter.
4. Add automated tests for happy path, validation failures, disabled/loading states.
5. Gate rollout using feature flags or route-based segmentation.
6. Run cross-browser and accessibility checks.
7. Migrate remaining forms in batches; monitor error/abandonment metrics post-release.

## Output Format

Return:

- **Form inventory**: Forms by complexity, traffic, criticality, and migration order.
- **Parity contract**: Field-by-field mapping, validation rules, payload shape.
- **Reusable patterns**: Schema conversion examples, adapter interface, Controller usage.
- **Migration checklist**: Per-form verification steps (validation, payload, a11y, layout).
- **Rollout plan**: Feature flag strategy, batch order, rollback criteria.

## Constraints

- Avoid all-at-once rewrites for high-traffic forms.
- Do not ship changes without payload compatibility verification.
- Keep rollback path available until post-release metrics stabilize.
- Preserve accessibility semantics during component replacement.
