"""Xiaomi MiMo TTS/ASR provider plugin for Hermes Agent."""
from __future__ import annotations

import base64
import logging
import os
from typing import Any, Dict, Iterator, List, Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None  # type: ignore[misc,assignment]

from agent.tts_provider import TTSProvider

logger = logging.getLogger(__name__)

_DEFAULT_BASE_URL = "https://api.xiaomimimo.com/v1"


class _CompatOpenAIClient:
    """Use the standard OpenAI SDK pointing at MiMo's chat-completions endpoint."""

    def __init__(self, base_url: str, api_key: Optional[str]) -> None:
        if OpenAI is None:
            raise RuntimeError("openai package is required: pip install openai")
        self._client = OpenAI(base_url=base_url, api_key=api_key or "")

    def tts(self, text: str, *, model: str, voice: str) -> bytes:
        completion = self._client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": ""},
                {"role": "assistant", "content": text},
            ],
            extra_body={
                "audio": {
                    "format": "wav",
                    "voice": voice,
                }
            },
        )
        message = getattr(completion.choices[0], "message", None)
        audio_attr = getattr(message, "audio", None)
        data: Optional[str] = getattr(audio_attr, "data", None)
        if not data:
            raise RuntimeError("MiMo TTS response did not include audio data")
        return base64.b64decode(data)


class XiaomiMimoTTSProvider(TTSProvider):
    """TTS provider for Xiaomi MiMo-V2.5 series.

    Uses the OpenAI-compatible ``/v1/chat/completions`` endpoint with the
    MiMo TTS audio generation extension and writes the resulting WAV bytes
    back to ``output_path``.
    """

    @property
    def name(self) -> str:
        return "xiaomi-mimo"

    @property
    def voice_compatible(self) -> bool:
        return False

    def __init__(self) -> None:
        self._base_url = os.getenv("MIMO_BASE_URL", _DEFAULT_BASE_URL).rstrip("/")
        self._api_key = self._resolve_api_key()

    def _resolve_api_key(self) -> Optional[str]:
        return os.getenv("MIMO_API_KEY")

    def is_available(self) -> bool:
        if OpenAI is None:
            return False
        return bool(self._api_key)

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "Xiaomi MiMo",
            "badge": "free tier",
            "tag": "MiMo-V2.5 TTS/ASR (OpenAI-compatible)",
            "env_vars": [
                {
                    "key": "MIMO_API_KEY",
                    "prompt": "MiMo API key",
                    "url": "https://mimo.mi.com/console",
                },
                {
                    "key": "MIMO_BASE_URL",
                    "prompt": "MiMo base URL",
                    "default": _DEFAULT_BASE_URL,
                },
            ],
        }

    def list_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": "mimo-v2.5-tts",
                "display": "MiMo-V2.5-TTS",
                "languages": ["zh-CN", "en"],
            },
            {
                "id": "mimo-v2.5-tts-voicedesign",
                "display": "MiMo-V2.5-TTS VoiceDesign",
                "languages": ["zh-CN", "en"],
            },
            {
                "id": "mimo-v2.5-tts-voiceclone",
                "display": "MiMo-V2.5-TTS VoiceClone",
                "languages": ["zh-CN", "en"],
            },
        ]

    def default_model(self) -> str:
        return "mimo-v2.5-tts"

    def default_voice(self) -> str:
        return "冰糖"

    def list_voices(self) -> List[Dict[str, Any]]:
        return [
            {"id": "冰糖", "display": "冰糖", "language": "zh-CN", "gender": "female"},
            {"id": "茉莉", "display": "茉莉", "language": "zh-CN", "gender": "female"},
            {"id": "苏打", "display": "苏打", "language": "zh-CN", "gender": "male"},
            {"id": "白桦", "display": "白桦", "language": "zh-CN", "gender": "male"},
            {"id": "mimo_default", "display": "MiMo-默认", "language": "zh-CN", "gender": "female"},
            {"id": "Mia", "display": "Mia", "language": "en", "gender": "female"},
            {"id": "Chloe", "display": "Chloe", "language": "en", "gender": "female"},
            {"id": "Milo", "display": "Milo", "language": "en", "gender": "male"},
            {"id": "Dean", "display": "Dean", "language": "en", "gender": "male"},
        ]

    def synthesize(
        self,
        text: str,
        output_path: str,
        *,
        voice: Optional[str] = None,
        model: Optional[str] = None,
        speed: Optional[float] = None,
        format: str = "mp3",
        **extra: Any,
    ) -> str:
        chosen_model = model or self.default_model()
        chosen_voice = (voice or self.default_voice()).strip() or self.default_voice()
        client = _CompatOpenAIClient(self._base_url, self._api_key)
        try:
            payload = client.tts(text, model=chosen_model, voice=chosen_voice)
        except Exception as exc:
            logger.exception("MiMo TTS synthesis failed")
            raise RuntimeError(f"MiMo TTS failed: {exc}") from exc

        fmt = (format or "mp3").lower()
        if fmt not in {"mp3", "wav", "ogg", "opus", "flac"}:
            fmt = "mp3"
        out_path = output_path if output_path.endswith(f".{fmt}") else f"{output_path}.{fmt}"
        with open(out_path, "wb") as fh:
            fh.write(payload)
        return out_path

    def stream(
        self,
        text: str,
        *,
        voice: Optional[str] = None,
        model: Optional[str] = None,
        format: str = "opus",
        **extra: Any,
    ) -> Iterator[bytes]:
        raise NotImplementedError("MiMo streaming synthesis is not implemented yet")
