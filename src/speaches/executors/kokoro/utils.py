from collections.abc import AsyncGenerator, Generator
import logging
from pathlib import Path
import time
from typing import Literal

import huggingface_hub
from kokoro_onnx import Kokoro
import numpy as np
from pydantic import BaseModel, computed_field

from speaches.api_types import Model
from speaches.audio import resample_audio
from speaches.hf_utils import (
    HfModelFilter,
    extract_language_list,
    get_cached_model_repos_info,
    get_model_card_data_from_cached_repo_info,
    list_model_files,
)
from speaches.model_registry import (
    ModelRegistry,
)

SAMPLE_RATE = 24000  # the default sample rate for Kokoro
LIBRARY_NAME = "onnx"
TASK_NAME_TAG = "text-to-speech"
TAGS = {"speaches", "kokoro"}


class KokoroModelFiles(BaseModel):
    model: Path
    voices: Path


class KokoroModelVoice(BaseModel):
    name: str
    language: str
    gender: Literal["male", "female"]

    @computed_field
    @property
    def id(self) -> str:
        return self.name


VOICES = [
    # American English
    KokoroModelVoice(name="af_heart", language="en-us", gender="female"),
    KokoroModelVoice(name="af_alloy", language="en-us", gender="female"),
    KokoroModelVoice(name="af_aoede", language="en-us", gender="female"),
    KokoroModelVoice(name="af_bella", language="en-us", gender="female"),
    KokoroModelVoice(name="af_jessica", language="en-us", gender="female"),
    KokoroModelVoice(name="af_kore", language="en-us", gender="female"),
    KokoroModelVoice(name="af_nicole", language="en-us", gender="female"),
    KokoroModelVoice(name="af_nova", language="en-us", gender="female"),
    KokoroModelVoice(name="af_river", language="en-us", gender="female"),
    KokoroModelVoice(name="af_sarah", language="en-us", gender="female"),
    KokoroModelVoice(name="af_sky", language="en-us", gender="female"),
    KokoroModelVoice(name="am_adam", language="en-us", gender="male"),
    KokoroModelVoice(name="am_echo", language="en-us", gender="male"),
    KokoroModelVoice(name="am_eric", language="en-us", gender="male"),
    KokoroModelVoice(name="am_fenrir", language="en-us", gender="male"),
    KokoroModelVoice(name="am_liam", language="en-us", gender="male"),
    KokoroModelVoice(name="am_michael", language="en-us", gender="male"),
    KokoroModelVoice(name="am_onyx", language="en-us", gender="male"),
    KokoroModelVoice(name="am_puck", language="en-us", gender="male"),
    KokoroModelVoice(name="am_santa", language="en-us", gender="male"),
    # British English
    KokoroModelVoice(name="bf_alice", language="en-gb", gender="female"),
    KokoroModelVoice(name="bf_emma", language="en-gb", gender="female"),
    KokoroModelVoice(name="bf_isabella", language="en-gb", gender="female"),
    KokoroModelVoice(name="bf_lily", language="en-gb", gender="female"),
    KokoroModelVoice(name="bm_daniel", language="en-gb", gender="male"),
    KokoroModelVoice(name="bm_fable", language="en-gb", gender="male"),
    KokoroModelVoice(name="bm_george", language="en-gb", gender="male"),
    KokoroModelVoice(name="bm_lewis", language="en-gb", gender="male"),
    # Japanese
    KokoroModelVoice(name="jf_alpha", language="ja", gender="female"),
    KokoroModelVoice(name="jf_gongitsune", language="ja", gender="female"),
    KokoroModelVoice(name="jf_nezumi", language="ja", gender="female"),
    KokoroModelVoice(name="jf_tebukuro", language="ja", gender="female"),
    KokoroModelVoice(name="jm_kumo", language="ja", gender="male"),
    # Mandarin Chinese
    KokoroModelVoice(name="zf_xiaobei", language="zh", gender="female"),
    KokoroModelVoice(name="zf_xiaoni", language="zh", gender="female"),
    KokoroModelVoice(name="zf_xiaoxiao", language="zh", gender="female"),
    KokoroModelVoice(name="zf_xiaoyi", language="zh", gender="female"),
    KokoroModelVoice(name="zm_yunjian", language="zh", gender="male"),
    KokoroModelVoice(name="zm_yunxi", language="zh", gender="male"),
    KokoroModelVoice(name="zm_yunxia", language="zh", gender="male"),
    KokoroModelVoice(name="zm_yunyang", language="zh", gender="male"),
    # Spanish
    KokoroModelVoice(name="ef_dora", language="es", gender="female"),
    KokoroModelVoice(name="em_alex", language="es", gender="male"),
    KokoroModelVoice(name="em_santa", language="es", gender="male"),
    # French
    KokoroModelVoice(name="ff_siwis", language="fr-fr", gender="female"),
    # Hindi
    KokoroModelVoice(name="hf_alpha", language="hi", gender="female"),
    KokoroModelVoice(name="hf_beta", language="hi", gender="female"),
    KokoroModelVoice(name="hm_omega", language="hi", gender="male"),
    KokoroModelVoice(name="hm_psi", language="hi", gender="male"),
    # Italian
    KokoroModelVoice(name="if_sara", language="it", gender="female"),
    KokoroModelVoice(name="im_nicola", language="it", gender="male"),
    # Brazilian Portuguese
    KokoroModelVoice(name="pf_dora", language="pt-br", gender="female"),
    KokoroModelVoice(name="pm_alex", language="pt-br", gender="male"),
    KokoroModelVoice(name="pm_santa", language="pt-br", gender="male"),
]


class KokoroModel(Model):
    sample_rate: int
    voices: list[KokoroModelVoice]


hf_model_filter = HfModelFilter(
    library_name=LIBRARY_NAME,
    task=TASK_NAME_TAG,
    tags=TAGS,
)


logger = logging.getLogger(__name__)


def normalize_language_code(lang_code: str) -> str:
    """
    将各种中文代码统一映射为 espeak 支持的标准代码
    
    Args:
        lang_code: 输入的语言代码
        
    Returns:
        标准化后的语言代码
    """
    chinese_codes = {
        "zh-cn": "zh",
        "zh-hans": "zh", 
        "zh-tw": "zh",
        "zh-hant": "zh",
        "cmn": "zh",
        "mandarin": "zh",
        "chinese": "zh"
    }
    return chinese_codes.get(lang_code.lower(), lang_code)


class KokoroModelRegistry(ModelRegistry):
    def list_remote_models(self) -> Generator[KokoroModel, None, None]:
        models = huggingface_hub.list_models(**self.hf_model_filter.list_model_kwargs(), cardData=True)
        for model in models:
            assert model.created_at is not None and model.card_data is not None, model
            yield KokoroModel(
                id=model.id,
                created=int(model.created_at.timestamp()),
                owned_by=model.id.split("/")[0],
                language=extract_language_list(model.card_data),
                task=TASK_NAME_TAG,
                sample_rate=SAMPLE_RATE,
                voices=VOICES,
            )

    def list_local_models(self) -> Generator[KokoroModel, None, None]:
        cached_model_repos_info = get_cached_model_repos_info()
        for cached_repo_info in cached_model_repos_info:
            model_card_data = get_model_card_data_from_cached_repo_info(cached_repo_info)
            if model_card_data is None:
                continue
            if self.hf_model_filter.passes_filter(model_card_data):
                yield KokoroModel(
                    id=cached_repo_info.repo_id,
                    created=int(cached_repo_info.last_modified),
                    owned_by=cached_repo_info.repo_id.split("/")[0],
                    language=extract_language_list(model_card_data),
                    task=TASK_NAME_TAG,
                    sample_rate=SAMPLE_RATE,
                    voices=VOICES,
                )

    def get_model_files(self, model_id: str) -> KokoroModelFiles:
        model_files = list(list_model_files(model_id))

        model_file_path = next(file_path for file_path in model_files if file_path.name == "model.onnx")
        voices_file_path = next(file_path for file_path in model_files if file_path.name == "voices.bin")

        return KokoroModelFiles(
            model=model_file_path,
            voices=voices_file_path,
        )

    def download_model_files(self, model_id: str) -> None:
        _model_repo_path_str = huggingface_hub.snapshot_download(
            repo_id=model_id, repo_type="model", allow_patterns=["model.onnx", "voices.bin", "README.md"]
        )


model_registry = KokoroModelRegistry(hf_model_filter=hf_model_filter)


async def generate_audio(
    kokoro_tts: Kokoro,
    text: str,
    voice: str,
    *,
    speed: float = 1.0,
    sample_rate: int | None = None,
) -> AsyncGenerator[bytes, None]:
    if sample_rate is None:
        sample_rate = SAMPLE_RATE
    
    # 修复纯中文文本问题：检测并自动添加标点
    # phonemizer 需要至少一个 ASCII 字符才能正确处理
    has_ascii = any(ord(char) < 128 for char in text)
    if not has_ascii and text.strip():
        # 如果是纯中文/非ASCII文本，自动在末尾添加句号
        text = text + "."
        logger.debug(f"Pure non-ASCII text detected, adding period for phonemizer compatibility")
    
    start = time.perf_counter()
    try:
        # 直接调用，不指定语言参数（因为 espeak 不支持我们的语言代码）
        async for audio_data, _ in kokoro_tts.create_stream(text, voice, speed=speed):
            assert isinstance(audio_data, np.ndarray) and audio_data.dtype == np.float32 and isinstance(sample_rate, int)
            normalized_audio_data = (audio_data * np.iinfo(np.int16).max).astype(np.int16)
            audio_bytes = normalized_audio_data.tobytes()
            if sample_rate != SAMPLE_RATE:
                audio_bytes = resample_audio(audio_bytes, SAMPLE_RATE, sample_rate)
            yield audio_bytes
    except Exception as e:
        logger.error(f"TTS failed: {e}")
        raise
    
    logger.info(f"Generated audio for {len(text)} characters in {time.perf_counter() - start}s")
