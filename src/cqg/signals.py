# src/cqg/signals.py
import re
from .models import ParsedDoc

def non_alpha_fraction(text: str) -> float:
    if not text:
        return 1.0
    alpha = sum(c.isalpha() for c in text)
    return round(1 - alpha / len(text), 4)

def mean_words_per_sentence(text: str) -> float:
    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    if not sentences:
        return 0.0
    return round(sum(len(s.split()) for s in sentences) / len(sentences), 2)

def duplicate_line_fraction(text: str) -> float:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        return 0.0
    seen, dup = set(), 0
    for l in lines:
        if l in seen:
            dup += 1
        seen.add(l)
    return round(dup / len(lines), 4)

def type_token_ratio(text: str) -> float:
    tokens = re.findall(r"\w+", text.lower())
    if not tokens:
        return 0.0
    return round(len(set(tokens)) / len(tokens), 4)

def block_integrity(doc: ParsedDoc) -> float:
    if not doc.blocks:
        return 0.0
    good = sum(1 for b in doc.blocks if b.text.strip())
    return round(good / len(doc.blocks), 4)
