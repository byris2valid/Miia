import json
import os
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from prompt import SYSTEM_PROMPT
from validate import apply_reply, cart_total, parse_reply

load_dotenv()

MODEL = "claude-sonnet-5"
FALLBACK_SAY = "Sorry, I didn't catch that. Could you say it again?"

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def load_catalog() -> dict[str, dict]:
    path = Path(__file__).parent / "catalog.json"
    items = json.loads(path.read_text(encoding="utf-8"))
    return {item["slot"]: item for item in items}


def build_system(catalog: dict[str, dict], cart: dict[str, int]) -> str:
    # str.replace instead of .format because the prompt contains literal JSON braces
    return (
        SYSTEM_PROMPT
        .replace("{catalog_json}", json.dumps(list(catalog.values()), indent=2))
        .replace("{cart_json}", json.dumps(cart))
    )


def call_model(system: str, history: list[dict]) -> str:
    resp = client.messages.create(
        model=MODEL,
        max_tokens=400,
        system=system,
        messages=history,
    )
    for block in resp.content:
        if block.type == "text":
            return block.text
    raise ValueError("No text block in response")


def get_reply(system: str, history: list[dict], catalog: dict[str, dict]):
    raw = call_model(system, history)
    try:
        return parse_reply(raw, catalog), raw
    except Exception:
        retry_history = history + [
            {"role": "assistant", "content": raw},
            {"role": "user", "content": "Your last reply was not valid JSON. Respond with only the JSON object."},
        ]
        raw = call_model(system, retry_history)
        try:
            return parse_reply(raw, catalog), raw
        except Exception:
            return None, raw


def print_cart(cart: dict[str, int], catalog: dict[str, dict]) -> None:
    if not cart:
        print("  [cart empty]")
        return
    for slot, qty in cart.items():
        item = catalog[slot]
        print(f"  {qty} x {item['name']} ({slot}) - ${item['price'] * qty:.2f}")
    print(f"  TOTAL: ${cart_total(cart, catalog):.2f}")


def main() -> None:
    catalog = load_catalog()
    cart: dict[str, int] = {}
    history: list[dict] = []

    print("Miia: Hi, I'm Miia! What can I get you? (Ctrl+C to quit)")
    while True:
        try:
            user = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nBye!")
            return
        if not user:
            continue

        history.append({"role": "user", "content": user})
        system = build_system(catalog, cart)
        reply, raw = get_reply(system, history, catalog)

        if reply is None:
            print(f"Miia: {FALLBACK_SAY}")
            history.pop()
            continue

        history.append({"role": "assistant", "content": raw})
        apply_reply(reply, cart, catalog)

        print(f"Miia: {reply.say}")
        print_cart(cart, catalog)

        if reply.action == "checkout":
            print(f"\nCheckout total: ${cart_total(cart, catalog):.2f} (payment not implemented yet)")
            return


if __name__ == "__main__":
    main()
