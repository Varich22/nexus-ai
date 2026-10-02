# Frontend — *coming soon*

Stack prévu : **Next.js 14 (App Router) + TypeScript + Tailwind CSS + shadcn/ui**.

## Pages prévues

- `/` — interface de chat (streaming SSE)
- `/conversations` — historique
- `/settings` — clés API, providers, modèle

## Développement

À venir dans la prochaine itération. Le backend est déjà fonctionnel et expose :

- `GET /health`
- `POST /api/v1/chat` (mode bloquant + `stream=true` pour SSE)
- `GET /api/v1/chat/tools` (liste des outils)
- `DELETE /api/v1/conversations/{id}`

Tu peux déjà tester l'API via :
- Swagger UI : http://localhost:8000/docs
- ReDoc : http://localhost:8000/redoc
- curl / Postman / Insomnia
