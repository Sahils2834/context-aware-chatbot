
import os
from dotenv import load_dotenv
from openai import OpenAI, APIConnectionError, APIStatusError, APITimeoutError

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise RuntimeError(
        "OPENAI_API_KEY is missing. Check your .env file."
    )

client = OpenAI(api_key=api_key, timeout=60.0, max_retries=2)


def test_chat():
    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            instructions=(
                "You are a helpful AI assistant. "
                "Explain technical topics clearly and simply."
            ),
            input="Explain what an AI chatbot is in two sentences."
        )

        print("\nOpenAI Response:")
        print(response.output_text)

    except APITimeoutError:
        print("The OpenAI request timed out. Please try again.")

    except APIConnectionError:
        print("Could not connect to OpenAI. Check your internet connection.")

    except APIStatusError as error:
        print(f"OpenAI API error: HTTP {error.status_code}")
        print(error.message)


if __name__ == "__main__":
    test_chat()
