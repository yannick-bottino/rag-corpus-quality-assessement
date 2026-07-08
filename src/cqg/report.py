# src/cqg/report.py
from collections import defaultdict
from .models import CriterionScore, DocScore
from .registry.loader import Registry

def _level(pct: float) -> str:
    if pct >= 90: return "Excellent"
    if pct >= 70: return "Acceptable"
    if pct >= 50: return "Insuffisant"
    return "Inadapté"

def compute_doc_score(doc_id: str, criteria: list[CriterionScore], reg: Registry,
                      parse_confidence: float, config_hash: str,
                      coverage_flag_below: float = 0.7) -> DocScore:
    by_id = {c.id: c for c in reg.criteria}
    num = defaultdict(float); den = defaultdict(float)
    for cs in criteria:
        if cs.status != "scored" or cs.score is None:
            continue
        crit = by_id.get(cs.id)
        if crit is None:  # critere hors registre : ignore plutot que crasher le batch
            continue
        dim = crit.dimension
        num[dim] += cs.weight * cs.score
        den[dim] += cs.weight * reg.scale_max
    dims = {d: round(num[d] / den[d] * 100, 1) for d in den if den[d] > 0}
    gnum = sum(reg.dimension_weights[d] * v for d, v in dims.items())
    gden = sum(reg.dimension_weights[d] for d in dims)
    global_pct = round(gnum / gden, 1) if gden else 0.0
    # Couverture coherente avec le score : un "scored" sans note (score None) ne compte pas.
    scored = sum(1 for c in criteria if c.status == "scored" and c.score is not None)
    not_eval = sum(1 for c in criteria if c.status == "not_evaluated")
    # denom nul (tout na ou liste vide) : couverture indefinie, on retourne 100.0 par convention.
    coverage = round(scored / (scored + not_eval) * 100, 1) if (scored + not_eval) else 100.0
    flags = []
    if coverage < coverage_flag_below * 100:
        flags.append("low_coverage")
    if parse_confidence < 0.5:
        flags.append("low_parse_confidence")
    return DocScore(doc_id=doc_id, global_pct=global_pct, level=_level(global_pct),
                    coverage_pct=coverage, dimensions=dims, criteria=criteria,
                    worst_sections=[], flags=flags, config_hash=config_hash)
