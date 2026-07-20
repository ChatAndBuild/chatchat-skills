# Asset Generation

Use this reference when image or video assets are requested.

## Tool Rule

If the user names an approved image/video generation tool, use only that tool for generated image and video assets. Do not substitute another generator. If that tool is unavailable, continue with prompts, editing notes, and a command plan, then state what is waiting on tool access.

Ask users which image, video, voiceover, and SFX/audio models they want when asset generation is requested. Do not ask whether those models support specific modes or parameters; verify that yourself before generation.

For production requests, generate final media only after the user confirms the creative draft and chooses the production tools/models. A short creative approval does not choose tools. If the user explicitly grants permission to skip draft approval or delegate tool choice, document that and continue.

Do not use local/system defaults such as system TTS, ffmpeg-only composition, locally installed CLIs, or available APIs as a silent fallback. Use them only when the user selected them, previously approved them for this job, or explicitly said the agent may choose defaults.

## Generation Ladder

1. Product reference assets.
2. Visual references.
3. Short video segments.
4. Audio assets: voiceover, BGM, realistic action SFX, ambience, and transition sounds.
5. Assembly plan.
6. QC and selective regeneration.

## Product Reference Gate

For a specific product ad, product reference images are required before any image or video generation that depicts the product.

- Treat URLs, ecommerce pages, PDFs, documents, screenshots, uploaded images, and brand folders as possible product image sources.
- Extract or save at least one usable product image, packshot, or source screenshot before visual generation. Prefer multiple angles when available.
- Record the source of each product reference image in the source ledger.
- Match the selected variant, color, size, bundle, and packaging when the source provides variants.
- Pass the product reference image into the chosen image/video model whenever the tool supports image references.
- If the chosen tool cannot use image references, do not ask it to recreate the product from text. Use it only for backgrounds, hands, lifestyle context, transitions, or non-product shots, then composite the exact product image or approved packshot in post.
- If no usable product image is available, ask the user for one or switch to a non-product visual plan. Do not generate a product look from text alone.
- If the product reference is low resolution, cropped, watermarked, or ambiguous, tell the user the risk and ask for a better image before final production.

This is not a user capability question. After tool selection, inspect whether the chosen tool can accept image references; if not, choose the background/composite path or ask for an approved alternative.

## What AI Visuals Should Do

- Create background, lifestyle, demo, and transition shots.
- Preserve product shape, color family, materials, proportions, visible controls, packaging, and use case from the supplied product reference images.
- Leave safe space for exact captions and product cards.
- Support one ad beat at a time.

## What AI Visuals Should Not Do

- Render exact legal text, price, review quotes, ratings, or brand copy.
- Invent logos, awards, badges, app screens, claims, or UI.
- Show unsafe product use.
- Create before/after claims that the source page does not support.

Real product brand marks and real-world companion devices are allowed when they are factually appropriate to the product and source assets. Do not mechanically ban a laptop, phone, or known device brand from a charger, accessory, case, app, or electronics ad. Reject only when the visual invents misleading text, fake UI, incorrect product details, or unsupported claims.

## Screen Guidance

When a phone, laptop, tablet, watch, dashboard, or app screen appears:

- Prefer screen-off, face-down, closed, cropped, or blurred screens.
- If a screen must be visible, describe only abstract light, color, or motion.
- Never ask the generator to create a real app UI, store page, rating screen, music player, review card, payment page, or message thread unless the user supplies exact approved artwork for post-production.
- Treat any generated readable UI as a failed asset.

## Segment Prompt Fields

- Segment name.
- Duration.
- Purpose.
- Source product facts used.
- Reference images needed.
- Scene action.
- Camera and motion.
- Style.
- Negative guidance.
- Post-production text to add later.
- QC checks for this segment.

## Regeneration Policy

Regenerate a segment when:

- Product is distorted.
- Product shape, color, packaging, layout, controls, or scale does not match the reference image.
- The visual contains fake text or logo artifacts.
- A phone, laptop, or app screen contains fake UI or pseudo-text.
- The beat does not match the storyboard.
- The clip is too static for paid social.
- The claim becomes stronger than the source supports.

Regenerate only the failing segment when possible.

## Video QA

After each generated video:

- Download the output.
- Confirm aspect ratio, duration, and file integrity.
- Check at least three frames: early, middle, and late.
- Reject any clip with generated text, fake UI, distorted product, unsafe usage, or off-brief action.
- Preserve rejected clips in the run notes when useful; they teach the next prompt revision.

## Audio Asset QA

For generated or post-produced audio:

- Default BGM is on unless the user opts out.
- Keep video/model sound enabled when the chosen tool can produce useful natural action sound; replace or supplement in post when it is noisy, misleading, or off-sync.
- Add realistic foley and ambience for visible actions: product taps, cable drag, plug clicks, bag zip, coffee cup movement, room tone, cafe noise, office hum, street/airport bed, and soft transition whooshes.
- Distinguish BGM from sound design. BGM is the music bed; SFX/ambience are diegetic or environment sounds.
- Verify that the final file has an audio stream and that sound supports the visible action.
