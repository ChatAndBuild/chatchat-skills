# Audio Post Production

Use this reference when the user wants a finished ad cut, voiceover, BGM, sound effects, or production handoff for audio.

## Default Audio Architecture

Separate visual generation from audio and text:

- Generate visual footage without model-made captions, logos, price, reviews, or app UI.
- Add voiceover, BGM, realistic sound effects, ambience, captions, CTA, legal text, and product lockup in post.
- Keep exact claims in approved text layers and voiceover, not inside generated visuals.
- Default BGM is on unless the user opts out.
- Sound effects and ambience are not optional polish; they should support visible actions and spaces.
- Keep generated video sound enabled when the model/tool can provide useful natural sync sound. If the model audio is poor, misleading, or not controllable, replace or supplement it in post.

## Voiceover

Preferred production options:

- Human VO.
- ElevenLabs.
- Minimax voice.
- Another advertiser-approved TTS provider.

Fallback options:

- Local system TTS for timing drafts only after the user selects it, delegates tool choice, or the task is clearly non-production timing work.
- Text-only VO copy when no audio tool is available.

Always label placeholder VO clearly.

For production requests, do not silently choose local/system TTS or any default audio tool after creative approval. Ask for voiceover, BGM, and SFX/audio tool choices first unless the user explicitly delegated tool choice.

## BGM

Preferred production options:

- Licensed TikTok-safe music.
- Generated BGM with confirmed commercial usage rights.
- Brand-owned music bed.

Fallback options:

- Low-volume synthesized timing bed for internal drafts.
- Clearly labeled placeholder music bed when usage rights are unclear.
- No BGM only when the user opts out, the creative specifically requires no music, or no safe placeholder can be used.

## Sound Effects

Use realistic sound design for visible actions and environments:

- Product taps.
- Product pickup/put-down.
- Object friction on a table, such as coffee cup, cable, charger, keyboard, or bag movement.
- Cable plug.
- Cable drag.
- Bag zip.
- Room tone, cafe noise, office hum, street/airport ambience, white noise.
- Transition hits.
- UI-neutral whooshes.

Avoid cartoon sounds unless the creative style calls for them.

## Mix Rules

- VO should stay front and intelligible.
- BGM should support pace, not compete.
- SFX should mark transitions and product moments.
- Keep enough headroom for platform encoding.
- Export standard AAC audio at 48 kHz for final MP4 drafts.

## Claim Safety

- Voiceover must keep source-backed qualifiers such as "up to."
- Do not add price, discount, rating, review count, or scarcity language unless approved.
- If claim wording differs between captions and VO, fix before delivery.

## Output

Return:

- VO copy.
- Caption copy.
- BGM direction.
- Ambience and SFX cue sheet.
- Audio replacement plan.
- Final audio mix notes.
