Hackathon/
├── backend/
│   ├── main.py              ← FastAPI app entry point
│   ├── database.py          ← Firebase connection + Mock fallback
│   ├── models.py            ← Pydantic schemas
│   ├── auth_utils.py        ← JWT authentication
│   ├── sentiment.py         ← Sentiment analysis engine
│   ├── requirements.txt     ← Python dependencies
│   ├── .env.example         ← Environment variables template
│   └── routers/
│       ├── auth.py          ← /api/auth  (register, login, me)
│       ├── chat.py          ← /api/chat  (send, history, clear)
│       └── crisis.py        ← /api/crisis (logs, helplines)
└── frontend/
    └── templates/
        └── index.html       ← Full frontend (single file)
```
