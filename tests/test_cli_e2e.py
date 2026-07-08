import os, json
from cqg.cli import run

def test_end_to_end(tmp_path):
    from reportlab.pdfgen import canvas
    corpus = tmp_path / "corpus"; corpus.mkdir()
    for name in ("a.pdf", "b.pdf"):
        c = canvas.Canvas(str(corpus / name))
        to = c.beginText(72, 800)
        for _ in range(30):
            to.textLine("Version v1.0 du 2026-01-01.")
        c.drawText(to); c.showPage(); c.save()
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("llm:\n  provider: mock\n  temperature: 0\npaths:\n  workdir: ./wd\n"
                   "thresholds:\n  coverage_flag_below: 0.7\n", encoding="utf-8")
    out = tmp_path / "out"
    paths = run(str(corpus), str(cfg), str(out))
    assert os.path.exists(paths["corpus_report"]["xlsx"])
    assert os.path.exists(out / "a.score.json")
    data = json.loads((out / "a.score.json").read_text(encoding="utf-8"))
    assert data["config_hash"] and "level" in data


def test_run_isolates_and_flags_bad_document(tmp_path):
    from reportlab.pdfgen import canvas
    corpus = tmp_path / "corpus"; corpus.mkdir()
    c = canvas.Canvas(str(corpus / "good.pdf")); to = c.beginText(72, 800)
    for _ in range(30):
        to.textLine("Version v1.0 du 2026-01-01.")
    c.drawText(to); c.showPage(); c.save()
    (corpus / "bad.txt").write_text("ceci n'est pas un pdf", encoding="utf-8")
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("llm:\n  provider: mock\nthresholds:\n  coverage_flag_below: 0.7\n", encoding="utf-8")
    out = tmp_path / "out"
    result = run(str(corpus), str(cfg), str(out))
    assert result["n_docs"] == 2
    assert result["n_errors"] >= 1
    bad = json.loads((out / "bad.score.json").read_text(encoding="utf-8"))
    assert any("processing_error" in f for f in bad["flags"])
