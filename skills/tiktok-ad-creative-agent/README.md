# TikTok Ad Creative Agent

An AI-agent skill package for turning product pages, ecommerce offers, ad briefs, images, or raw campaign notes into TikTok-ready ad creative packages and production workflows.

It helps advertisers, media buyers, creative strategists, brand operators, and growth teams create hooks, creative angles, storyboards, voiceover scripts, AI image/video prompts, editing briefs, compliance checks, delivery checklists, and launch test plans.

## Quick Start

1. Place this folder where your agent runtime can load skills, for example:

   ```bash
   ~/.codex/skills/tiktok-ad-creative-agent
   ```

2. Ask your agent to use the skill for a TikTok ad creative task:

   ```text
   Use the TikTok Ad Creative Agent to turn this product page into 5 hooks, 3 ad angles, and a 30-second storyboard.
   ```

3. Provide the product source or brief. Useful inputs include:

   - Product page, Amazon listing, ecommerce URL, app store page, or landing page
   - Product images or brand assets
   - Offer details, price, discount, audience, claims, proof points, and campaign goal
   - Desired duration, aspect ratio, language, voiceover style, and audio direction

4. For a planning request, the agent returns a structured creative package.

5. For a finished video or generated-media request, the agent must first confirm the creative direction, then ask which tools or models to use for image/video generation, voiceover, BGM/SFX, and final assembly.

## Target Platforms

This package is designed for AI-agent environments that can read a `SKILL.md` file and load bundled Markdown resources on demand.

Primary target:

- Codex skill-compatible runtimes

Portable usage:

- ChatGPT, Claude, Gemini, or other AI assistants can use the instructions if the `SKILL.md`, `references/`, and `assets/` files are made available in context or through a file-enabled workspace.

Platform notes:

- The skill is tool-neutral and does not require a specific image model, video model, editor, voiceover provider, or MCP server.
- Production-stage work depends on the tools available in the active environment.
- If a target platform cannot use image references for generation, the exact product image should be composited in post or the user should approve a different production path.

## Prerequisites And Dependencies

Runtime requirements:

- An AI agent or assistant that can follow Markdown instructions.
- File access to this package's `SKILL.md`, `references/`, and `assets/` directories.
- Product source material supplied by the user or extracted from a provided page, document, or image.

Optional production dependencies:

- Image generation tool or model
- Video generation tool or model
- Voiceover generation tool
- BGM/SFX source or generator
- Video assembly or rendering tool
- Editing environment for captions, overlays, safe-area checks, and final export

No fixed MCP server, external agent, API key, or provider-specific model is required by default.

## Configuration

The skill does not require a config file. Configure each job through the user brief.

Common configurable options:

| Option | Default / Guidance |
| --- | --- |
| Product source | User-provided URL, page, PDF, image, document, or brief |
| Output type | Planning package unless the user asks for production or final video |
| Duration | 15s, 30s, 45s, or 60s depending on campaign need |
| Aspect ratio | TikTok-first vertical video, usually 9:16 |
| Language | Match the user's requested market or brief language |
| Audio | BGM is on by default unless the user opts out |
| Production tools | Must be selected or confirmed by the user before production starts |
| Product references | Required before generating visuals that depict a specific product |
| Compliance posture | Review for risk, but do not present it as legal or platform-policy clearance |

## Package Contents

```text
tiktok-ad-creative-agent/
├── SKILL.md
├── README.md
├── assets/
│   ├── audio-post-template.md
│   ├── creative-brief-template.md
│   ├── launch-test-plan-template.md
│   ├── qc-scorecard-template.md
│   ├── source-ledger-template.md
│   ├── storyboard-template.md
│   └── voiceover-template.md
└── references/
    ├── asset-generation.md
    ├── audio-post-production.md
    ├── compliance-qc.md
    ├── creative-angles.md
    ├── delivery-checklist.md
    ├── editing-brief.md
    ├── human-approval-gates.md
    ├── intake.md
    ├── iteration-loop.md
    ├── offer-and-audience.md
    ├── product-page-extraction.md
    ├── prompt-templates.md
    ├── remotion-captioning.md
    └── storyboard-formats.md
```

## Typical Workflow

1. Gather the brief, product source, campaign objective, duration, aspect ratio, language, and audio preference.
2. Extract product facts, offer details, reviews, proof points, product references, and missing fields.
3. Identify the buyer, pain points, objections, triggers, and reason to believe.
4. Select creative angles from `references/creative-angles.md`.
5. Generate 1-3 second hooks mapped to audience tensions.
6. Build a timed storyboard with visuals, voiceover, on-screen copy, product exposure, and CTA.
7. Confirm the creative direction before spending credits or generating production media.
8. Ask the user to choose or approve production tools.
9. Generate prompts, assets, audio, captions, and editing instructions when production is requested.
10. Run compliance QC, iteration review, and delivery checks before final handoff.

## Common Errors And Handling

| Issue | How To Handle It |
| --- | --- |
| Missing product facts | Ask for the missing facts or mark them as unknown. Do not invent claims, prices, guarantees, or proof. |
| Incomplete source page | Keep a source ledger and clearly separate extracted facts from assumptions. |
| No product reference image | Stop before product-specific visual generation and request a usable product image. |
| User approves creative but has not selected tools | Ask for image/video, voiceover, BGM/SFX, and assembly tool choices before production. |
| AI model cannot preserve product appearance | Use it only for non-product shots, composite the exact product image in post, or ask for another tool path. |
| Readable text needed in generated visuals | Avoid putting exact legal lines, pricing, logos, or readable brand text into generation prompts; add exact text in post. |
| Sensitive or regulated claims | Run compliance QC and flag risk. Do not present the review as legal, medical, financial, or platform-policy clearance. |
| User asks for final video immediately | Treat it as a production request, show the creative draft first, and get confirmation before production. |

## Limitations And Notes

- This skill does not replace professional legal, medical, financial, or platform-policy review.
- It should not invent product details, awards, reviews, endorsements, performance numbers, or scarcity claims.
- It does not guarantee TikTok approval or ad performance.
- Finished-video production depends on available generation, voiceover, audio, and editing tools.
- Generated media may require human review for product accuracy, brand safety, claim support, safe areas, captions, and final platform readiness.

## Maintainers And Feedback

This package should be maintained by the team or individual responsible for TikTok ad creative operations in the workspace where it is installed.

When reporting issues, include:

- The input source or brief type
- Requested output type
- Target market and language
- Tools or models used, if production was requested
- The generated package or artifact that needs review
- Any claim, compliance, or product-accuracy concern
