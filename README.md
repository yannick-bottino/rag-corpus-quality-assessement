# Corpus Quality Gate (cqg)

Quality gate for document corpora before RAG ingestion (score-and-flag, reference-free, document-level).

## Contexte

Evalue la qualite intrinseque d'un corpus documentaire heterogene (FR/EN, multimodal) avant chunking et embedding : score et flag les documents faibles pour revue humaine, ne supprime jamais en silence. L'outil ne requiert ni ground truth ni jeu de requetes : chaque document est note independamment, puis les scores sont agreges au niveau du corpus.

## Installation

```bash
python -m venv .venv
source .venv/Scripts/activate  # Windows Git Bash
pip install -e ".[dev]"
```

Extras optionnels selon le fournisseur LLM branche (voir plus bas) :

```bash
pip install -e ".[openai]"      # provider openai ou azure_openai
pip install -e ".[anthropic]"   # provider anthropic
```

## Usage

```bash
cqg run <dossier_corpus> --config config/config.example.yaml --out workdir/out
```

- `<dossier_corpus>` : dossier contenant les documents a evaluer (PDF numeriques ; pas d'OCR).
- `--config` : fichier de configuration YAML (voir `config/config.example.yaml`).
- `--out` : dossier de sortie (cree automatiquement si absent).

Chaque document est triage, parse, mesure sur des signaux deterministes (integrite des blocs,
completude des references), puis juge par le LLM configure sur les criteres qualitatifs du
registre. Un document en echec de traitement est signale (`processing_error`) et note au
niveau minimal : il n'interrompt jamais le traitement du reste du corpus.

## Structure des sorties

Dans `--out` :

| Fichier | Contenu |
|---|---|
| `<doc_id>.score.json` | Fiche de score complete par document (score global, niveau, couverture, score par critere, justification, preuve, flags) |
| `corpus_report.xlsx` | Classeur a 3 onglets : `Synthese` (un document par ligne), `Detail` (un critere par ligne), `Remediation` (criteres notes <= 2, tries par poids decroissant) |
| `synthese.csv`, `detail.csv`, `remediation.csv` | Export CSV (`;`, UTF-8 avec BOM) de chaque onglet, pour outillage externe |
| `corpus_redundancy.json` | Detection de redondance entre documents au niveau corpus |

Chaque fiche de score porte un `config_hash` (empreinte de la configuration LLM, des seuils, de
la version du registre de criteres et de la version de la politique de reponse) : deux runs avec
le meme hash sont reproductibles a l'identique, un changement de hash signale une configuration
differente entre deux runs.

## Branchement LLM entreprise

Le coeur de l'outil est agnostique du fournisseur LLM. La configuration se fait entierement via
`config.yaml`, sans modification de code :

```yaml
llm:
  provider: azure_openai        # mock | openai | azure_openai | anthropic
  base_url: "https://<endpoint-entreprise>"
  model: "<nom-du-deploiement>"
  temperature: 0
  api_key_env: "CQG_LLM_API_KEY"
```

- `provider: mock` : aucun appel reseau, utilise pour les tests et la demo en session.
- `provider: openai` / `azure_openai` : passe par le SDK `openai` (extra `.[openai]`).
- `provider: anthropic` : passe par le SDK `anthropic` (extra `.[anthropic]`).
- La cle d'API n'est jamais lue depuis le fichier de configuration : `api_key_env` designe le nom
  d'une variable d'environnement (ex. `export CQG_LLM_API_KEY=...`) lue au runtime. Aucune cle en
  clair ne doit figurer dans `config.yaml` ni etre committee.
- `base_url` pointe vers l'endpoint entreprise (par exemple un deploiement Azure OpenAI, ou tout
  autre fournisseur compatible OpenAI / Anthropic) : le meme pipeline tourne en session interactive
  et en batch, seul `config.yaml` change.

## Golden Q/R

`cqg` peut generer, par document, un jeu de questions/reponses de reference a partir du contenu
reellement present dans le document (voir `src/cqg/golden_qa.py`). Regle anti-fabrication stricte :
toute question non explicitement couverte par le document recoit la reponse
"Non couvert par le document" plutot qu'une reponse inventee.

La politique de reponse (ton, exigence de citer les references et le produit concerne, gestion des
caveats) est editable par les equipes metier dans `config/golden_qa_policy.md`, sans toucher au
code.

## Licences

Dependances autorisees : MIT / Apache-2.0 / BSD uniquement.
Bannies (licences AGPL / non commerciales) : `pyiqa`, `marker-pdf`, `maverick-coref`, `pymupdf4llm`, `pymupdf`.

Verification (gate de licences, executee aussi en CI) :

```bash
python scripts/check_licenses.py
```

Le script echoue (code de sortie 1) si une dependance bannie est detectee dans l'environnement
installe.

## Tests

```bash
python -m pytest -v
```

## Statut

Pipeline complet de bout en bout (`cqg run`) : triage, parsing, signaux deterministes, jugement
LLM, agregation des scores, rapport Excel/CSV, detection de redondance corpus, generation de
golden Q/R. Packaging, gate de licences et CI en place.
