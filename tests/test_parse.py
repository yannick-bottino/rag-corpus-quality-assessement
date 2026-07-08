from cqg.parse import parse_document


def test_pypdf_fallback_extracts_text(tmp_path, monkeypatch):
    from reportlab.pdfgen import canvas
    p = tmp_path / "d.pdf"
    c = canvas.Canvas(str(p))
    to = c.beginText(72, 800)
    for _ in range(20):
        to.textLine("Bonjour le monde.")
    c.drawText(to); c.showPage(); c.save()
    monkeypatch.setattr("cqg.parse._docling_available", lambda: False)
    doc = parse_document(str(p), "born_digital")
    assert "Bonjour" in doc.markdown
    assert 0.0 <= doc.parse_confidence <= 1.0
    assert len(doc.blocks) >= 1
