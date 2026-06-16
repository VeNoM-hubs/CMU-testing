import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

DEFAULT_BASE_URL = "https://ai-gateway.andrew.cmu.edu/v1"
DEFAULT_MODEL = "gpt-4o-mini"
KEY_FILENAMES = ("api key.txt", "API key", "api_key.txt", ".api_key")


def normalize_api_key(key: str, base_url: str) -> str:
    """CMU AI Gateway virtual keys must start with 'sk-'."""
    if "ai-gateway.andrew.cmu.edu" in base_url and not key.startswith("sk-"):
        return f"sk-{key}"
    return key


def load_api_key(base_url: str) -> str:
    if key := os.environ.get("CHAT_API_KEY", "").strip():
        return normalize_api_key(key, base_url)

    script_dir = Path(__file__).resolve().parent
    for name in KEY_FILENAMES:
        path = script_dir / name
        if path.is_file():
            key = path.read_text(encoding="utf-8").strip()
            if key:
                return normalize_api_key(key, base_url)

    raise ValueError(
        "Missing API key. Set CHAT_API_KEY or place your key in one of: "
        + ", ".join(KEY_FILENAMES)
    )


def print_help(model: str, base_url: str) -> None:
    print(
        f"\nCommands:\n"
        f"  /help            Show this help\n"
        f"  /quit, /exit     End the chat\n"
        f"  /clear           Clear conversation history\n"
        f"  /model <name>    Switch model (current: {model})\n"
        f"\nConfig (env vars):\n"
        f"  CHAT_API_KEY     API key (overrides key file)\n"
        f"  CHAT_API_BASE    API base URL (current: {base_url})\n"
        f"  CHAT_MODEL       Default model (current: {model})\n"
    )


def run_terminal_chat() -> None:
    load_dotenv()

    base_url = os.environ.get("CHAT_API_BASE", DEFAULT_BASE_URL).strip()
    model = os.environ.get("CHAT_MODEL", DEFAULT_MODEL).strip()
    api_key = load_api_key(base_url)

    client = OpenAI(base_url=base_url, api_key=api_key)
    messages: list[dict[str, str]] = []

    print("Terminal LLM Chat")
    print(f"Model: {model}  |  API: {base_url}")
    print("Type a message and press Enter. /help for commands.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not user_input:
            continue

        lowered = user_input.lower()
        if lowered in {"/quit", "/exit", "quit", "exit"}:
            print("Bye.")
            break
        if lowered == "/help":
            print_help(model, base_url)
            continue
        if lowered == "/clear":
            messages.clear()
            print("Conversation cleared.")
            continue
        if lowered.startswith("/model"):
            parts = user_input.split(maxsplit=1)
            if len(parts) < 2 or not parts[1].strip():
                print(f"Usage: /model <name>  (current: {model})")
                continue
            model = parts[1].strip()
            print(f"Switched to model: {model}")
            continue

        messages.append({"role": "user", "content": user_input})
        print("Assistant: ", end="", flush=True)

        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
            )
            reply = response.choices[0].message.content or ""
            print(reply)
            messages.append({"role": "assistant", "content": reply})
        except Exception as exc:
            messages.pop()
            print(f"\nError: {exc}")

        print()


if __name__ == "__main__":
    run_terminal_chat()
