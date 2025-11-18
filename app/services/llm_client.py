"""
Lightweight Gemini LLM client wrapper.
Provides a factory function that returns an LLM instance or None if unavailable.
"""

import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)


def create_llm(api_key: Optional[str], model: str) -> Optional[Any]:
    """
    Create a Gemini LLM instance if possible.
    
    Args:
        api_key: Google Generative AI API key
        model: Model identifier (e.g., "gemini-2.0-flash")
    
    Returns:
        LLM instance with .invoke(prompt) -> object with .content field,
        or None if LLM cannot be created
    """
    if not api_key:
        logger.info("No GEMINI_API_KEY provided, LLM path disabled")
        return None
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=0.7,
        )
        logger.info(f"LLM initialized successfully with model: {model}")
        return llm
    except ImportError:
        logger.warning("langchain-google-genai not installed, LLM path disabled")
        return None
    except Exception as e:
        logger.warning(f"Failed to initialize LLM: {e}, LLM path disabled")
        return None
