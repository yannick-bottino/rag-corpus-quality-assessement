# tests/test_signals.py
from cqg.signals import non_alpha_fraction, duplicate_line_fraction, block_integrity
from cqg.models import ParsedDoc, Block

def test_non_alpha_fraction():
    assert non_alpha_fraction("abc123") == 0.5

def test_duplicate_line_fraction():
    txt = "ligne a\nligne a\nligne b"
    assert round(duplicate_line_fraction(txt), 2) == 0.33

def test_block_integrity_all_good():
    doc = ParsedDoc(doc_id="d", markdown="x",
                    blocks=[Block(kind="text", text="ok"), Block(kind="text", text="ok2")],
                    parse_confidence=1.0)
    assert block_integrity(doc) == 1.0
