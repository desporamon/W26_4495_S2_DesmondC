# =============================================================================
# BC Health Platform - OpenAI Utility Module
# =============================================================================
# MEDICAL DISCLAIMER:
# This tool is for informational purposes only and does not replace
# professional medical advice. Always consult a qualified healthcare
# provider for medical concerns. If you are experiencing a medical
# emergency, call 911 immediately.
# =============================================================================

"""
OpenAI API integration for the BC Health Platform Symptom Assessment Chatbot.

This module provides functions to:
- Extract structured symptom data from natural language user input
- Verify that the OpenAI API connection is working

The API key is loaded from Streamlit's secrets management (secrets.toml),
ensuring no credentials are hardcoded in source code.
"""

import json

import openai
import streamlit as st


# =============================================================================
# API CONFIGURATION
# =============================================================================

# Load the API key from Streamlit secrets (set in .streamlit/secrets.toml)
# This avoids hardcoding any credentials in the source code.
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Use a low temperature for consistent, deterministic medical responses.
# Lower temperature = less randomness = more reliable symptom extraction.
MODEL_NAME = "gpt-4o-mini"
MODEL_TEMPERATURE = 0.1


# =============================================================================
# SYSTEM PROMPT FOR SYMPTOM EXTRACTION
# =============================================================================

# This prompt instructs GPT to act as a medical symptom parser.
# It must return ONLY valid JSON so we can parse the response programmatically.
SYMPTOM_EXTRACTION_PROMPT = """You are a medical symptom extraction assistant.
Your job is to analyze a patient's description and extract structured information.

You MUST respond with ONLY valid JSON in this exact format (no extra text):
{
    "symptoms": ["symptom1", "symptom2"],
    "duration": "duration string or unknown",
    "severity": "mild or moderate or severe"
}

Rules:
- "symptoms": a list of distinct symptom strings extracted from the input.
- "duration": how long the patient has had symptoms. Use "unknown" if not mentioned.
- "severity": infer from context clues (e.g., "terrible" = severe, "a bit" = mild).
  If unclear, default to "moderate".
- Keep symptom names short and clear (e.g., "chest pain", "dizziness", "nausea").
- Do NOT include any text outside the JSON object."""


# =============================================================================
# MAIN FUNCTIONS
# =============================================================================

def extract_symptoms(user_input: str) -> dict:
    """
    Extract structured symptom information from natural language input.

    Sends the user's symptom description to OpenAI's GPT model, which parses
    it into a structured dictionary with symptoms, duration, and severity.

    Args:
        user_input: A natural language string describing symptoms.
                    Example: "I've had chest pain for 2 hours and feel dizzy"

    Returns:
        A dictionary with the following keys:
        - "symptoms": list of symptom strings (e.g., ["chest pain", "dizziness"])
        - "duration": duration string (e.g., "2 hours") or "unknown"
        - "severity": one of "mild", "moderate", or "severe"
        - "raw_response": the full text response from GPT

        If an error occurs, returns {"error": "<error message>"} instead.
    """
    try:
        # Call the OpenAI Chat Completions API
        response = openai.chat.completions.create(
            model=MODEL_NAME,
            temperature=MODEL_TEMPERATURE,
            messages=[
                {
                    "role": "system",
                    "content": SYMPTOM_EXTRACTION_PROMPT
                },
                {
                    "role": "user",
                    "content": user_input
                }
            ]
        )

        # Extract the text content from the API response
        raw_response = response.choices[0].message.content.strip()

        # Parse the JSON response from GPT into a Python dictionary
        parsed = json.loads(raw_response)

        # Attach the raw response for debugging or display purposes
        parsed["raw_response"] = raw_response

        return parsed

    except json.JSONDecodeError:
        # GPT returned something that isn't valid JSON
        return {"error": "Failed to parse symptom data from AI response."}
    except openai.AuthenticationError:
        return {"error": "Invalid OpenAI API key. Check your secrets.toml configuration."}
    except openai.RateLimitError:
        return {"error": "API rate limit reached. Please try again in a moment."}
    except openai.APIError as e:
        return {"error": f"OpenAI API error: {e}"}
    except Exception as e:
        return {"error": f"Unexpected error during symptom extraction: {e}"}


def test_openai_connection() -> bool:
    """
    Test whether the OpenAI API key is valid and the service is reachable.

    Makes a minimal API call to verify connectivity. Useful for health checks
    or displaying connection status in the UI.

    Returns:
        True if the API responds successfully, False otherwise.
    """
    try:
        response = openai.chat.completions.create(
            model=MODEL_NAME,
            temperature=MODEL_TEMPERATURE,
            max_tokens=10,
            messages=[
                {"role": "user", "content": "Say OK"}
            ]
        )
        # If we get a response with content, the connection works
        return response.choices[0].message.content is not None
    except Exception:
        return False
