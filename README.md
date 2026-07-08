# Corpus Quality Gate (cqg)

Quality gate for document corpora before RAG ingestion (score-and-flag, reference-free, document-level).

## Contexte

Evalue la qualite intrinseque d'un corpus documentaire heterogene (FR/EN, multimodal) avant chunking et embedding : score et flag les documents faibles pour revue humaine, ne supprime jamais en silence.

## Installation

```bash
python -m venv .venv
source .venv/Scripts/activate  # Windows Git Bash
pip install -e ".[dev]"
```

## Licences

Dependances autorisees : MIT / Apache-2.0 / BSD uniquement.
Bannies (licences AGPL / non commerciales) : `pyiqa`, `marker-pdf`, `maverick-coref`, `pymupdf4llm`, `pymupdf`.

Verification :

```bash
python scripts/check_licenses.py
```

## Tests

```bash
python -m pytest -v
```

## Statut

Projet en construction (fondation posee : packaging, gate de licences, CI).
