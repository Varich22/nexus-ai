# Architecture — nexus-ai

## Vue d'ensemble

`nexus-ai` est une application agent-first : un LLM au centre, branché sur des outils concrets, exposé via une API HTTP, consommé par une UI web.

```
┌─────────────┐      ┌──────────────┐      ┌────────────────┐
│   Frontend  │ ───► │   Backend    │ ───► │  LLM Provider  │
│  (Next.js)  │ ◄─── │   (FastAPI)  │ ◄─── │  (OpenAI/etc.) │
└─────────────┘      └──────┬───────┘      └────────────────┘
                            │
                ┌───────────┼───────────┐
                ▼           ▼           ▼
          ┌──────────┐ ┌─────────┐ ┌──────────┐
          │ Tools    │ │ Memory  │ │ Storage  │
          │ registry │ │ (Chroma)│ │ (SQLite) │
          └──────────┘ └─────────┘ └──────────┘
```

## Composants

### Backend (`backend/`)

- **`app/main.py`** — point d'entrée FastAPI, monte les routes, configure CORS, gère le lifecycle (init DB, Chroma, LLM).
- **`app/core/config.py`** — settings via `pydantic-settings`, lit `.env`.
- **`app/core/logging.py`** — logging structuré JSON.
- **`app/api/`** — routes HTTP (health, chat streaming, conversations CRUD).
- **`app/agents/orchestrator.py`** — la pièce maîtresse. Reçoit un message utilisateur, gère le contexte, appelle le LLM via LiteLLM, déclenche les outils si besoin, boucle jusqu'à réponse finale, streame les tokens.
- **`app/agents/prompts.py`** — system prompts, templates.
- **`app/tools/`** — registry d'outils extensibles. Chaque outil expose :
  - `name`, `description`, `parameters` (JSON Schema)
  - `async run(**kwargs) -> str`
  - Format compatible OpenAI function calling → transmis tel quel à LiteLLM.
- **`app/services/llm.py`** — wrapper LiteLLM (streaming, completion, error handling).
- **`app/services/memory.py`** — interface mémoire haut-niveau (rappel + stockage).
- **`app/memory/vector.py`** — ChromaDB : embeddings, persistance, retrieval.
- **`app/models/`** — Pydantic schemas (API I/O) + SQLAlchemy DB models.

### Frontend (`frontend/`) — *à venir*

Stack prévu : Next.js 14 App Router + TypeScript + Tailwind + shadcn/ui.

- Page unique `/` = chat
- Streaming SSE pour affichage token-par-token
- Markdown rendering des réponses
- Panel latéral pour historique des conversations

### Outils (extensibles)

| Outil | Statut v1 | Description |
|---|---|---|
| `web_search` | ✅ | Recherche via Tavily (ou DDG fallback) |
| `web_fetch` | ✅ | Fetch + extract texte d'une URL |
| `read_file` | ✅ | Lit un fichier local |
| `write_file` | ✅ | Écrit/crée un fichier |
| `edit_file` | ✅ | Édition ciblée (find/replace) |
| `list_dir` | ✅ | Liste un dossier |
| `run_python` | ✅ | Exécute du Python en sandbox |
| `github_ops` | 🔜 | Issues, PRs, etc. |
| `memory_search` | 🔜 | Cherche dans la mémoire long-terme |
| `memory_store` | 🔜 | Stocke un fait en mémoire |

### Mémoire

Deux niveaux :

1. **Court terme** — l'historique de conversation est passé au LLM dans chaque appel.
2. **Long terme** — ChromaDB stocke des embeddings de "faits" (résumés, préférences, contexte persistant). Retrieval RAG quand le LLM en a besoin.

### Sécurité

- Clé API dans `.env` (jamais commitée)
- `.env.example` comme template
- API backend protégée par `API_KEY` (header `X-API-Key`)
- CORS configuré strict
- Exécution code en subprocess isolé avec timeout
- Pas d'eval, pas d'exec dynamique non sandboxée
- Logs structurés (pas de données sensibles loggées)

## Décisions techniques

| Choix | Raison |
|---|---|
| **FastAPI** | Async natif, écosystème IA excellent, OpenAPI auto, types stricts |
| **LiteLLM** | Abstraction multi-provider sans réécriture, retry, fallback, cost tracking |
| **Pydantic v2** | Validation/serialisation, performance, type safety |
| **ChromaDB** | Vector DB local gratuit, simple, persistant, pas d'infra |
| **SQLite (dev) → Postgres (prod)** | Zero-config local, scalable en prod |
| **httpx** | HTTP client async moderne |
| **Next.js** | SSR, écosystème, DX moderne |

## Évolutions prévues

- **Multi-agent** : un orchestrateur qui délègue à des sous-agents (researcher, coder, reviewer)
- **Auth utilisateur** : OAuth, JWT
- **Persistance cloud** : Postgres managé (Neon, Supabase free tier)
- **File d'attente tâches longues** : Celery / arq + Redis
- **MCP support** : intégrer des serveurs MCP pour étendre les outils
- **Tavily → autres providers** : Brave Search, Serper, You.com
