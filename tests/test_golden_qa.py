# tests/test_golden_qa.py
import os
from cqg.models import ParsedDoc, Block
from cqg.llm.mock import MockLLM
from cqg.golden_qa import generate_golden_qa, write_golden_qa

def test_generate_and_write(tmp_path):
    doc = ParsedDoc(doc_id="d", markdown="Le produit X couvre le risque incendie.",
                    blocks=[Block(kind="text", text="...")], parse_confidence=1.0)
    llm = MockLLM(default={"questions": [
        {"question": "Le produit X couvre-t-il l'incendie ?",
         "reponse": "Oui, le produit X couvre l'incendie.",
         "sources": "section 1", "couvert": "oui", "origine": "document"}]})
    rows = generate_golden_qa(doc, profile="gestionnaire sinistres", llm=llm, policy="POLICY")
    assert rows and rows[0]["statut_validation"] == "a_valider"
    paths = write_golden_qa(rows, str(tmp_path))
    assert os.path.exists(paths["xlsx"]) and os.path.exists(paths["csv"])

def test_uncovered_question_defaults_to_marker():
    doc = ParsedDoc(doc_id="d", markdown="x", blocks=[Block(kind="text", text="x")],
                    parse_confidence=1.0)
    llm = MockLLM(default={"questions": [{"question": "Q?", "sources": "", "origine": "profil"}]})
    rows = generate_golden_qa(doc, profile="p", llm=llm, policy="POLICY")
    assert rows[0]["couvert"] == "non"
    assert rows[0]["reponse"] == "Non couvert par le document"

def test_golden_csv_escapes_special_chars(tmp_path):
    import csv as _csvmod
    rows = [{"id": "d-1", "origine": "document", "question": "Q?",
             "reponse": "Oui; couvre incendie.\nVoir 2.1", "sources": "s1", "couvert": "oui",
             "statut_validation": "a_valider", "commentaire_beta": ""}]
    paths = write_golden_qa(rows, str(tmp_path))
    with open(paths["csv"], encoding="utf-8-sig", newline="") as f:
        parsed = list(_csvmod.reader(f, delimiter=";"))
    assert len(parsed[1]) == len(parsed[0])
    assert any("Oui; couvre incendie." in cell for cell in parsed[1])
