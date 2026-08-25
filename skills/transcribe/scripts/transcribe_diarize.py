#!/usr/bin/env python3
"""Transcribe audio (optionally with speaker diarization) using OpenAI."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_OPENAI_MODEL = "gpt-4o-mini-transcribe"
DEFAULT_ATLAS_MODEL = "xai/stt-v1"
DEFAULT_RESPONSE_FORMAT = "text"
DEFAULT_CHUNKING_STRATEGY = "auto"
MAX_OPENAI_AUDIO_BYTES = 25 * 1024 * 1024
MAX_ATLAS_AUDIO_BYTES = 500 * 1024 * 1024
MAX_KNOWN_SPEAKERS = 4
ATLAS_POLL_INTERVAL_SECONDS = 2.0
ATLAS_MAX_POLL_INTERVAL_SECONDS = 10.0
ATLAS_POLL_TIMEOUT_SECONDS = 300.0

ALLOWED_RESPONSE_FORMATS = {"text", "json", "diarized_json"}
ALLOWED_PROVIDERS = {"openai", "atlas"}


def _die(message: str, code: int = 1) -> None:
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(code)


def _warn(message: str) -> None:
    print(f"Warning: {message}", file=sys.stderr)


def _ensure_api_key(provider: str, dry_run: bool) -> None:
    env_name = "OPENAI_API_KEY" if provider == "openai" else "ATLASCLOUD_API_KEY"
    if os.getenv(env_name):
        print(f"{env_name} is set.", file=sys.stderr)
        return
    if dry_run:
        _warn(f"{env_name} is not set; dry-run only.")
        return
    _die(f"{env_name} is not set. Export it before running.")


def _normalize_response_format(value: Optional[str]) -> str:
    if not value:
        return DEFAULT_RESPONSE_FORMAT
    fmt = value.strip().lower()
    if fmt not in ALLOWED_RESPONSE_FORMATS:
        _die(
            "response-format must be one of: "
            + ", ".join(sorted(ALLOWED_RESPONSE_FORMATS))
        )
    return fmt


def _normalize_chunking_strategy(value: Optional[str]) -> Any:
    if not value:
        return DEFAULT_CHUNKING_STRATEGY
    raw = str(value).strip()
    if raw.startswith("{"):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            _die("chunking-strategy JSON is invalid")
    return raw


def _guess_mime_type(path: Path) -> str:
    mime, _ = mimetypes.guess_type(str(path))
    if mime:
        return mime
    return "audio/wav"


def _encode_data_url(path: Path) -> str:
    data = path.read_bytes()
    mime = _guess_mime_type(path)
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _parse_known_speakers(raw_items: List[str]) -> Tuple[List[str], List[str]]:
    names: List[str] = []
    refs: List[str] = []
    for raw in raw_items:
        if "=" not in raw:
            _die("known-speaker must be NAME=PATH")
        name, path_str = raw.split("=", 1)
        name = name.strip()
        path = Path(path_str.strip())
        if not name or not path_str.strip():
            _die("known-speaker must be NAME=PATH")
        if not path.exists():
            _die(f"Known speaker file not found: {path}")
        names.append(name)
        refs.append(_encode_data_url(path))
    if len(names) > MAX_KNOWN_SPEAKERS:
        _die(f"known speakers must be <= {MAX_KNOWN_SPEAKERS}")
    return names, refs


def _output_extension(response_format: str) -> str:
    return "txt" if response_format == "text" else "json"


def _build_output_path(
    audio_path: Path,
    response_format: str,
    out: Optional[str],
    out_dir: Optional[str],
) -> Path:
    ext = "." + _output_extension(response_format)
    if out:
        path = Path(out)
        if path.exists() and path.is_dir():
            return path / f"{audio_path.stem}.transcript{ext}"
        if path.suffix == "":
            return path.with_suffix(ext)
        return path
    if out_dir:
        base = Path(out_dir)
        base.mkdir(parents=True, exist_ok=True)
        return base / f"{audio_path.stem}.transcript{ext}"
    return Path(f"{audio_path.stem}.transcript{ext}")


def _create_openai_client():
    try:
        from openai import OpenAI
    except ImportError:
        _die("openai SDK not installed. Install with `uv pip install openai`.")
    return OpenAI()


def _format_output(result: Any, response_format: str) -> str:
    if response_format == "text":
        text = getattr(result, "text", None)
        return text if isinstance(text, str) else str(result)
    if hasattr(result, "model_dump"):
        return json.dumps(result.model_dump(), indent=2)
    if isinstance(result, (dict, list)):
        return json.dumps(result, indent=2)
    return json.dumps({"text": getattr(result, "text", str(result))}, indent=2)


def _validate_audio(path: Path, provider: str) -> None:
    if not path.exists():
        _die(f"Audio file not found: {path}")
    size = path.stat().st_size
    max_bytes = (
        MAX_OPENAI_AUDIO_BYTES if provider == "openai" else MAX_ATLAS_AUDIO_BYTES
    )
    if size > max_bytes:
        _warn(
            f"Audio file exceeds {max_bytes // (1024 * 1024)}MB limit "
            f"({size} bytes): {path}"
        )


def _build_openai_payload(
    args: argparse.Namespace,
    known_speaker_names: List[str],
    known_speaker_refs: List[str],
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "model": args.model,
        "response_format": args.response_format,
        "chunking_strategy": args.chunking_strategy,
    }
    if args.language:
        payload["language"] = args.language
    if args.prompt:
        payload["prompt"] = args.prompt
    if known_speaker_names:
        payload["extra_body"] = {
            "known_speaker_names": known_speaker_names,
            "known_speaker_references": known_speaker_refs,
        }
    return payload


def _build_atlas_payload(
    args: argparse.Namespace,
    audio_path: Path,
    encode_audio: bool = True,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "model": args.model,
        "audio": (
            base64.b64encode(audio_path.read_bytes()).decode("ascii")
            if encode_audio
            else "<base64 audio omitted>"
        ),
    }
    if args.language:
        payload["language"] = args.language
    if args.response_format == "diarized_json":
        payload["diarize"] = True
    return payload


def _run_openai_one(
    client: Any,
    audio_path: Path,
    payload: Dict[str, Any],
) -> Any:
    with audio_path.open("rb") as audio_file:
        return client.audio.transcriptions.create(
            file=audio_file,
            **payload,
        )


def _atlas_json_request(
    url: str,
    method: str,
    api_key: str,
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        url,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Atlas API HTTP {exc.code}: {detail}") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"Atlas API request failed: {exc}") from exc
    if not isinstance(result, dict):
        raise RuntimeError("Atlas API returned a non-object response")
    if result.get("code") not in (None, 0, 200):
        raise RuntimeError(
            f"Atlas API error {result.get('code')}: {result.get('message', '')}"
        )
    return result


def _atlas_data(response: Dict[str, Any]) -> Dict[str, Any]:
    data = response.get("data", response)
    if not isinstance(data, dict):
        raise RuntimeError("Atlas API response is missing prediction data")
    return data


def _run_atlas_one(
    payload: Dict[str, Any],
    api_key: str,
    base_url: str,
    request_json: Any = _atlas_json_request,
    sleep: Any = time.sleep,
    monotonic: Any = time.monotonic,
) -> Dict[str, Any]:
    # Submit exactly once. Only the idempotent prediction GET is polled.
    response = request_json(
        f"{base_url}/api/v1/model/generateAudio",
        "POST",
        api_key,
        payload,
    )
    prediction = _atlas_data(response)
    status = str(prediction.get("status", "")).lower()
    if status == "completed":
        return prediction
    if status in {"failed", "timeout"}:
        raise RuntimeError(
            f"Atlas transcription {status}: {prediction.get('error', '')}"
        )

    prediction_id = prediction.get("id")
    if not prediction_id:
        raise RuntimeError("Atlas API response is missing prediction id")
    prediction_url = f"{base_url}/api/v1/model/prediction/{prediction_id}"
    deadline = monotonic() + ATLAS_POLL_TIMEOUT_SECONDS
    poll_interval = ATLAS_POLL_INTERVAL_SECONDS

    while monotonic() < deadline:
        sleep(poll_interval)
        prediction = _atlas_data(
            request_json(prediction_url, "GET", api_key, None)
        )
        status = str(prediction.get("status", "")).lower()
        if status == "completed":
            return prediction
        if status in {"failed", "timeout"}:
            raise RuntimeError(
                f"Atlas transcription {status}: {prediction.get('error', '')}"
            )
        poll_interval = min(poll_interval * 2, ATLAS_MAX_POLL_INTERVAL_SECONDS)

    raise RuntimeError("Atlas transcription timed out after 300 seconds")


def _format_atlas_output(result: Dict[str, Any], response_format: str) -> str:
    transcription = result.get("stt_result")
    if response_format == "text":
        if isinstance(transcription, dict) and isinstance(transcription.get("text"), str):
            return transcription["text"]
        raise RuntimeError("Atlas response is missing transcript text")
    value = transcription if isinstance(transcription, dict) else result
    return json.dumps(value, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Transcribe audio with OpenAI or Atlas Cloud."
    )
    parser.add_argument("audio", nargs="+", help="Audio file(s) to transcribe")
    parser.add_argument(
        "--provider",
        choices=sorted(ALLOWED_PROVIDERS),
        default="openai",
        help="Transcription provider (default: openai)",
    )
    parser.add_argument(
        "--model",
        help="Model to use (defaults to the provider's recommended model)",
    )
    parser.add_argument(
        "--response-format",
        default=DEFAULT_RESPONSE_FORMAT,
        help="Response format: text, json, or diarized_json",
    )
    parser.add_argument(
        "--chunking-strategy",
        default=DEFAULT_CHUNKING_STRATEGY,
        help="Chunking strategy (use 'auto' for long audio)",
    )
    parser.add_argument("--language", help="Optional language hint (e.g. 'en')")
    parser.add_argument("--prompt", help="Optional prompt to guide transcription")
    parser.add_argument(
        "--known-speaker",
        action="append",
        default=[],
        help="Known speaker reference as NAME=PATH (repeatable, max 4)",
    )
    parser.add_argument("--out", help="Output file path (single audio only)")
    parser.add_argument("--out-dir", help="Output directory for transcripts")
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Write transcript to stdout instead of a file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs and print payload without calling the API",
    )

    args = parser.parse_args()
    args.model = args.model or (
        DEFAULT_OPENAI_MODEL if args.provider == "openai" else DEFAULT_ATLAS_MODEL
    )
    args.response_format = _normalize_response_format(args.response_format)
    args.chunking_strategy = _normalize_chunking_strategy(args.chunking_strategy)

    if args.out and len(args.audio) > 1:
        _die("--out only supports a single audio file")
    if args.stdout and (args.out or args.out_dir):
        _die("--stdout cannot be combined with --out or --out-dir")
    if args.stdout and len(args.audio) > 1:
        _die("--stdout only supports a single audio file")

    if args.provider == "openai":
        if args.prompt and "transcribe-diarize" in args.model:
            _die("prompt is not supported with gpt-4o-transcribe-diarize")
        if (
            args.response_format == "diarized_json"
            and "transcribe-diarize" not in args.model
        ):
            _die("diarized_json requires gpt-4o-transcribe-diarize")
    else:
        if args.model != DEFAULT_ATLAS_MODEL:
            _die(f"Atlas provider currently supports model {DEFAULT_ATLAS_MODEL}")
        if args.prompt:
            _die("prompt is not supported by the Atlas transcription provider")
        if args.known_speaker:
            _die("known-speaker is not supported by the Atlas transcription provider")

    _ensure_api_key(args.provider, args.dry_run)

    audio_paths = [Path(p) for p in args.audio]
    for path in audio_paths:
        _validate_audio(path, args.provider)

    known_names: List[str] = []
    known_refs: List[str] = []
    if args.provider == "openai":
        known_names, known_refs = _parse_known_speakers(args.known_speaker)
        if known_names and "transcribe-diarize" not in args.model:
            _warn(
                "known-speaker references are only supported for "
                "gpt-4o-transcribe-diarize"
            )

    if args.dry_run:
        payload = (
            _build_openai_payload(args, known_names, known_refs)
            if args.provider == "openai"
            else _build_atlas_payload(args, audio_paths[0], encode_audio=False)
        )
        print(json.dumps(payload, indent=2))
        return

    openai_client = _create_openai_client() if args.provider == "openai" else None
    atlas_api_key = os.getenv("ATLASCLOUD_API_KEY", "")
    atlas_base_url = os.getenv("ATLASCLOUD_BASE_URL", "https://api.atlascloud.ai").rstrip(
        "/"
    )

    for path in audio_paths:
        if args.provider == "openai":
            payload = _build_openai_payload(args, known_names, known_refs)
            result = _run_openai_one(openai_client, path, payload)
            output = _format_output(result, args.response_format)
        else:
            payload = _build_atlas_payload(args, path)
            try:
                result = _run_atlas_one(
                    payload,
                    atlas_api_key,
                    atlas_base_url,
                )
                output = _format_atlas_output(result, args.response_format)
            except RuntimeError as exc:
                _die(str(exc))
        if args.stdout:
            print(output)
            continue
        out_path = _build_output_path(path, args.response_format, args.out, args.out_dir)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding="utf-8")
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
