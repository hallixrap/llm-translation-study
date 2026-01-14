"""
Back Translation Project - Translation Pipeline
Stanford Clinical Translation Evaluation Framework

This module handles all translation operations across different LLM providers.
Supports: OpenAI (GPT-5.1), Anthropic (Claude Sonnet 4.5), Google (Gemini 2.5), Moonshot (Kimi K2)
"""

import time
import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional
import traceback

# API clients - will be initialized when needed
openai_client = None
anthropic_client = None
genai = None
moonshot_client = None
hf_client = None

from config import (
    API_KEYS, MODELS, ACTIVE_MODELS, LANGUAGES, ACTIVE_LANGUAGES,
    TRANSLATION_SYSTEM_PROMPT, TRANSLATION_USER_PROMPT,
    BACK_TRANSLATION_SYSTEM_PROMPT, BACK_TRANSLATION_USER_PROMPT,
    EXECUTION_CONFIG, TRANSLATIONS_DIR, logger
)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class TranslationResult:
    """Stores the result of a translation operation."""
    doc_id: str
    model: str
    source_language: str
    target_language: str
    original_text: str
    translated_text: str
    back_translated_text: Optional[str]
    timestamp: str
    translation_time_seconds: float
    back_translation_time_seconds: Optional[float]
    success: bool
    error_message: Optional[str] = None

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


# =============================================================================
# API CLIENT INITIALIZATION
# =============================================================================

def init_openai():
    """Initialize OpenAI client."""
    global openai_client
    if openai_client is None:
        try:
            from openai import OpenAI
            openai_client = OpenAI(api_key=API_KEYS["openai"])
            logger.info("OpenAI client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
    return openai_client


def init_anthropic():
    """Initialize Anthropic client."""
    global anthropic_client
    if anthropic_client is None:
        try:
            import anthropic
            anthropic_client = anthropic.Anthropic(api_key=API_KEYS["anthropic"])
            logger.info("Anthropic client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            raise
    return anthropic_client


def init_google():
    """Initialize Google Generative AI client."""
    global genai
    if genai is None:
        try:
            import google.generativeai as google_genai
            google_genai.configure(api_key=API_KEYS["google"])
            genai = google_genai
            logger.info("Google AI client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Google AI client: {e}")
            raise
    return genai


def init_moonshot():
    """Initialize Moonshot (Kimi K2) client.

    Kimi K2 uses an OpenAI-compatible API endpoint.
    Get your API key from: https://platform.moonshot.ai/

    Note: Kimi K2 thinking model can take 60-90 minutes for long documents,
    so we set a very long timeout (2 hours).
    """
    global moonshot_client
    if moonshot_client is None:
        try:
            from openai import OpenAI
            import httpx
            # Kimi K2 thinking model is VERY slow - can take 60-90 min for long docs
            # Set timeout to 2 hours to avoid premature timeouts
            moonshot_client = OpenAI(
                api_key=API_KEYS["moonshot"],
                base_url="https://api.moonshot.ai/v1",  # Moonshot API endpoint (international)
                timeout=httpx.Timeout(7200.0, connect=60.0)  # 2 hour read timeout, 60s connect
            )
            logger.info("Moonshot (Kimi K2) client initialized with 2-hour timeout")
        except Exception as e:
            logger.error(f"Failed to initialize Moonshot client: {e}")
            raise
    return moonshot_client


def init_huggingface():
    """Initialize Hugging Face Inference Client.

    Uses the OpenAI-compatible HuggingFace Router endpoint.
    Get your token from: https://huggingface.co/settings/tokens
    Base URL: https://router.huggingface.co/v1
    """
    global hf_client
    if hf_client is None:
        try:
            from openai import OpenAI
            hf_client = OpenAI(
                api_key=API_KEYS["huggingface"],
                base_url="https://router.huggingface.co/v1"  # HuggingFace OpenAI-compatible endpoint
            )
            logger.info("Hugging Face Inference client initialized (OpenAI-compatible)")
        except Exception as e:
            logger.error(f"Failed to initialize Hugging Face client: {e}")
            raise
    return hf_client


# =============================================================================
# TRANSLATION FUNCTIONS BY PROVIDER
# =============================================================================

def translate_with_openai(
    text: str,
    target_language: str,
    model_config: dict,
    is_back_translation: bool = False,
    source_language: str = "English"
) -> str:
    """Translate text using OpenAI models."""
    client = init_openai()

    if is_back_translation:
        system_prompt = BACK_TRANSLATION_SYSTEM_PROMPT
        user_prompt = BACK_TRANSLATION_USER_PROMPT.format(
            source_language=source_language,
            translated_text=text
        )
    else:
        system_prompt = TRANSLATION_SYSTEM_PROMPT
        user_prompt = TRANSLATION_USER_PROMPT.format(
            target_language=target_language,
            document_text=text
        )

    # GPT-5.1+ uses max_completion_tokens instead of max_tokens
    response = client.chat.completions.create(
        model=model_config["model_id"],
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_completion_tokens=model_config["max_tokens"],
        temperature=model_config["temperature"]
    )

    return response.choices[0].message.content.strip()


def translate_with_anthropic(
    text: str,
    target_language: str,
    model_config: dict,
    is_back_translation: bool = False,
    source_language: str = "English"
) -> str:
    """Translate text using Anthropic Claude models."""
    client = init_anthropic()

    if is_back_translation:
        system_prompt = BACK_TRANSLATION_SYSTEM_PROMPT
        user_prompt = BACK_TRANSLATION_USER_PROMPT.format(
            source_language=source_language,
            translated_text=text
        )
    else:
        system_prompt = TRANSLATION_SYSTEM_PROMPT
        user_prompt = TRANSLATION_USER_PROMPT.format(
            target_language=target_language,
            document_text=text
        )

    response = client.messages.create(
        model=model_config["model_id"],
        max_tokens=model_config["max_tokens"],
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt}
        ]
    )

    return response.content[0].text.strip()


def translate_with_google(
    text: str,
    target_language: str,
    model_config: dict,
    is_back_translation: bool = False,
    source_language: str = "English"
) -> str:
    """Translate text using Google Gemini models."""
    genai_client = init_google()

    if is_back_translation:
        prompt = f"""{BACK_TRANSLATION_SYSTEM_PROMPT}

{BACK_TRANSLATION_USER_PROMPT.format(
    source_language=source_language,
    translated_text=text
)}"""
    else:
        prompt = f"""{TRANSLATION_SYSTEM_PROMPT}

{TRANSLATION_USER_PROMPT.format(
    target_language=target_language,
    document_text=text
)}"""

    # Safety settings to allow medical content translation
    # Use proper enum types from the google.generativeai.types module
    from google.generativeai.types import HarmCategory, HarmBlockThreshold

    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }

    model = genai_client.GenerativeModel(
        model_config["model_id"],
        safety_settings=safety_settings
    )

    # Increase max_output_tokens to avoid truncation (finish_reason: MAX_TOKENS)
    # Medical documents can be long; 8192 tokens provides sufficient headroom
    max_tokens = max(model_config["max_tokens"], 8192)

    generation_config = genai_client.types.GenerationConfig(
        max_output_tokens=max_tokens,
        temperature=model_config["temperature"]
    )

    response = model.generate_content(prompt, generation_config=generation_config)

    # Handle cases where response may not have text due to blocking or truncation
    if not response.candidates:
        raise ValueError(f"Gemini returned no candidates. Response: {response}")

    candidate = response.candidates[0]

    # Check finish reason and provide better error messages
    # finish_reason values: 1=STOP (normal), 2=MAX_TOKENS, 3=SAFETY, 4=RECITATION, 5=OTHER
    if candidate.finish_reason == 2:  # MAX_TOKENS
        logger.warning("Gemini response truncated due to max_tokens limit")
    elif candidate.finish_reason == 3:  # SAFETY
        safety_ratings = candidate.safety_ratings if hasattr(candidate, 'safety_ratings') else "N/A"
        raise ValueError(f"Gemini blocked response due to safety filters. Safety ratings: {safety_ratings}")
    elif candidate.finish_reason not in (0, 1):  # 0=UNSPECIFIED, 1=STOP (both OK)
        raise ValueError(f"Gemini returned unexpected finish_reason: {candidate.finish_reason}")

    # Extract text from the response parts
    if not candidate.content or not candidate.content.parts:
        raise ValueError(f"Gemini response has no content parts. Finish reason: {candidate.finish_reason}")

    return candidate.content.parts[0].text.strip()


def translate_with_moonshot(
    text: str,
    target_language: str,
    model_config: dict,
    is_back_translation: bool = False,
    source_language: str = "English"
) -> str:
    """Translate text using Moonshot Kimi K2 model.

    Kimi K2 uses an OpenAI-compatible API, so the interface is similar to OpenAI.
    """
    client = init_moonshot()

    if is_back_translation:
        system_prompt = BACK_TRANSLATION_SYSTEM_PROMPT
        user_prompt = BACK_TRANSLATION_USER_PROMPT.format(
            source_language=source_language,
            translated_text=text
        )
    else:
        system_prompt = TRANSLATION_SYSTEM_PROMPT
        user_prompt = TRANSLATION_USER_PROMPT.format(
            target_language=target_language,
            document_text=text
        )

    response = client.chat.completions.create(
        model=model_config["model_id"],
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=model_config["max_tokens"],
        temperature=model_config["temperature"]
    )

    return response.choices[0].message.content.strip()


def translate_with_huggingface(
    text: str,
    target_language: str,
    model_config: dict,
    is_back_translation: bool = False,
    source_language: str = "English"
) -> str:
    """Translate text using Hugging Face Inference Router (OpenAI-compatible).

    Used for open-weight models like Kimi K2 (moonshotai/Kimi-K2-Instruct-0905).
    Requires a Hugging Face token with Inference API access.
    Endpoint: https://router.huggingface.co/v1
    """
    client = init_huggingface()

    if is_back_translation:
        system_prompt = BACK_TRANSLATION_SYSTEM_PROMPT
        user_prompt = BACK_TRANSLATION_USER_PROMPT.format(
            source_language=source_language,
            translated_text=text
        )
    else:
        system_prompt = TRANSLATION_SYSTEM_PROMPT
        user_prompt = TRANSLATION_USER_PROMPT.format(
            target_language=target_language,
            document_text=text
        )

    # Use OpenAI-compatible chat completions API
    response = client.chat.completions.create(
        model=model_config["model_id"],
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=model_config["max_tokens"],
        temperature=model_config["temperature"]
    )

    return response.choices[0].message.content.strip()


# =============================================================================
# UNIFIED TRANSLATION INTERFACE
# =============================================================================

def translate(
    text: str,
    target_language: str,
    model_name: str,
    is_back_translation: bool = False,
    source_language: str = "English"
) -> str:
    """
    Unified translation function that routes to the appropriate provider.

    Args:
        text: The text to translate
        target_language: Target language name (e.g., "Spanish", "Chinese")
        model_name: Name of the model from ACTIVE_MODELS
        is_back_translation: If True, translates back to English
        source_language: Source language for back-translation

    Returns:
        Translated text
    """
    if model_name not in MODELS:
        raise ValueError(f"Unknown model: {model_name}. Available: {list(MODELS.keys())}")

    model_config = MODELS[model_name]
    provider = model_config["provider"]

    # Route to appropriate provider
    if provider == "openai":
        return translate_with_openai(text, target_language, model_config, is_back_translation, source_language)
    elif provider == "anthropic":
        return translate_with_anthropic(text, target_language, model_config, is_back_translation, source_language)
    elif provider == "google":
        return translate_with_google(text, target_language, model_config, is_back_translation, source_language)
    elif provider == "moonshot":
        return translate_with_moonshot(text, target_language, model_config, is_back_translation, source_language)
    elif provider == "huggingface":
        return translate_with_huggingface(text, target_language, model_config, is_back_translation, source_language)
    else:
        raise ValueError(f"Unknown provider: {provider}")


def translate_with_retry(
    text: str,
    target_language: str,
    model_name: str,
    is_back_translation: bool = False,
    source_language: str = "English",
    max_retries: int = None,
    retry_delay: int = None
) -> str:
    """
    Translate with automatic retry on failure.
    """
    max_retries = max_retries or EXECUTION_CONFIG["retry_attempts"]
    retry_delay = retry_delay or EXECUTION_CONFIG["retry_delay"]

    last_error = None

    for attempt in range(max_retries):
        try:
            result = translate(
                text=text,
                target_language=target_language,
                model_name=model_name,
                is_back_translation=is_back_translation,
                source_language=source_language
            )
            return result

        except Exception as e:
            last_error = e
            logger.warning(f"Translation attempt {attempt + 1}/{max_retries} failed: {e}")

            if attempt < max_retries - 1:
                # Exponential backoff
                sleep_time = retry_delay * (2 ** attempt)
                logger.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)

    raise last_error


# =============================================================================
# FULL TRANSLATION PIPELINE
# =============================================================================

def run_translation_pipeline(
    doc_id: str,
    english_text: str,
    target_language_key: str,
    model_name: str
) -> TranslationResult:
    """
    Run the complete translation pipeline for a single document/language/model combination.

    Pipeline:
    1. English → Target Language (forward translation)
    2. Target Language → English (back translation)

    Args:
        doc_id: Document identifier
        english_text: Original English text
        target_language_key: Language key from LANGUAGES config
        model_name: Model name from ACTIVE_MODELS

    Returns:
        TranslationResult with all translation data
    """
    timestamp = datetime.now().isoformat()
    language_config = LANGUAGES[target_language_key]
    target_language_name = language_config["name"]

    logger.info(f"Starting pipeline: {doc_id} | {model_name} | {target_language_name}")

    try:
        # Step 1: Forward translation (English → Target)
        start_time = time.time()
        translated_text = translate_with_retry(
            text=english_text,
            target_language=target_language_name,
            model_name=model_name,
            is_back_translation=False
        )
        translation_time = time.time() - start_time
        logger.info(f"  Forward translation complete ({translation_time:.2f}s)")

        # Rate limiting delay
        time.sleep(EXECUTION_CONFIG["rate_limit_delay"])

        # Step 2: Back translation (Target → English)
        start_time = time.time()
        back_translated_text = translate_with_retry(
            text=translated_text,
            target_language="English",
            model_name=model_name,
            is_back_translation=True,
            source_language=target_language_name
        )
        back_translation_time = time.time() - start_time
        logger.info(f"  Back translation complete ({back_translation_time:.2f}s)")

        return TranslationResult(
            doc_id=doc_id,
            model=model_name,
            source_language="English",
            target_language=target_language_key,
            original_text=english_text,
            translated_text=translated_text,
            back_translated_text=back_translated_text,
            timestamp=timestamp,
            translation_time_seconds=translation_time,
            back_translation_time_seconds=back_translation_time,
            success=True
        )

    except Exception as e:
        logger.error(f"Pipeline failed: {doc_id} | {model_name} | {target_language_name}")
        logger.error(f"Error: {str(e)}")
        logger.error(traceback.format_exc())

        return TranslationResult(
            doc_id=doc_id,
            model=model_name,
            source_language="English",
            target_language=target_language_key,
            original_text=english_text,
            translated_text="",
            back_translated_text=None,
            timestamp=timestamp,
            translation_time_seconds=0,
            back_translation_time_seconds=None,
            success=False,
            error_message=str(e)
        )


# =============================================================================
# BATCH PROCESSING
# =============================================================================

def process_batch(
    documents: list,
    languages: list[str] = None,
    models: list[str] = None,
    save_intermediate: bool = True
) -> list[TranslationResult]:
    """
    Process a batch of documents through the translation pipeline.

    Args:
        documents: List of PatientDocument objects
        languages: List of language keys (defaults to ACTIVE_LANGUAGES)
        models: List of model names (defaults to ACTIVE_MODELS)
        save_intermediate: Whether to save results after each document

    Returns:
        List of TranslationResult objects
    """
    languages = languages or ACTIVE_LANGUAGES
    models = models or ACTIVE_MODELS

    total_combinations = len(documents) * len(languages) * len(models)
    logger.info(f"Starting batch processing: {total_combinations} total combinations")
    logger.info(f"  Documents: {len(documents)}")
    logger.info(f"  Languages: {languages}")
    logger.info(f"  Models: {models}")

    results = []
    completed = 0

    for doc in documents:
        doc_results = []

        for lang_key in languages:
            for model_name in models:
                result = run_translation_pipeline(
                    doc_id=doc.doc_id,
                    english_text=doc.english_text,
                    target_language_key=lang_key,
                    model_name=model_name
                )
                doc_results.append(result)
                results.append(result)

                completed += 1
                progress = (completed / total_combinations) * 100
                logger.info(f"Progress: {completed}/{total_combinations} ({progress:.1f}%)")

                # Rate limiting between API calls
                time.sleep(EXECUTION_CONFIG["rate_limit_delay"])

        # Save intermediate results after each document
        if save_intermediate:
            save_results(doc_results, f"intermediate_{doc.doc_id}.json")

    return results


def save_results(results: list[TranslationResult], filename: str):
    """Save translation results to JSON file."""
    filepath = TRANSLATIONS_DIR / filename
    data = [r.to_dict() for r in results]

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(f"Saved {len(results)} results to {filepath}")
    return filepath


def load_results(filename: str) -> list[TranslationResult]:
    """Load translation results from JSON file."""
    filepath = TRANSLATIONS_DIR / filename

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    results = [TranslationResult.from_dict(d) for d in data]
    logger.info(f"Loaded {len(results)} results from {filepath}")
    return results


# =============================================================================
# CHECKPOINT AND RESUME
# =============================================================================

def get_checkpoint_file() -> Path:
    """Get the checkpoint file path."""
    return TRANSLATIONS_DIR / "checkpoint.json"


def save_checkpoint(completed_combinations: set, results: list[TranslationResult]):
    """Save checkpoint for resuming interrupted processing."""
    checkpoint = {
        "completed": list(completed_combinations),
        "timestamp": datetime.now().isoformat(),
        "total_results": len(results)
    }

    with open(get_checkpoint_file(), 'w') as f:
        json.dump(checkpoint, f)

    logger.info(f"Checkpoint saved: {len(completed_combinations)} combinations completed")


def load_checkpoint() -> tuple[set, bool]:
    """Load checkpoint if exists."""
    checkpoint_file = get_checkpoint_file()

    if checkpoint_file.exists():
        with open(checkpoint_file, 'r') as f:
            checkpoint = json.load(f)
        completed = set(checkpoint.get("completed", []))
        logger.info(f"Checkpoint loaded: {len(completed)} combinations already completed")
        return completed, True
    else:
        return set(), False


def process_batch_with_resume(
    documents: list,
    languages: list[str] = None,
    models: list[str] = None,
) -> list[TranslationResult]:
    """
    Process batch with checkpoint/resume capability.

    Allows resuming interrupted processing by skipping already-completed combinations.
    """
    languages = languages or ACTIVE_LANGUAGES
    models = models or ACTIVE_MODELS

    # Load existing checkpoint
    completed_combinations, has_checkpoint = load_checkpoint()

    # Load existing results if checkpoint exists
    all_results_file = TRANSLATIONS_DIR / "all_results.json"
    if has_checkpoint and all_results_file.exists():
        results = load_results("all_results.json")
    else:
        results = []

    total_combinations = len(documents) * len(languages) * len(models)
    remaining = total_combinations - len(completed_combinations)

    logger.info(f"Processing with resume: {remaining} remaining of {total_combinations}")

    for doc in documents:
        for lang_key in languages:
            for model_name in models:
                # Create unique combination key
                combo_key = f"{doc.doc_id}|{lang_key}|{model_name}"

                # Skip if already completed
                if combo_key in completed_combinations:
                    continue

                # Process this combination
                result = run_translation_pipeline(
                    doc_id=doc.doc_id,
                    english_text=doc.english_text,
                    target_language_key=lang_key,
                    model_name=model_name
                )

                results.append(result)
                completed_combinations.add(combo_key)

                # Save checkpoint periodically
                if len(results) % EXECUTION_CONFIG["batch_size"] == 0:
                    save_results(results, "all_results.json")
                    save_checkpoint(completed_combinations, results)

                # Rate limiting
                time.sleep(EXECUTION_CONFIG["rate_limit_delay"])

    # Final save
    save_results(results, "all_results.json")
    save_checkpoint(completed_combinations, results)

    return results


# =============================================================================
# TESTING / VERIFICATION
# =============================================================================

def test_single_translation(model_name: str = "gpt-4-turbo", language: str = "spanish"):
    """Test a single translation to verify setup."""
    test_text = """Heart Failure: What You Need to Know

What is Heart Failure?
Heart failure means your heart is not pumping blood as well as it should.

Warning Signs - Call Your Doctor If You Have:
• Sudden weight gain
• Increased swelling in your legs
• Shortness of breath"""

    logger.info(f"\n{'='*60}")
    logger.info(f"TESTING: {model_name} → {LANGUAGES[language]['name']}")
    logger.info(f"{'='*60}")

    try:
        result = run_translation_pipeline(
            doc_id="TEST_001",
            english_text=test_text,
            target_language_key=language,
            model_name=model_name
        )

        logger.info(f"\nSuccess: {result.success}")
        logger.info(f"\n--- ORIGINAL (English) ---\n{result.original_text[:500]}...")
        logger.info(f"\n--- TRANSLATED ({LANGUAGES[language]['name']}) ---\n{result.translated_text[:500]}...")
        logger.info(f"\n--- BACK-TRANSLATED (English) ---\n{result.back_translated_text[:500]}...")

        return result

    except Exception as e:
        logger.error(f"Test failed: {e}")
        logger.error(traceback.format_exc())
        return None


def verify_api_connections():
    """Verify all API connections are working."""
    logger.info("\n" + "="*60)
    logger.info("VERIFYING API CONNECTIONS")
    logger.info("="*60)

    test_text = "Hello, this is a test."
    status = {}

    # Test OpenAI
    try:
        for model in [m for m in ACTIVE_MODELS if MODELS[m]["provider"] == "openai"]:
            result = translate(test_text, "Spanish", model)
            status[model] = "✓ Working"
            logger.info(f"  {model}: ✓ Working")
    except Exception as e:
        status["openai"] = f"✗ Failed: {str(e)[:50]}"
        logger.error(f"  OpenAI: ✗ Failed: {e}")

    # Test Anthropic
    try:
        for model in [m for m in ACTIVE_MODELS if MODELS[m]["provider"] == "anthropic"]:
            result = translate(test_text, "Spanish", model)
            status[model] = "✓ Working"
            logger.info(f"  {model}: ✓ Working")
    except Exception as e:
        status["anthropic"] = f"✗ Failed: {str(e)[:50]}"
        logger.error(f"  Anthropic: ✗ Failed: {e}")

    # Test Google
    try:
        for model in [m for m in ACTIVE_MODELS if MODELS[m]["provider"] == "google"]:
            result = translate(test_text, "Spanish", model)
            status[model] = "✓ Working"
            logger.info(f"  {model}: ✓ Working")
    except Exception as e:
        status["google"] = f"✗ Failed: {str(e)[:50]}"
        logger.error(f"  Google: ✗ Failed: {e}")

    # Test Moonshot (Kimi K2 via direct API)
    try:
        for model in [m for m in ACTIVE_MODELS if MODELS[m]["provider"] == "moonshot"]:
            result = translate(test_text, "Spanish", model)
            status[model] = "✓ Working"
            logger.info(f"  {model}: ✓ Working")
    except Exception as e:
        status["moonshot"] = f"✗ Failed: {str(e)[:50]}"
        logger.error(f"  Moonshot: ✗ Failed: {e}")

    # Test Hugging Face (Kimi K2 via HF Inference API)
    try:
        for model in [m for m in ACTIVE_MODELS if MODELS[m]["provider"] == "huggingface"]:
            result = translate(test_text, "Spanish", model)
            status[model] = "✓ Working"
            logger.info(f"  {model}: ✓ Working")
    except Exception as e:
        status["huggingface"] = f"✗ Failed: {str(e)[:50]}"
        logger.error(f"  Hugging Face: ✗ Failed: {e}")

    return status


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        verify_api_connections()
    elif len(sys.argv) > 1 and sys.argv[1] == "--test":
        model = sys.argv[2] if len(sys.argv) > 2 else "gpt-5.1"
        lang = sys.argv[3] if len(sys.argv) > 3 else "spanish"
        test_single_translation(model, lang)
    else:
        print("""
Usage:
  python translation_pipeline.py --verify    # Verify API connections
  python translation_pipeline.py --test [model] [language]  # Test single translation

Examples:
  python translation_pipeline.py --test gpt-5.1 spanish
  python translation_pipeline.py --test claude-sonnet-4.5 chinese_simplified
  python translation_pipeline.py --test kimi-k2 vietnamese
        """)
