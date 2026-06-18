# AI Video Brand Guardrail

[![GitHub stars](https://img.shields.io/github/stars/krishnasahu29/AI-Video-Brand-Guardrail.svg)](https://github.com/krishnasahu29/AI-Video-Brand-Guardrail/stargazers)
[![License](https://img.shields.io/github/license/krishnasahu29/AI-Video-Brand-Guardrail.svg)](https://github.com/krishnasahu29/AI-Video-Brand-Guardrail/blob/master/LICENSE)

## Overview

The **Compliance QA Pipeline** is an open‑source, AI‑powered solution that automatically audits video content for brand‑compliance violations. It ingests a YouTube URL, extracts speech & OCR, indexes the content, and runs a LangGraph workflow powered by LLMs to detect policy breaches, producing a concise compliance report.

> *"AI‑driven brand guardian – keep your videos safe, compliant, and on‑brand."*

## Key Features

* **End‑to‑end workflow** using **LangGraph**: `START` → `Indexer` → `Auditor` → `END`.
* **FastAPI** REST API (`/audit`, `/health`).
* **Azure Monitor OpenTelemetry** + **OpenAI/GenAI instrumentation** for full observability.
* **Docker‑ready** (can be containerized for production).
* **Modular architecture** – easy to add new rule‑sets or video platforms.
* **Comprehensive CLI** (`python main.py`) for quick local testing.

## Architecture

```mermaid
flowchart TD
    A[Client (CLI / HTTP)] --> B[FastAPI Server]
    B --> C[LangGraph Workflow]
    C --> D[Indexer Node]
    D --> E[Auditor Node]
    E --> F[Report Generation]
    
    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#bbf,stroke:#333,stroke-width:2px
    style C fill:#bfb,stroke:#333,stroke-width:2px
    style D fill:#ff9,stroke:#333,stroke-width:2px
    style E fill:#ff9,stroke:#333,stroke-width:2px
    style F fill:#9f9,stroke:#333,stroke-width:2px

```

## Quick Start

### Prerequisites

* Python **3.12** or later
* `git`
* Azure Application Insights connection string (optional for telemetry)
* OpenAI API Key

### Installation

```bash
# Clone the repo
git clone [https://github.com/krishnasahu29/AI-Video-Brand-Guardrail.git](https://github.com/krishnasahu29/AI-Video-Brand-Guardrail.git)
cd AI-Video-Brand-Guardrail

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

```

### Configuration

Create a `.env` file in the project root:

```env
# OpenAI API key
OPENAI_API_KEY=sk-****************

# Azure Application Insights (optional)
APPLICATIONINSIGHTS_CONNECTION_STRING=InstrumentationKey=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx;IngestionEndpoint=https://....

```

### Run the API Server

```bash
uvicorn backend.src.api.server:app --reload

```

The server will be available at `http://127.0.0.1:8000`.

### Run the CLI Demo

```bash
python main.py

```

You will see the simulated audit of a YouTube video and a formatted compliance report.

---

## API Usage

### Submit an Audit Request

```bash
curl -X POST [http://127.0.0.1:8000/audit](http://127.0.0.1:8000/audit) \
     -H "Content-Type: application/json" \
     -d '{"video_url": "[https://youtu.be/dT7S75eYhcQ](https://youtu.be/dT7S75eYhcQ)"}'

```

**Response Schema** (`AuditResponse`):

```json
{
  "session_id": "string",
  "video_id": "string",
  "status": "PASS | FAIL",
  "compliance_results": [
    {
      "category": "string",
      "severity": "HIGH | MEDIUM | LOW",
      "description": "string"
    }
  ],
  "final_report": "string"
}

```

### Health Check

```bash
curl [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

```

---

## Telemetry & Observability

The `setup_telemetry()` function in `backend/src/api/telemetry.py` automatically configures:

* **Azure Monitor** (distributed tracing, HTTP, DB, exception, performance metrics).
* **OpenAI/GenAI instrumentation** – each LLM call is recorded with the *GenAI Semantic Conventions* and appears in the *Agents (preview)* dashboard.
* All logs are emitted via the standard logging module.

> 💡 **Tip:** If the `APPLICATIONINSIGHTS_CONNECTION_STRING` is missing, telemetry is gracefully disabled and a warning is logged.

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feat/your-feature`).
3. Write tests and ensure they pass (`pytest`).
4. Open a Pull Request with a clear description.
5. Follow the code‑style guidelines (Black, flake8).

## License

This project is licensed under the **MIT License** – see the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.

*Built with 💙 by the Agentic AI Stack community.*

```

```
