
import json
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2"


def test_chat():
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": "Explain what an AI chatbot is in two sentences."
            }
        ],
        "stream": False
    }

    request_data = json.dumps(payload).encode("utf-8")

    request = Request(
        OLLAMA_URL,
        data=request_data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urlopen(request, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))

        print("\nAI Response:")
        print(result["message"]["content"])

    except HTTPError as error:
        print(f"Ollama returned HTTP error {error.code}: {error.reason}")

    except URLError as error:
        print(f"Could not connect to Ollama: {error.reason}")

    except TimeoutError:
        print("The request timed out. Try again or use a smaller model.")

    except (KeyError, json.JSONDecodeError):
        print("Ollama returned an unexpected response format.")


if __name__ == "__main__":
    test_chat()
