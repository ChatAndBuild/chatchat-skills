# gpt-4o-transcribe-diarize quick reference

- Input formats: mp3, mp4, mpeg, mpga, m4a, wav, webm.
- Max file size: 25 MB per request.
- response_format options: text, json, diarized_json.
- For audio longer than ~30 seconds, pass chunking_strategy (use "auto" to split into chunks).
- Known speakers: up to 4 references via extra_body known_speaker_names + known_speaker_references (data URLs).
- Prompting is not supported for gpt-4o-transcribe-diarize.

# Atlas Cloud xai/stt-v1 quick reference

- Set `ATLASCLOUD_API_KEY` and pass `--provider atlas`.
- Input may be a URL or Base64 audio; the bundled CLI uses Base64 for local files.
- Container formats are auto-detected and support files up to 500 MB.
- `diarized_json` enables speaker diarization and returns word timestamps with speaker IDs.
- Known-speaker references and prompts are not supported by this provider path.
- Submission is attempted once; prediction status is polled with bounded GET requests.
