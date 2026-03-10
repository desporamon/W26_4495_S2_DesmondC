# =============================================================================
# BC Health Platform - OpenAI Utility Module
# =============================================================================
# MEDICAL DISCLAIMER:
# This tool is for informational purposes only and does not replace
# professional medical advice. Always consult a qualified healthcare
# provider for medical concerns. If you are experiencing a medical
# emergency, call 911 immediately.
# =============================================================================
# Sprint 3E: Multi-turn chatbot enhancement

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


# =============================================================================
# MULTI-TURN EXTRACTION — Sprint 3E
# =============================================================================

# System prompt for multi-turn extraction.  Unlike SYMPTOM_EXTRACTION_PROMPT,
# this version instructs GPT to look at the FULL conversation and accumulate
# all symptom information rather than parsing a single message in isolation.
MULTITURN_EXTRACTION_PROMPT = """You are a medical symptom extraction assistant working in a multi-turn conversation.
Your job is to review the full conversation history and the latest user message, \
then extract ALL accumulated symptom information found anywhere in the conversation.

You MUST respond with ONLY valid JSON in this exact format (no extra text):
{
    "symptoms": ["symptom1", "symptom2"],
    "duration": "duration string or unknown",
    "severity": "mild or moderate or severe",
    "body_location": "body location string or null"
}

Rules:
- "symptoms": a COMPLETE list of ALL distinct symptoms mentioned across the ENTIRE conversation, not just the latest message. Accumulate — do NOT drop symptoms from earlier turns.
- "duration": how long the patient has had symptoms. Use "unknown" if never mentioned.
- "severity": infer from context across the full conversation (e.g., "terrible" = severe, "a bit" = mild). Default to "moderate" if unclear.
- "body_location": where on the body the symptoms are felt (e.g., "chest", "abdomen", "head"). Use null if not mentioned anywhere.
- Keep symptom names short and clear (e.g., "chest pain", "dizziness", "nausea").
- Do NOT include any text outside the JSON object."""


def extract_symptoms_multiturn(user_input: str, conversation_history: list) -> dict:
    """
    Extract structured symptom information accumulated across a multi-turn conversation.

    Unlike extract_symptoms(), this function provides the full conversation history
    to GPT so that symptoms, duration, severity, and body location mentioned across
    multiple turns are consolidated into a single structured result.

    Args:
        user_input: The user's latest message.
        conversation_history: List of {"role": "user"/"assistant", "content": "..."}
                              dicts representing the conversation so far (not including
                              the current user_input turn — that is appended here).

    Returns:
        A dictionary with:
        - "symptoms":      list of all accumulated symptom strings
        - "duration":      duration string (e.g., "3 days") or "unknown"
        - "severity":      one of "mild", "moderate", or "severe"
        - "body_location": body location string or None
        - "raw_response":  the raw GPT response text

        On failure returns {"error": "<error message>"}.
    """
    try:
        messages = [{"role": "system", "content": MULTITURN_EXTRACTION_PROMPT}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_input})

        response = openai.chat.completions.create(
            model=MODEL_NAME,
            temperature=0.3,
            messages=messages,
        )
        raw_response = response.choices[0].message.content.strip()
        parsed = json.loads(raw_response)
        parsed["raw_response"] = raw_response
        return parsed

    except json.JSONDecodeError:
        return {"error": "Failed to parse symptom data from AI response."}
    except openai.AuthenticationError:
        return {"error": "Invalid OpenAI API key. Check your secrets.toml configuration."}
    except openai.RateLimitError:
        return {"error": "API rate limit reached. Please try again in a moment."}
    except openai.APIError as e:
        return {"error": f"OpenAI API error: {e}"}
    except Exception as e:
        return {"error": f"Unexpected error during multi-turn symptom extraction: {e}"}


def generate_follow_up_response(follow_up_question: str, conversation_history: list) -> str:
    """
    Generate a natural, empathetic conversational reply that embeds a follow-up question.

    Takes a slot-filling question (e.g., "How long have you been experiencing
    these symptoms?") and asks GPT to rephrase it warmly given the conversation
    context, rather than presenting it as a bare form prompt.

    Args:
        follow_up_question: The specific question to embed naturally.
        conversation_history: Full conversation history so far as a list of
                              {"role": "user"/"assistant", "content": "..."} dicts.

    Returns:
        A natural-language string for the assistant to display.
        Falls back to returning follow_up_question as-is if the API call fails.

    Temperature: 0.5 — slightly higher than extraction calls for natural variation.
    """
    system_prompt = (
        "You are a caring health assessment assistant for BC residents. "
        "Your role is to gather more information about a patient's symptoms "
        "through natural conversation. "
        "Ask the follow-up question naturally and empathetically in 2-3 sentences maximum. "
        "Acknowledge what the patient has already shared before asking your question. "
        "Do not diagnose. Do not provide medical advice yet."
    )

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(conversation_history)
    messages.append({
        "role": "user",
        "content": (
            f"[Internal instruction — do not repeat this to the user: "
            f"Ask the following question naturally and empathetically: {follow_up_question}]"
        ),
    })

    try:
        response = openai.chat.completions.create(
            model=MODEL_NAME,
            temperature=0.5,
            messages=messages,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        # Graceful degradation: return the raw question if the API call fails
        return follow_up_question


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
