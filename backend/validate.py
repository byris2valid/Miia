import json
from typing import Literal

from pydantic import BaseModel, Field


class ItemRef(BaseModel):
    slot: str
    qty: int = Field(ge=1, le=10)


class MiiaReply(BaseModel):
    action: Literal[
        "add_item", "remove_item", "recommend", "clarify",
        "checkout", "smalltalk", "cancel",
    ]
    items: list[ItemRef] = []
    say: str


def parse_reply(raw: str, catalog: dict[str, dict]) -> MiiaReply:
    reply = MiiaReply.model_validate(json.loads(raw))
    for it in reply.items:
        if it.slot not in catalog:
            raise ValueError(f"Unknown slot {it.slot}")
    return reply


def apply_reply(reply: MiiaReply, cart: dict[str, int], catalog: dict[str, dict]) -> dict[str, int]:
    if reply.action == "add_item":
        for it in reply.items:
            have = cart.get(it.slot, 0)
            cart[it.slot] = min(have + it.qty, catalog[it.slot]["stock"])
    elif reply.action == "remove_item":
        for it in reply.items:
            cart[it.slot] = max(cart.get(it.slot, 0) - it.qty, 0)
            if cart[it.slot] == 0:
                cart.pop(it.slot)
    elif reply.action == "cancel":
        cart.clear()
    return cart


def cart_total(cart: dict[str, int], catalog: dict[str, dict]) -> float:
    return round(sum(catalog[s]["price"] * q for s, q in cart.items()), 2)
