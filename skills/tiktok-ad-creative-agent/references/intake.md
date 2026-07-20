# Intake

Use this reference when the user gives a product, landing page, offer, or rough ad idea and wants TikTok ad creative output.

## Minimum Inputs

- Product name.
- Category.
- Creative brief or campaign direction. If absent, ask for one before final production.
- Target buyer.
- Main offer or conversion goal.
- Available proof points.
- Required or forbidden claims.
- Existing assets: product photos, demo footage, reviews, founder footage, UGC, brand guidelines.
- Market and language.
- Aspect ratio or output size. Default TikTok assumption is 9:16, but confirm when the user has not specified.
- Desired length. Ask when missing; do not silently choose a duration for generated media.
- Whether the user wants final assembly into a finished cut, or only strategy/prompts/assets.

## Production Tool Inputs

Ask for these only after the user confirms the creative draft for production:

- Desired image model/tool.
- Desired video model/tool.
- Desired voiceover model/tool.
- Desired BGM/SFX audio model/tool.
- Desired assembly/rendering tool.

A short approval such as "yes", "ok", "looks good", "confirm", "approved", "好呀", "可以", or "确认" confirms only the creative draft. It does not select tools and does not authorize the agent to choose local/default tools.

If the user has not selected tools after creative approval, ask the production tool question and stop. Do not run production-stage commands, download production assets, generate media, synthesize audio, create a render/assembly project, assemble a timeline, or export a video until the user either selects tools or explicitly delegates tool choice with wording such as "you choose", "use defaults", "你来选", or "用默认".

## Best Intake Questions

Ask only what is necessary to avoid weak creative.

1. What is the product and what does it help the buyer do?
2. Who is the buyer and what problem are they already trying to solve?
3. What creative direction do you want: pain point, comparison, unboxing, real-life routine, review, offer, demo, or another angle?
4. What aspect ratio and duration should the output use?
5. What is the offer, price point, discount, bundle, trial, or CTA?
6. What proof can be safely used: demos, reviews, stats, ingredients, expert quotes, press, certifications?
7. What claims must be avoided?
8. What assets are available now?
9. What is the desired tone: premium, casual, funny, direct-response, founder-led, educational, cozy, high-energy?
10. Do you want final assembly into a finished cut?

After the creative draft is approved for production, ask:

1. Which image and video models/tools do you want to use?
2. Which voiceover, BGM, and SFX/audio models/tools do you want to use?
3. Which assembly/rendering tool should create the final cut?
4. If you want me to choose the tools, say so explicitly.

## If Inputs Are Missing

Make conservative assumptions and label them. Do not invent facts. When the missing detail affects compliance, creative direction, aspect ratio, duration, or final assembly, ask before producing the creative draft. Ask for model and tool choices after the user approves the creative draft for production.

Do not ask users to reason about model capabilities such as supported parameters, duration limits, or input modes. Ask which model they want to use; inspect capabilities yourself when executing.

Do not treat local availability as consent. Finding Node, ffmpeg, system TTS, a browser, a local editor, or any installed generator does not mean those tools are approved for production.

## Production Request Handling

If the user says to make, generate, produce, render, or create a TikTok ad/video from a brief, do not stop at a planning package. Produce the creative draft first, ask the user to confirm or revise it, then continue into tool selection and production.

The confirmation prompt must name the production path. Say that after confirmation the agent can make/render/assemble the finished video, then ask for tool/model choices. Do not end a production request by offering only a "production package", prompt pack, subtitle file, voiceover draft, BGM/SFX table, or editing timeline unless the user asked for an editor handoff instead of a rendered video.

Use this shape in the user's language:

`Please confirm whether this creative direction is approved or what to revise. Once approved, I can continue into finished video production: choose the image/video, voiceover, BGM/SFX, and assembly tools; generate the assets; assemble the cut; run QC; and deliver the video.`

Chinese example:

- Bad: `确认这个方向后，我可以继续给你做成片级生产包：逐镜头提示词、字幕文件、配音稿、BGM/SFX 表和剪辑时间线。`
- Good: `确认这个方向后，我可以继续进入视频成片制作：先确认要用的生图/生视频、旁白、BGM/SFX 和合成工具，然后生成素材、合成剪辑、做质检并交付视频。`

After the user replies with only `好呀` or similar:

- Bad: `收到，我会默认用本地流程、系统 TTS 和 ffmpeg 开始生成。`
- Good: `创意方向已确认。进入成片制作前，请先告诉我：生图/生视频、旁白、BGM/SFX、最终合成分别用哪些工具或模型？如果你想让我决定，请明确说“你来选”或“用默认”。`

## Intake Output Shape

Return:

- Product summary.
- Buyer hypothesis.
- Offer summary.
- Proof inventory.
- Claim boundaries.
- Asset inventory.
- Format: aspect ratio, duration, language, captions, and CTA.
- Assembly decision.
- Creative draft confirmation status.
- Production tool choices after confirmation: image, video, voiceover, BGM/SFX audio, assembly/rendering, and any access notes.
- Open questions.
