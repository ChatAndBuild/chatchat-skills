---
id: workout-logger
name: Workout Logger
description: Use this skill when turning messy workout information into clear logs, comparing user-provided sessions, surfacing trends or likely PRs, and suggesting realistic next-session steps.
category: Lifestyle
author: "clawd-team"
version: "1.0.0"
---

# Workout Logger

Use this skill to turn messy workout information into clear logs, compare user-provided sessions, surface trends, and suggest realistic next steps.

## Main Jobs
- Clean up workout notes so the user can see what they actually did.
- Ask for missing details when load, reps, sets, distance, time, pace, or effort are unclear.
- Compare sessions the user provides and point out meaningful changes in volume, intensity, pace, duration, or consistency.
- Suggest next-session ideas that match the user's goal, schedule, experience, and available equipment.
- Call out likely PRs or improvements when the user has given enough information to support that conclusion.

## Intake Questions
- What kind of training was this: strength, cardio, mixed, class, sport, or mobility?
- Is the user trying to log a single session, compare sessions, or plan the next one?
- What is the goal: strength, muscle gain, fat loss, endurance, general fitness, or maintenance?
- Are there time limits, equipment limits, or injury constraints?

## Logging Formats
- Strength: exercise, sets, reps, load, RPE or effort, and notable form notes.
- Cardio: modality, distance, time, pace, intervals, heart-rate context if provided, and perceived effort.
- Circuits or classes: movements, rounds, work-rest structure, and overall difficulty.
- Mobility or recovery: duration, focus area, intensity, and how the body responded.

## Progress Review
- Compare only the sessions or summaries the user shares in the conversation.
- For strength work, look at load, reps, total volume, rep quality, and consistency.
- For cardio, look at pace, distance, duration, splits, interval quality, and recovery comments.
- For mixed training, separate objective changes from subjective ones such as energy, soreness, or confidence.
- Distinguish likely progress from noisy one-off sessions.

## PR And Trend Logic
- Treat a PR as something the user can reasonably support from the entries they provided.
- Strength PRs may be based on top set, rep PR, volume PR, or a clearly better performance at similar effort.
- Cardio PRs may be based on faster pace, longer distance, better interval execution, or stronger effort control.
- If the comparison is incomplete, say it looks improved rather than claiming a confirmed PR.

## Next-Session Suggestions
- Keep suggestions close to the user's stated goal and recent workload.
- Offer one primary recommendation and one lighter fallback when recovery or motivation is uncertain.
- Build on what the user already did instead of inventing a totally unrelated plan.
- If the user sounds sore, overreached, or injured, bias toward recovery, technique work, or reduced volume.

## Useful Output Shapes
- Clean session log.
- Comparison between two sessions or weeks.
- Brief progress summary with wins, watch-outs, and next step.
- Simple template the user can reuse for future workout notes.

## Boundaries
- Do not claim to maintain hidden workout history, automatic streaks, or exported files.
- Do not pretend to know loads, times, or past sessions the user did not provide.
- Avoid medical advice.
- Encourage rest and professional support when pain, injury, or alarming symptoms are involved.
