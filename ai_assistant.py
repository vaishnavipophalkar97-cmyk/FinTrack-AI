import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "gemma3:1b"


def ask_gemma(question, financial_summary, model=DEFAULT_MODEL):
    """
    Ask a locally running Gemma model about an aggregate
    financial summary.

    The financial summary should be calculated by Python.
    The model should explain the supplied figures, not
    calculate authoritative financial totals itself.
    """

    prompt = f"""
You are FinTrack AI, a helpful financial record assistant.

Your job is to explain the user's recorded financial activity.

IMPORTANT RULES:
1. Use only the information in the financial summary.
2. Never invent transactions, balances, dates, or amounts.
3. Do not give investment, tax, or financial advice.
4. Do not claim that a deposit is income unless the data says so.
5. If the summary does not contain the answer, say so.
6. Explain that recorded contributions are not necessarily
   the current market value of investments.
7. Keep your response clear and concise.

FINANCIAL SUMMARY:
{financial_summary}

USER QUESTION:
{question}

Answer using the supplied information.
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        response.raise_for_status()
        data = response.json()

        answer = data.get("response", "").strip()

        if not answer:
            return "The AI model returned an empty response."

        return answer

    except requests.exceptions.ConnectionError:
        return (
            "Could not connect to Ollama. Make sure Ollama is "
            "installed and running on this computer."
        )

    except requests.exceptions.Timeout:
        return (
            "The AI request took too long. Try again or use "
            "a smaller model."
        )

    except requests.exceptions.HTTPError as error:
        return (
            f"Ollama returned an HTTP error: {error}. "
            "Check that the selected model is installed."
        )

    except (ValueError, KeyError):
        return "Could not read the response from the AI model."

    except requests.exceptions.RequestException as error:
        return f"An AI connection error occurred: {error}"