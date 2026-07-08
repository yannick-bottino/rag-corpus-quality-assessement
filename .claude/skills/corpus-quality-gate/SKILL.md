---
name: corpus-quality-gate
description: >-
  Evalue la qualite intrinseque d'un corpus documentaire avant ingestion RAG
  (score-and-flag, reference-free, document-level). Produit une fiche JSON par
  document et un rapport Excel/CSV par corpus. Utilise ce skill pour auditer un
  corpus, qualifier des documents avant RAG, ou generer une golden Q/R.
---

# Corpus Quality Gate

Outil Python `cqg`. Deux modes d'usage sur le meme coeur.

## En session (demo)
1. `pip install -e .`
2. Copier `config/config.example.yaml`, garder `provider: mock` (ou brancher un LLM).
3. `cqg run <dossier_corpus> --config config/config.example.yaml --out workdir/out`
4. Livrables dans `workdir/out/` : `<doc>.score.json`, `corpus_report.xlsx`, CSV, `corpus_redundancy.json`.

## En batch (Azure OpenAI ou autre endpoint entreprise)
Dans `config.yaml`, renseigner `llm.provider: azure_openai`, `base_url`, `model`,
et la variable d'environnement de la cle (`api_key_env`). Aucun changement de code.

## Golden Q/R
Voir `src/cqg/golden_qa.py` ; la politique de reponse est editable dans
`config/golden_qa_policy.md` (references, caveats, produit cite, etc.).
