# src/cqg/judge.py
from .models import CriterionScore, ParsedDoc
from .registry.loader import Registry
from .llm.base import LLMClient

_SCHEMA = {"type": "object", "required": ["status", "justification"]}

def _representative_excerpt(markdown: str, budget: int = 24000) -> str:
    # Jugement document-level : au lieu de tronquer au debut, on echantillonne tout le
    # document. Si le doc tient dans le budget, on le rend entier ; sinon on prend une tete
    # substantielle + des fenetres reparties sur le reste, separees par un marqueur.
    if len(markdown) <= budget:
        return markdown
    head = int(budget * 0.5)
    rest_budget = budget - head
    parts = [markdown[:head]]
    remaining = markdown[head:]
    n = 4  # nombre de fenetres reparties
    win = max(1, rest_budget // n)
    # Les fenetres sont reparties de facon a ce que la derniere colle exactement a la fin de
    # `remaining` : sinon la toute fin du document n'est jamais echantillonnee.
    span = max(1, len(remaining) - win)
    for i in range(n):
        start = (span * i) // max(1, n - 1) if n > 1 else 0
        parts.append("\n[...]\n" + remaining[start:start + win])
    return "".join(parts)

def _prompt(doc: ParsedDoc, crit, signal_hint, max_doc_chars: int = 24000) -> str:
    return (
        "Tu evalues la qualite d'un document pour un systeme RAG. Note SECTION par section.\n"
        f"Critere {crit.id} ({crit.label}). Echelle 1 a 5 (3 = partiellement satisfaisant).\n"
        "Si tu ne peux pas evaluer de facon fiable, retourne status=not_evaluated et explique pourquoi. "
        "Ne devine jamais une note.\n"
        f"Signal deterministe disponible: {signal_hint}\n"
        "Reponds en JSON: {status: scored|not_evaluated, score: 1-5 ou null, "
        "justification: une phrase, evidence: citation/section ou null}.\n\n"
        f"Contenu:\n{_representative_excerpt(doc.markdown, max_doc_chars)}"
    )

def score_document(doc: ParsedDoc, reg: Registry, metrics: dict,
                   llm: LLMClient, config_hash: str, max_doc_chars: int = 24000) -> list[CriterionScore]:
    na = set(metrics.get("na", []))
    d_scores = metrics.get("d_scores", {})
    h_signals = metrics.get("h_signals", {})
    out: list[CriterionScore] = []
    for crit in reg.criteria:
        base = dict(id=crit.id, tag=crit.tag, weight=crit.weight)
        if crit.id in na:
            out.append(CriterionScore(**base, status="na", score=None,
                                      justification="Objet absent du document (inventaire).",
                                      evidence=None))
            continue
        if crit.external_dep:
            out.append(CriterionScore(**base, status="not_evaluated", score=None,
                                      justification="Referentiel de questions/cas d'usage absent.",
                                      evidence=None))
            continue
        if crit.tag == "D" and crit.id in d_scores:
            out.append(CriterionScore(**base, status="scored", score=int(d_scores[crit.id]),
                                      justification="Signal deterministe.", evidence=None))
            continue
        resp = llm.judge(_prompt(doc, crit, h_signals.get(crit.id), max_doc_chars), _SCHEMA)
        status = resp.get("status", "not_evaluated")
        justification = (resp.get("justification") or "").strip()
        score = resp.get("score") if status == "scored" else None
        # Anti-fabrication : la SEULE voie vers "scored" est une note entiere valide dans le
        # bareme AVEC justification. Tout le reste (score manquant/hors bareme/non entier,
        # justification vide, "na" renvoye par le LLM, statut inconnu) est demote en not_evaluated.
        valid_scored = (
            status == "scored"
            and isinstance(score, int) and not isinstance(score, bool)
            and 1 <= score <= reg.scale_max
            and bool(justification)
        )
        if valid_scored:
            final_status, final_score = "scored", score
        else:
            final_status, final_score = "not_evaluated", None
            if status == "scored":
                reason = "Non evalue: reponse LLM 'scored' non conforme (score ou justification invalide)."
                justification = f"{reason} {justification}".strip() if justification else reason
            elif not justification:
                justification = "Non evalue: reponse LLM incomplete."
        out.append(CriterionScore(**base, status=final_status, score=final_score,
                                  justification=justification, evidence=resp.get("evidence")))
    return out
