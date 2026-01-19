#!/usr/bin/env python3
"""
Configuration for Medical Translation Pipeline
Back Translation Project - Stanford Clinical Translation Evaluation Framework
"""

import os
import logging
from pathlib import Path

# =============================================================================
# PATHS
# =============================================================================

BASE_DIR = Path("/Users/chukanya/Library/Mobile Documents/com~apple~CloudDocs/Coding/Back translation project")
TRANSLATIONS_DIR = BASE_DIR / "output" / "medlineplus_results"
METRICS_DIR = BASE_DIR / "output" / "medlineplus_metrics"

# Create directories if they don't exist
TRANSLATIONS_DIR.mkdir(parents=True, exist_ok=True)
METRICS_DIR.mkdir(parents=True, exist_ok=True)

# =============================================================================
# API KEYS - Use environment variables
# =============================================================================

API_KEYS = {
    "openai": os.getenv("OPENAI_API_KEY", ""),
    "anthropic": os.getenv("ANTHROPIC_API_KEY", ""),
    "google": os.getenv("GOOGLE_API_KEY", ""),
    "moonshot": os.getenv("MOONSHOT_API_KEY", ""),
}

# =============================================================================
# MODEL CONFIGURATIONS - Exact model IDs used for the 704 translations
# =============================================================================

MODELS = {
    "gpt-5.1": {
        "provider": "openai",
        "model_id": "gpt-5.1",
        "max_tokens": 4096,
        "temperature": 0.3,
    },
    "claude-opus-4.5": {
        "provider": "anthropic",
        "model_id": "claude-opus-4-5-20251101",
        "max_tokens": 4096,
        "temperature": 0.3,
    },
    "gemini-3-pro": {
        "provider": "google",
        "model_id": "gemini-3-pro-preview",
        "max_tokens": 16384,
        "temperature": 0.3,
    },
    "kimi-k2": {
        "provider": "moonshot",
        "model_id": "kimi-k2-thinking",
        "max_tokens": 32768,
        "temperature": 0.3,
    },
}

ACTIVE_MODELS = [
    "gpt-5.1",
    "claude-opus-4.5",
    "gemini-3-pro",
    "kimi-k2"
]

# =============================================================================
# LANGUAGES
# =============================================================================

LANGUAGES = {
    "spanish": {
        "code": "es",
        "name": "Spanish",
        "script": "Latin",
        "resource_level": "high",
    },
    "chinese_simplified": {
        "code": "zh-CN",
        "name": "Chinese (Simplified)",
        "script": "Non-Latin",
        "resource_level": "high",
    },
    "vietnamese": {
        "code": "vi",
        "name": "Vietnamese",
        "script": "Latin (diacritics)",
        "resource_level": "medium",
    },
    "russian": {
        "code": "ru",
        "name": "Russian",
        "script": "Cyrillic",
        "resource_level": "high",
    },
    "arabic": {
        "code": "ar",
        "name": "Arabic",
        "script": "Non-Latin (RTL)",
        "resource_level": "medium",
    },
    "korean": {
        "code": "ko",
        "name": "Korean",
        "script": "Non-Latin",
        "resource_level": "high",
    },
    "tagalog": {
        "code": "tl",
        "name": "Tagalog/Filipino",
        "script": "Latin",
        "resource_level": "low",
    },
    "haitian_creole": {
        "code": "ht",
        "name": "Haitian Creole",
        "script": "Latin",
        "resource_level": "low",
    },
}

ACTIVE_LANGUAGES = list(LANGUAGES.keys())

# =============================================================================
# PROMPT TEMPLATES - Exact prompts used for the 704 translations
# =============================================================================

TRANSLATION_SYSTEM_PROMPT = """You are an expert medical translator specializing in patient education materials.
Your translations must:
1. Preserve ALL medical terminology accurately
2. Maintain patient-friendly readability (aim for 6th-8th grade reading level)
3. Be culturally appropriate for the target language speakers
4. Keep ALL safety warnings and critical information intact
5. Preserve document structure (headings, bullet points, numbered lists)

CRITICAL: Never omit, modify, or soften any medical warnings or safety information."""

TRANSLATION_USER_PROMPT = """Translate the following patient education document from English to {target_language}.

Requirements:
- Maintain exact document structure and formatting
- Preserve all medical terms accurately (use commonly understood equivalents when available)
- Keep all numbered lists, bullet points, and section headers
- Do not add explanations or commentary
- Do not remove any content

Document to translate:
---
{document_text}
---

Provide only the {target_language} translation, nothing else."""

BACK_TRANSLATION_SYSTEM_PROMPT = """You are a professional medical translator. Your task is to translate text back to English.

CRITICAL INSTRUCTIONS:
1. Translate EXACTLY what is written - do not correct perceived errors
2. Preserve the meaning and structure as closely as possible
3. If something seems unclear or wrong in the source, translate it literally anyway
4. Do not add any explanations or notes about the translation"""

BACK_TRANSLATION_USER_PROMPT = """Translate the following {source_language} medical text back to English.

Important: Translate literally and exactly. Do not correct any errors you perceive -
we need to see exactly what the text says.

Text to translate:
---
{translated_text}
---

Provide only the English translation, nothing else."""

# =============================================================================
# EXECUTION SETTINGS
# =============================================================================

EXECUTION_CONFIG = {
    "batch_size": 5,
    "retry_attempts": 3,
    "retry_delay": 5,
    "rate_limit_delay": 1,
    "save_intermediate": True,
    "parallel_models": False,
}

# =============================================================================
# LOGGING
# =============================================================================

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger("BackTranslation")
