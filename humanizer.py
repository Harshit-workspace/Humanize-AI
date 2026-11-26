
import requests
import re


# ==========================================
# OLLAMA CONFIGURATION
# ==========================================

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:3b"

REQUEST_TIMEOUT = (10, 180)


# ==========================================
# WRITING STYLES
# ==========================================

STYLES = {
    "Clear and natural": """
Write in clear, natural and easy-to-understand English.
Use smooth sentence transitions.
Avoid unnecessarily complicated vocabulary.
Keep the writing straightforward and engaging.
""",

    "Casual": """
Use a friendly, conversational tone.
Make the writing relaxed and approachable.
Use natural everyday English.
Avoid sounding overly formal.
""",

    "Academic": """
Use formal, readable academic English.
Maintain logical structure and precise vocabulary.
Use appropriate transitions between ideas.
Avoid unnecessary complexity.
""",

    "Professional": """
Use polished and professional English.
Make the writing clear, confident and organised.
Use appropriate professional vocabulary.
Keep the tone respectful and concise.
"""
}


# ==========================================
# SYSTEM PROMPT
# ==========================================

SYSTEM_PROMPT = """
You are an experienced professional writing editor.

Rewrite the text provided by the user.

IMPORTANT RULES:

1. Preserve the original meaning and intention.
2. Do not invent facts, statistics or examples.
3. Do not change names, dates, numbers or technical terms.
4. Correct grammar, spelling and punctuation.
5. Improve sentence structure and readability.
6. Improve paragraph flow and transitions.
7. Avoid repetitive expressions.
8. Maintain a consistent writing style.
9. Keep approximately the same length.
10. Do not remove important information.
11. Preserve lists and formatting where appropriate.
12. Do not unnecessarily replace simple words with complicated ones.

OUTPUT REQUIREMENTS:

Return ONLY the rewritten text.

Never include:
- Introductions
- Explanations
- Editing notes
- Reminders
- Instructions
- Your thoughts or reasoning
- Comments about the original text

The final response must contain only the edited writing.
"""


# ==========================================
# RESPONSE CLEANING
# ==========================================

def clean_response(result):

    if not result:
        return ""

    # Remove thinking tags
    result = re.sub(
        r"<think>.*?</think>",
        "",
        result,
        flags=re.DOTALL | re.IGNORECASE
    )

    result = result.strip()

    # Remove common introductions
    result = re.sub(
        r"^(Here is the revised text:|"
        r"Here is the improved version:|"
        r"Here is the rewritten text:|"
        r"Revised text:|"
        r"Improved version:|"
        r"Rewritten text:)\s*",
        "",
        result,
        flags=re.IGNORECASE
    )

    # Remove unwanted reminder sections
    result = re.split(
        r"\n\s*(?:Remember|Note|Explanation|Editing notes)\s*:",
        result,
        maxsplit=1,
        flags=re.IGNORECASE
    )[0]

    # Remove surrounding quotation marks
    if (
        len(result) >= 2
        and result.startswith('"')
        and result.endswith('"')
    ):
        result = result[1:-1].strip()

    return result.strip()


# ==========================================
# HUMANIZER FUNCTION
# ==========================================

def humanize_text(text, style="Clear and natural"):

    if not text or not text.strip():
        return "Please enter some text."

    instruction = STYLES.get(
        style,
        STYLES["Clear and natural"]
    )

    user_prompt = f"""
WRITING STYLE:
{instruction}

TEXT TO EDIT:

{text}

TASK:
Improve the writing while preserving its meaning.

Return only the edited text.
Do not repeat these instructions.
"""

    try:

        response = requests.post(
            OLLAMA_URL,

            json={
                "model": MODEL_NAME,

                "messages": [
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],

                "stream": False,

                "options": {
                    "temperature": 0.45,
                    "top_p": 0.9,
                    "top_k": 40,
                    "repeat_penalty": 1.1,
                    "num_predict": 2048
                }
            },

            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        try:
            data = response.json()

        except ValueError:
            raise RuntimeError(
                "Ollama returned an invalid response."
            )

        result = data.get(
            "message", {}
        ).get(
            "content", ""
        )

        result = clean_response(result)

        if not result:
            raise RuntimeError(
                "The model returned empty text. Please try again."
            )

        return result

    # ======================================
    # ERROR HANDLING
    # ======================================

    except requests.exceptions.ConnectionError:

        raise RuntimeError(
            "Ollama is not running. "
            "Please start Ollama and try again."
        )

    except requests.exceptions.Timeout:

        raise RuntimeError(
            "The model took too long to respond. "
            "Try using shorter text."
        )

    except requests.exceptions.HTTPError as error:

        status_code = (
            error.response.status_code
            if error.response is not None
            else "Unknown"
        )

        raise RuntimeError(
            f"Ollama HTTP error ({status_code}). "
            "Check whether the model is available."
        )

    except requests.exceptions.RequestException as error:

        raise RuntimeError(
            f"Connection error: {error}"
        )

    except RuntimeError:
        raise

    except Exception as error:

        raise RuntimeError(
            f"Unexpected humanizer error: {error}"
        )
