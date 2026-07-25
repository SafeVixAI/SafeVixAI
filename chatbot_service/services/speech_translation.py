# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from dataclasses import asdict, dataclass
from io import BytesIO
from typing import Any

from config import Settings


@dataclass(slots=True)
class SpeechTranslationResult:
    text: str
    target_language: str
    device: str
    model_source: str
    sample_rate: int


class IndicSeamlessService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._model = None
        self._processor = None
        self._tokenizer = None
        self._device = self._resolve_device()

    @property
    def model_source(self) -> str:
        model_dir = self.settings.speech_model_dir
        if model_dir and model_dir.exists():
            return str(model_dir)
        return self.settings.speech_model_id

    def _dependencies_available(self) -> bool:
        torch, torchaudio, _fe, _tok, _model_cls = self._import_dependencies()
        return all(dep is not None for dep in (torch, torchaudio, _fe, _tok, _model_cls))

    def status(self) -> dict[str, Any]:
        model_dir = self.settings.speech_model_dir
        return {
            'configured': bool(self.settings.speech_model_id or model_dir),
            'dependencies_available': self._dependencies_available(),
            'device': self._device,
            'model_source': self.model_source,
            'model_dir_exists': bool(model_dir and model_dir.exists()),
            'default_target_language': self.settings.speech_default_target_lang,
            'model_loaded': self._model is not None,
        }

    def translate_audio_bytes(
        self,
        audio_bytes: bytes,
        *,
        target_language: str | None = None,
    ) -> SpeechTranslationResult:
        if not audio_bytes:
            msg = 'Audio payload is empty'
            raise ValueError(msg)
        if len(audio_bytes) > 10_000_000:
            msg = 'Audio payload exceeds 10 MB limit'
            raise ValueError(msg)
        torch, torchaudio, _, _, _ = self._import_dependencies()
        if torch is None:
            msg = (
                'IndicSeamless dependencies are not installed. '
                'Install torch, torchaudio, transformers, and datasets in the chatbot_service environment.'
            )
            raise RuntimeError(
                msg
            )

        self._ensure_model_loaded()
        target_lang = (target_language or self.settings.speech_default_target_lang).lower()
        try:
            waveform, sample_rate = torchaudio.load(BytesIO(audio_bytes))
        except Exception as exc:
            msg = f"Failed to load audio: {exc}"
            raise RuntimeError(msg) from exc
        try:
            if waveform.ndim == 2 and waveform.shape[0] > 1:
                waveform = waveform.mean(dim=0, keepdim=True)
        except Exception as exc:
            msg = f"Failed to process audio channels: {exc}"
            raise RuntimeError(msg) from exc
        if sample_rate != 16_000:
            try:
                waveform = torchaudio.functional.resample(
                    waveform,
                    orig_freq=sample_rate,
                    new_freq=16_000,
                )
                sample_rate = 16_000
            except Exception as exc:
                msg = f"Failed to resample audio: {exc}"
                raise RuntimeError(msg) from exc

        try:
            audio_array = waveform.squeeze(0)
            inputs = self._processor(audio_array, sampling_rate=sample_rate, return_tensors='pt')
            inputs = {key: value.to(self._device) for key, value in inputs.items()}
        except Exception as exc:
            msg = f"Failed to prepare audio input: {exc}"
            raise RuntimeError(msg) from exc

        try:
            generated = self._model.generate(
                **inputs,
                tgt_lang=target_lang,
            )
        except Exception as exc:
            msg = f"Model inference failed: {exc}"
            raise RuntimeError(msg) from exc

        try:
            tokens = generated[0].detach().cpu().numpy().squeeze()
            text = self._tokenizer.decode(
                tokens,
                clean_up_tokenization_spaces=True,
                skip_special_tokens=True,
            ).strip()
        except Exception as exc:
            msg = f"Failed to decode model output: {exc}"
            raise RuntimeError(msg) from exc

        return SpeechTranslationResult(
            text=text,
            target_language=target_lang,
            device=self._device,
            model_source=self.model_source,
            sample_rate=sample_rate,
        )

    @staticmethod
    def _import_dependencies() -> tuple:
        try:
            import torch
            import torchaudio
            from transformers import (
                SeamlessM4TFeatureExtractor,
                SeamlessM4TTokenizer,
                SeamlessM4Tv2ForSpeechToText,
            )
            return (torch, torchaudio, SeamlessM4TFeatureExtractor, SeamlessM4TTokenizer, SeamlessM4Tv2ForSpeechToText)
        except ImportError:
            return (None, None, None, None, None)

    def _ensure_model_loaded(self) -> None:
        if self._model is not None and self._processor is not None and self._tokenizer is not None:
            return
        _, _, _fe, _tok, _model_cls = self._import_dependencies()
        if _model_cls is None:
            msg = 'IndicSeamless dependencies not available'
            raise RuntimeError(msg)
        model_source = self.model_source
        try:
            self._model = _model_cls.from_pretrained(model_source).to(self._device)
            self._processor = _fe.from_pretrained(model_source)
            self._tokenizer = _tok.from_pretrained(model_source)
        except Exception as exc:
            self._model = None
            self._processor = None
            self._tokenizer = None
            msg = f"Failed to load model from {model_source}: {exc}"
            raise RuntimeError(msg) from exc

    def _resolve_device(self) -> str:
        configured = (self.settings.speech_device or 'auto').lower()
        torch, _, _, _, _ = self._import_dependencies()
        if configured == 'auto':
            return 'cuda' if torch is not None and torch.cuda.is_available() else 'cpu'
        if configured == 'cuda' and (torch is None or not torch.cuda.is_available()):
            return 'cpu'
        return configured


def speech_result_to_dict(result: SpeechTranslationResult) -> dict[str, Any]:
    return asdict(result)
