import argparse
from pathlib import Path
from .config import load_config, config_hash
from .registry.loader import load_registry
from .triage import triage_corpus
from .parse import parse_document
from .deterministic import compute_metrics
from .llm.base import from_config
from .judge import score_document
from .report import compute_doc_score, write_doc_json, write_corpus_report
from .redundancy import corpus_redundancy
from .models import DocScore
import json

def run(corpus_dir: str, config_path: str, out_dir: str) -> dict:
    cfg = load_config(config_path)
    reg = load_registry()
    llm = from_config(cfg.get("llm", {"provider": "mock"}))
    chash = config_hash(cfg, registry_version="v1", policy_version="v1")
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    threshold = cfg.get("thresholds", {}).get("coverage_flag_below", 0.7)
    scores, parsed, errors = [], [], []
    for item in triage_corpus(corpus_dir):
        doc_id = item["doc_id"]
        try:
            doc = parse_document(item["path"], item["category"])
            parsed.append((doc.doc_id, doc.markdown))
            metrics = compute_metrics(doc, reg)
            criteria = score_document(doc, reg, metrics, llm, chash)
            ds = compute_doc_score(doc.doc_id, criteria, reg, doc.parse_confidence, chash, threshold)
        except Exception as exc:
            # Score-and-flag : un document en echec est signale pour revue humaine, jamais
            # abandonne en silence et ne fait jamais tomber le reste du corpus.
            ds = DocScore(doc_id=doc_id, global_pct=0.0, level="Inadapte", coverage_pct=0.0,
                          dimensions={}, criteria=[], worst_sections=[],
                          flags=[f"processing_error: {type(exc).__name__}"], config_hash=chash)
            errors.append({"doc_id": doc_id, "error": f"{type(exc).__name__}: {exc}"})
        write_doc_json(ds, str(out))
        scores.append(ds)
    report = write_corpus_report(scores, reg, str(out))
    redundancy = corpus_redundancy(parsed)
    (out / "corpus_redundancy.json").write_text(
        json.dumps(redundancy, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"corpus_report": report, "n_docs": len(scores), "n_errors": len(errors),
            "errors": errors, "redundancy": str(out / "corpus_redundancy.json")}

def main() -> int:
    parser = argparse.ArgumentParser(prog="cqg")
    parser.add_argument("command", choices=["run"])
    parser.add_argument("corpus")
    parser.add_argument("--config", default="config/config.example.yaml")
    parser.add_argument("--out", default="./workdir/out")
    args = parser.parse_args()
    if args.command == "run":
        result = run(args.corpus, args.config, args.out)
        print(f"Termine: {result['n_docs']} documents. Rapport: {result['corpus_report']['xlsx']}")
    return 0
