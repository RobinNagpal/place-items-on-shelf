"""A small fixed vocabulary for the tiny VLA's instruction encoder.

Real VLAs use a learned subword tokenizer (BPE / SentencePiece) over
tens of thousands of tokens. Ours uses a hand-listed vocabulary of
the words this exercise's instructions might contain, which keeps the
tokeniser to a 20-line dictionary lookup and the embedding table to a
few hundred floats. The mechanism is the same; the scale is not.
"""

from __future__ import annotations

import re

VOCAB: list[str] = [
    "<pad>", "<unk>",
    "pick", "place", "put", "grab", "move", "lift",
    "the", "a", "and", "to", "from", "into", "onto",
    "red", "blue", "green", "yellow", "black", "white",
    "cube", "block", "vial", "cap", "object", "thing",
    "left", "right", "center", "above", "below",
    "tray", "slot", "rack", "table", "shelf",
]

WORD_TO_ID: dict[str, int] = {w: i for i, w in enumerate(VOCAB)}
VOCAB_SIZE: int = len(VOCAB)
MAX_LEN: int = 12


def tokenize(text: str) -> list[int]:
    """Lowercase, split on words, map to ids, pad / truncate to MAX_LEN."""
    words = re.findall(r"[a-zA-Z]+", text.lower())
    ids = [WORD_TO_ID.get(w, WORD_TO_ID["<unk>"]) for w in words]
    ids = ids[:MAX_LEN]
    while len(ids) < MAX_LEN:
        ids.append(WORD_TO_ID["<pad>"])
    return ids
