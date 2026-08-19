# SentinelAI-X: Autonomous AI SOC Multi-Agent Detection & Response Engine

SentinelAI-X is an autonomous Security Operations Center (SOC) platform designed for real-time threat telemetry ingestion, unsupervised ML anomaly detection, causal MITRE ATT&CK timeline reconstruction, and human-authorized incident containment.

## Key Features

* **Procedural MITRE Campaign Generator**: Simulates realistic multi-stage intrusion campaigns (Active Scanning -> Exploit -> Lateral Movement -> Exfiltration) buried under background enterprise noise.
* **Isolation Forest Anomaly Scoring**: Fast unsupervised machine learning detection layer filtering benign network traffic.
* **Autonomous Multi-Agent Crew**: Coordinated pipeline performing automated triage, MITRE ATT&CK causal mapping, and blast-radius assessment.
* **Human-in-the-Loop (HITL) Containment Gate**: Operator call-sign authorization checkpoint preventing automated false-positive outages.

## Architecture

* **Backend**: FastAPI (Python), Scikit-Learn, Pandas, NumPy, Uvicorn
* **Frontend**: React (Vite), Tailwind CSS, Lucide React Icons

## Local Setup & Run

### 1. Backend Setup
\\\ash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
\\\

### 2. Frontend Setup
\\\ash
cd frontend
npm install
npm run dev
\\\

Access the dashboard at [\http://localhost:5173\.](https://sentinel-ai-x-chi.vercel.app)
