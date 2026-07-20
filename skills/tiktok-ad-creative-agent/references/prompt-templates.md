# Prompt Templates

Use this reference when the user asks for AI image or AI video prompts. Keep prompts tool-neutral unless the user names a specific generator.

## Image Reference Prompt

```text
Create a 9:16 vertical product ad reference image for [product/category].

Product reference inputs:
[List exact product image paths/URLs/source screenshots. Required for a specific product.]

Scene:
[Describe the environment, product moment, subject, and action.]

Visual style:
[UGC handheld / premium studio / stop-motion / clean 3D / lifestyle / cinematic / tabletop demo.]

Composition:
[Foreground, midground, background, product placement, negative space for captions.]

Lighting and color:
[Brand palette, mood, realism level.]

Important constraints:
- Use the supplied product reference image for product appearance.
- Preserve product shape, color, material, controls, packaging, and proportions.
- No readable text.
- No fake logos.
- No invented packaging claims.
- Keep the product area clean for post-production overlay.
- Leave safe space for TikTok UI and captions.
```

## Video Segment Prompt

```text
Generate a [duration] second 9:16 vertical ad segment.

Product reference inputs:
[List exact product image paths/URLs/source screenshots. Required for segments showing the specific product.]

Purpose:
[Hook / product reveal / demo / proof / routine / lifestyle outcome / CTA background.]

Action:
[What happens second by second.]

Camera:
[Handheld, close-up, tabletop push-in, smooth orbit, quick cuts, creator POV.]

Subject:
[Person, product, hand demo, environment, pet, object, or abstract metaphor.]

Product consistency:
[How the visible product must match the supplied reference images; if the model cannot accept image references, keep the product out of the generated shot and add it in post.]

Style:
[Natural UGC / polished ad / 3D / stop-motion / realistic product demo.]

Do not include:
- Readable text.
- Logos unless supplied as an exact post-production overlay.
- Fake app screens.
- Visible phone/laptop UI unless exact artwork is supplied for post-production.
- Medical, financial, or guaranteed outcome visuals.
```

## Negative Prompt Block

Use when a generator supports negative guidance:

```text
No readable text, no fake logos, no misspelled packaging, no invented product shape, no invented packaging, no fake app UI, no pseudo-text on screens, no extra fingers, no distorted product, no medical visuals, no extreme before/after, no unsafe behavior, no claims displayed in-scene.
```

## Prompt Quality Checklist

- The prompt has one job.
- It describes action, not just mood.
- It specifies aspect ratio and safe area.
- It separates visuals from exact post-production text.
- It avoids unverified claims.
- It leaves room for captions and CTA.
- It includes product reference image inputs when the segment shows a specific product.
- It avoids generating a specific product from text alone.
