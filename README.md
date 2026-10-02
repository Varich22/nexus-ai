# 🤖 nexus-ai

> Assistant IA polyvalent, open et auto-hébergeable — recherche, code, contenu, fichiers, automatisation.

[![Status](https://img.shields.io/badge/status-MVP-orange)](#)
[![License](https://img.shields.io/badge/license-MIT-blue)](#)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](#)
[![Node](https://img.shields.io/badge/node-20%2B-green)](#)

## ✨ Capacités

- 💬 **Chat conversationnel** avec streaming token-par-token
- 🔍 **Recherche web** en profondeur (Tavily / DuckDuckGo)
- 🌐 **Fetch et extraction** de pages web
- 📁 **Lecture / écriture / édition** de fichiers
- 💻 **Exécution de code** Python sécurisée (sandbox)
- 🐙 **Opérations GitHub** (issues, PRs, repos)
- 🧠 **Mémoire vectorielle** persistante (ChromaDB)
- 🔌 **Multi-provider LLM** via LiteLLM (OpenAI, Anthropic, Ollama, Mistral, ...)

## 🏗️ Architecture

Monorepo :

- **`backend/`** — API FastAPI + agent orchestrateur + outils
- **`frontend/`** — UI Next.js (chat moderne, streaming)
- **`docs/``** — Documentation architecture & décisions

```
nexus-ai/
├── backend/          # Python 3.11+, FastAPI, LiteLLM, ChromaDB
├── frontend/         # Next.js 14, TypeScript, Tailwind, shadcn/ui
├── docs/             # Architecture, guides
└── .github/          # CI workflows
```

Voir [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) pour le détail complet.

## 🚀 Démarrage rapide

### Pré-requis

- **Python 3.11+**
- **Node 20+**
- **Docker** (optionnel, recommandé)
- Une **clé API** pour au moins un provider LLM (OpenAI, Anthropic, ou Ollama local)

### Installation

```bash
# 1. Cloner le repo
git clone https://github.com/Varich22/nexus-ai.git
cd nexus-ai

# 2. Configurer l'environnement
cp .env.example .env
# Éditer .env et mettre ta OPENAI_API_KEY (ou autre provider)

# 3. Lancer en local (mode dev)
docker compose up

# OU lancer séparément :
# Backend
cd backend && pip install -e ".[dev]" && uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm install && npm run dev
```

L'API sera sur `http://localhost:8000` (Swagger : `/docs`)
Le frontend sera sur `http://localhost:3000`

## ⚙️ Configuration

Toutes les variables d'env sont dans `.env.example`. Les principales :

| Variable | Description | Défaut |
|---|---|---|
| `OPENAI_API_KEY` | Clé API OpenAI (ou provider équivalent) | — |
| `LLM_MODEL` | Modèle à utiliser | `gpt-4o-mini` |
| `DATABASE_URL` | URL de la base SQL | `sqlite:///./nexus.db` |
| `CHROMA_PERSIST_DIR` | Dossier persistance ChromaDB | `./chroma` |
| `LOG_LEVEL` | Niveau de log | `INFO` |
| `CORS_ORIGINS` | Origins autorisées (CSV) | `http://localhost:3000` |

## 🧪 Tests

```bash
cd backend
pytest                    # Tests unitaires
pytest --cov=app          # Avec coverage
ruff check .              # Lint
ruff format .             # Format
```

## 🛣️ Roadmap

- [x] Backend FastAPI avec LiteLLM
- [x] Agent orchestrateur avec tool calling
- [x] Outils : web search, fetch, file ops, code execution
- [x] Mémoire vectorielle ChromaDB
- [ ] Frontend Next.js avec chat streaming
- [ ] Auth utilisateur (API key + OAuth)
- [ ] Persistance conversations (Postgres)
- [ ] Plus d'outils (calendar, email, Notion, etc.)
- [ ] Mode multi-agent (researcher + coder + reviewer)

## 📜 License

MIT

## 🤝 Contribution

PRs bienvenues. Pour les changements majeurs, ouvre d'abord une issue.
