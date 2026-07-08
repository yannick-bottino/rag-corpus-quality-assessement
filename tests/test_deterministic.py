# tests/test_deterministic.py
from cqg.models import ParsedDoc, Block
from cqg.registry.loader import load_registry
from cqg.deterministic import compute_metrics

def test_metrics_marks_na_and_scores():
    doc = ParsedDoc(doc_id="d", markdown="Version v1.2 du 2026-01-01. " * 5,
                    blocks=[Block(kind="text", text="para")], parse_confidence=1.0)
    m = compute_metrics(doc, load_registry())
    assert "3.1" in m["na"]            # pas d'image
    assert "signals" in m and "non_alpha_fraction" in m["signals"]
    assert all(1 <= v <= 5 for v in m["d_scores"].values())
