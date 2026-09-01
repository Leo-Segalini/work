"""Provider local Qwen3-0.6B (± LoRA) pour DiagOps M0 / M1."""

from __future__ import annotations

import logging
import os
import time
from typing import Any

from app.model_client import (
    ModelConfigError,
    ModelUpstreamError,
    _extract_json,
    normalize_payload,
)
from app.schemas import DiagnoseRequest, DiagnoseResponse

logger = logging.getLogger(__name__)

DEFAULT_LOCAL_MODEL = "Qwen/Qwen3-0.6B"
DEFAULT_REVISION = "c1899de289a04d12100db370d81485cdf75e47ca"

_provider_cache: dict[str, Any] = {}


def _build_input_text(request: DiagnoseRequest) -> str:
    parts: list[str] = []
    if request.equipment_id:
        parts.append(f"Equipement: {request.equipment_id}")
    parts.append(request.technician_note)
    return "\n".join(parts)


def _resolve_device_and_dtype(torch: Any, requested: str) -> tuple[Any, str]:
    if torch.cuda.is_available():
        device = torch.device("cuda")
        dtype_name = requested
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = torch.device("mps")
        dtype_name = "float16" if requested == "bfloat16" else requested
    else:
        device = torch.device("cpu")
        dtype_name = "float32"
    return device, dtype_name


def _resolve_dtype(torch: Any, name: str) -> Any:
    mapping = {
        "bfloat16": torch.bfloat16,
        "float16": torch.float16,
        "float32": torch.float32,
    }
    if name not in mapping:
        raise ModelConfigError(f"dtype non supporté: {name}")
    return mapping[name]


def get_local_provider(*, with_adapter: bool) -> Any:
    """Charge (une fois) le modèle local, avec ou sans adaptateur LoRA."""
    adapter_path = os.getenv("LORA_ADAPTER_PATH", "").strip() or None
    if with_adapter and not adapter_path:
        raise ModelConfigError(
            "LORA_ADAPTER_PATH manquant pour MODEL_PROVIDER=local_lora"
        )

    cache_key = f"{'lora' if with_adapter else 'base'}:{adapter_path or '-'}"
    if cache_key in _provider_cache:
        return _provider_cache[cache_key]

    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise ModelConfigError(
            "dépendances locales absentes (torch/transformers) : "
            "installer l'environnement M1 ou les libs locales"
        ) from exc

    model_id = os.getenv("LOCAL_MODEL_ID", DEFAULT_LOCAL_MODEL).strip()
    revision = os.getenv("LOCAL_MODEL_REVISION", DEFAULT_REVISION).strip()
    requested_dtype = os.getenv("LOCAL_MODEL_DTYPE", "bfloat16").strip()

    try:
        device, dtype_name = _resolve_device_and_dtype(torch, requested_dtype)
        dtype = _resolve_dtype(torch, dtype_name)
        tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            revision=revision,
            trust_remote_code=False,
        )
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token = tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            revision=revision,
            torch_dtype=dtype,
            trust_remote_code=False,
        )
        if with_adapter:
            from peft import PeftModel

            model = PeftModel.from_pretrained(model, adapter_path)

        model.to(device)
        model.eval()
    except ModelConfigError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("échec chargement modèle local")
        raise ModelConfigError(f"échec chargement modèle local: {exc}") from exc

    provider = {
        "tokenizer": tokenizer,
        "model": model,
        "device": device,
        "torch": torch,
    }
    _provider_cache[cache_key] = provider
    logger.info(
        "modèle local chargé key=%s device=%s dtype=%s",
        cache_key,
        device,
        dtype_name,
    )
    return provider


def _apply_chat_template(tokenizer: Any, messages: list[dict[str, str]]) -> str:
    kwargs = {"tokenize": False, "add_generation_prompt": True}
    try:
        return tokenizer.apply_chat_template(
            messages, enable_thinking=False, **kwargs
        )
    except TypeError:
        return tokenizer.apply_chat_template(messages, **kwargs)


def diagnose_local(request: DiagnoseRequest, *, with_adapter: bool) -> DiagnoseResponse:
    """Génère un diagnostic via Qwen3 local (± LoRA)."""
    provider = get_local_provider(with_adapter=with_adapter)
    tokenizer = provider["tokenizer"]
    model = provider["model"]
    device = provider["device"]
    torch = provider["torch"]

    system = (
        "Vous etes DiagOps, un assistant de maintenance industrielle. "
        "Transformez le rapport technicien en un unique objet JSON conforme au contrat. "
        "N'ajoutez aucun texte avant ou apres le JSON."
    )
    user = (
        "Analysez le rapport suivant et retournez le diagnostic JSON.\n\n"
        f"Identifiant du rapport: {request.report_id}\n"
        f"Rapport:\n{_build_input_text(request)}"
    )
    prompt = _apply_chat_template(
        tokenizer,
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    started = time.perf_counter()
    try:
        with torch.inference_mode():
            outputs = model.generate(
                **inputs,
                max_new_tokens=256,
                do_sample=False,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
    except Exception as exc:  # noqa: BLE001
        logger.exception("échec inférence locale")
        raise ModelUpstreamError(f"échec inférence locale: {exc}") from exc

    prompt_length = inputs["input_ids"].shape[1]
    text = tokenizer.decode(outputs[0][prompt_length:], skip_special_tokens=True)
    elapsed = time.perf_counter() - started
    logger.info(
        "inférence locale ok report_id=%s duration_ms=%.1f",
        request.report_id,
        elapsed * 1000,
    )
    raw = _extract_json(text)
    return normalize_payload(raw, request)
