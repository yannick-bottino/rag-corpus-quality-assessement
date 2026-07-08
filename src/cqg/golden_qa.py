# src/cqg/golden_qa.py
import csv
from pathlib import Path
from openpyxl import Workbook
from .models import ParsedDoc
from .llm.base import LLMClient
from .report import _sanitize_cell

_COLS = ["id", "origine", "question", "reponse", "sources", "couvert",
         "statut_validation", "commentaire_beta"]

def _prompt(doc: ParsedDoc, profile: str, policy: str) -> str:
    return (
        "Genere un jeu de questions/reponses de reference (golden set) pour ce profil utilisateur.\n"
        f"Profil: {profile}\n"
        "Regle absolue: ne fabrique aucune reponse absente du document. Si non couvert, "
        "reponse='Non couvert par le document', couvert='non'.\n"
        f"Politique de reponse a respecter:\n{policy}\n"
        "Reponds en JSON: {questions: [{question, reponse, sources, couvert (oui|non), origine (profil|document)}]}\n\n"
        f"Document:\n{doc.markdown[:6000]}"
    )

def generate_golden_qa(doc: ParsedDoc, profile: str, llm: LLMClient, policy: str) -> list[dict]:
    resp = llm.judge(_prompt(doc, profile, policy), {"type": "object"})
    rows = []
    for i, q in enumerate(resp.get("questions", []), start=1):
        # Anti-fabrication : seule une reponse explicitement couverte ("oui") ET non vide est
        # conservee ; tout le reste bascule sur le marqueur "Non couvert par le document".
        couvert = (q.get("couvert") or "non").strip().lower()
        reponse = (q.get("reponse") or "").strip()
        if couvert != "oui" or not reponse:
            couvert, reponse = "non", "Non couvert par le document"
        rows.append({
            "id": f"{doc.doc_id}-{i}",
            "origine": q.get("origine", "document"),
            "question": q.get("question", ""),
            "reponse": reponse,
            "sources": q.get("sources", ""),
            "couvert": couvert,
            "statut_validation": "a_valider",
            "commentaire_beta": "",
        })
    return rows

def write_golden_qa(rows: list[dict], out_dir: str) -> dict:
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    wb = Workbook(); ws = wb.active; ws.title = "golden_qa"
    ws.append(_COLS)
    for r in rows:
        ws.append([_sanitize_cell(r[c]) for c in _COLS])
    xlsx = out / "golden_qa.xlsx"; wb.save(xlsx)
    csv_path = out / "golden_qa.csv"
    # csv.writer echappe ; guillemets et retours ligne ; utf-8-sig pour les accents dans Excel.
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(_COLS)
        for r in rows:
            writer.writerow([_sanitize_cell(r[c]) for c in _COLS])
    return {"xlsx": str(xlsx), "csv": str(csv_path)}
