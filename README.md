ComplianceQAPipeline/
├── .env                              # 🔑 GCP credentials
├── .python-version                   # Python 3.12
├── pyproject.toml                    # 📦 Updated dependencies
├── main.py                           # 🚀 CLI entry point
├── backend/
│   ├── Dockerfile                    # 🐳 NEW: Cloud Run container
│   ├── data/
│   │   ├── 1001a-influencer-guide-508_1.pdf
│   │   └── youtube-ad-specs.pdf
│   ├── scripts/
│   │   └── index_documents.py        # 🔧 UPDATED: Uses Vertex AI
│   ├── tests/
│   │   ├── test_nodes.py             # 🧪 NEW: Unit tests
│   │   └── test_workflow.py          # 🧪 NEW: Integration tests
│   └── src/
│       ├── api/
│       │   ├── server.py             # 🌐 UPDATED: GCP telemetry
│       │   └── telemetry.py          # 📡 UPDATED: Cloud Trace
│       ├── graph/
│       │   ├── state.py              # 📋 UPDATED: New fields
│       │   ├── nodes.py              # ⚙️ UPDATED: Vertex AI + error nodes
│       │   └── workflow.py           # 🔄 UPDATED: Conditional edges
│       └── services/
│           └── video_intelligence.py # 🎬 NEW: Replaces video_indexer.py
└── frontend/                         # 🖥️ NEW
    └── app.py                        # Streamlit dashboard
