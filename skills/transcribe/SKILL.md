---
id: transcribe
name: "transcribe"
description: "Use this skill when a user asks to transcribe speech from audio/video, extract text from recordings, or label speakers in interviews or meetings."
category: OpenAI
author: openai
---


# Audio Transcribe

Transcribe audio using OpenAI or Atlas Cloud, with optional speaker diarization when requested. Prefer the bundled CLI for deterministic, repeatable runs. OpenAI remains the default provider.

## Workflow
1. Collect inputs: audio file path(s), desired response format (text/json/diarized_json), optional language hint, and any known speaker references.
2. Choose the provider. Use OpenAI by default, or Atlas Cloud when the user requests it. Verify the matching API key is set locally (do not ask the user to paste it).
3. Run the bundled `transcribe_diarize.py` CLI with sensible defaults (fast text transcription).
4. Validate the output: transcription quality, speaker labels, and segment boundaries; iterate with a single targeted change if needed.
5. Save outputs under `output/transcribe/` when working in this repo.

## Decision rules
- Default to `gpt-4o-mini-transcribe` with `--response-format text` for fast transcription.
- If the user wants speaker labels or diarization, use `--model gpt-4o-transcribe-diarize --response-format diarized_json`.
- If audio is longer than ~30 seconds, keep `--chunking-strategy auto`.
- Prompting is not supported for `gpt-4o-transcribe-diarize`.
- For Atlas Cloud, pass `--provider atlas`; the CLI uses `xai/stt-v1` and maps `diarized_json` to speaker diarization.
- Atlas Cloud does not support known-speaker hints or prompts in this CLI.

## Output conventions
- Use `output/transcribe/<job-id>/` for evaluation runs.
- Use `--out-dir` for multiple files to avoid overwriting.

## Dependencies (install if missing)
Prefer `uv` for dependency management.

```
uv pip install openai
```
If `uv` is unavailable:
```
python3 -m pip install openai
```

## Environment
- `OPENAI_API_KEY` must be set for live API calls.
- `ATLASCLOUD_API_KEY` must be set for Atlas Cloud calls.
- If the matching key is missing, instruct the user to create it in the provider UI and export it in their shell.
- Never ask the user to paste the full key in chat.

## Skill path (set once)

```bash
export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
export TRANSCRIBE_CLI="$CODEX_HOME/skills/transcribe/scripts/transcribe_diarize.py"
```

User-scoped skills install under `$CODEX_HOME/skills` (default: `~/.codex/skills`).

## CLI quick start
Single file (fast text default):
```
python3 "$TRANSCRIBE_CLI" \
  path/to/audio.wav \
  --out transcript.txt
```

Diarization with known speakers (up to 4):
```
python3 "$TRANSCRIBE_CLI" \
  meeting.m4a \
  --model gpt-4o-transcribe-diarize \
  --known-speaker "Alice=refs/alice.wav" \
  --known-speaker "Bob=refs/bob.wav" \
  --response-format diarized_json \
  --out-dir output/transcribe/meeting
```

Plain text output (explicit):
```
python3 "$TRANSCRIBE_CLI" \
  interview.mp3 \
  --response-format text \
  --out interview.txt
```

Atlas Cloud transcription:
```
python3 "$TRANSCRIBE_CLI" \
  meeting.m4a \
  --provider atlas \
  --response-format diarized_json \
  --out meeting.json
```

## Reference map
- `references/api.md`: supported formats, limits, response formats, and known-speaker notes.
