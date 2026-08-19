import os

files = {
    '.env.example': '''OPENAI_API_KEY=your_openai_api_key_here
JWT_SECRET=supersecret_soc_jwt_key_here
PORT=8000
''',
    'docker-compose.yml': '''version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - .env.example
    volumes:
      - ./backend:/app

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - /app/node_modules
''',
    'backend/Dockerfile': '''FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
''',
    'backend/requirements.txt': '''fastapi>=0.110.0
uvicorn>=0.28.0
scikit-learn>=1.4.0
pandas>=2.2.0
numpy>=1.26.0
pydantic>=2.6.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
reportlab>=4.1.0
openai>=1.14.0
python-dotenv>=1.0.1
''',
    'backend/app/__init__.py': '',
    'backend/app/main.py': '''from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.engine.campaign_generator import generate_telemetry_stream
from app.engine.ml_detector import SecurityAnomalyDetector

app = FastAPI(title="SentinelAI-X SOC Engine", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

detector = SecurityAnomalyDetector()

class ApprovalRequest(BaseModel):
    incident_id: str
    approved: bool
    approved_by: str

@app.post("/api/campaign/simulate")
async def trigger_simulation():
    raw_logs = generate_telemetry_stream(num_noise=45, inject_campaign=True)
    anomalies = detector.fit_predict(raw_logs)
    return {"total_events": len(raw_logs), "flagged_anomalies": len(anomalies), "anomalies": anomalies}

@app.post("/api/containment/authorize")
async def authorize_containment(req: ApprovalRequest):
    if not req.approved:
        return {"status": "REJECTED", "message": f"Containment rejected by operator {req.approved_by}"}
    return {
        "status": "EXECUTED",
        "incident_id": req.incident_id,
        "actions_taken": ["Host 10.0.4.15 isolated at switch level", "Attacker IP blocked on perimeter edge firewall"],
        "timestamp": "2026-08-19T15:20:00Z"
    }
''',
    'backend/app/engine/__init__.py': '',
    'backend/app/engine/campaign_generator.py': '''import random
from datetime import datetime, timezone
import uuid

ATTACK_STAGES = [
    {
        "stage": "Reconnaissance",
        "technique_id": "T1595",
        "technique_name": "Active Scanning",
        "events": [
            {"action": "port_scan", "proto": "TCP", "dest_port": 445, "status": "REJECT"},
            {"action": "vulnerability_sweep", "proto": "HTTP", "dest_port": 8080, "status": "404"}
        ]
    },
    {
        "stage": "Initial Access",
        "technique_id": "T1190",
        "technique_name": "Exploit Public-Facing App",
        "events": [
            {"action": "web_exploit", "proto": "HTTP", "dest_port": 443, "status": "200", "bytes_out": 4096}
        ]
    },
    {
        "stage": "Lateral Movement",
        "technique_id": "T1021.002",
        "technique_name": "SMB/Windows Admin Shares",
        "events": [
            {"action": "smb_exec", "proto": "SMB", "dest_port": 445, "status": "SUCCESS", "bytes_out": 8200}
        ]
    },
    {
        "stage": "Exfiltration",
        "technique_id": "T1048",
        "technique_name": "Exfiltration Over Alt Protocol",
        "events": [
            {"action": "dns_tunnel", "proto": "DNS", "dest_port": 53, "status": "SUCCESS", "bytes_out": 245000}
        ]
    }
]

def generate_telemetry_stream(num_noise: int = 40, inject_campaign: bool = True):
    logs = []
    campaign_id = str(uuid.uuid4())[:8]
    attacker_ip = f"198.51.100.{random.randint(10, 99)}"
    victim_ip = "10.0.4.15"

    for _ in range(num_noise):
        logs.append({
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "src_ip": f"10.0.1.{random.randint(1, 254)}",
            "dest_ip": f"10.0.2.{random.randint(1, 254)}",
            "proto": random.choice(["TCP", "UDP", "HTTPS", "DNS"]),
            "dest_port": random.choice([80, 443, 53, 22]),
            "bytes_out": random.randint(100, 2500),
            "status": "ALLOW",
            "is_anomaly": 0
        })

    if inject_campaign:
        for idx, stage in enumerate(ATTACK_STAGES):
            for ev in stage["events"]:
                logs.append({
                    "id": str(uuid.uuid4()),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "src_ip": attacker_ip if idx < 2 else victim_ip,
                    "dest_ip": victim_ip if idx < 2 else f"10.0.8.{random.randint(2, 50)}",
                    "proto": ev["proto"],
                    "dest_port": ev["dest_port"],
                    "bytes_out": ev.get("bytes_out", random.randint(3000, 80000)),
                    "status": ev["status"],
                    "campaign_tag": campaign_id,
                    "mitre_technique": stage["technique_id"],
                    "stage": stage["stage"],
                    "is_anomaly": 1
                })

    random.shuffle(logs)
    return logs
''',
    'backend/app/engine/ml_detector.py': '''import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

class SecurityAnomalyDetector:
    def __init__(self, contamination: float = 0.08):
        self.model = IsolationForest(contamination=contamination, random_state=42)

    def extract_features(self, logs: list[dict]) -> pd.DataFrame:
        df = pd.DataFrame(logs)
        df['port_norm'] = df['dest_port'] / 65535.0
        df['bytes_norm'] = np.log1p(df['bytes_out'])
        df['proto_cat'] = df['proto'].astype('category').cat.codes
        return df[['port_norm', 'bytes_norm', 'proto_cat']]

    def fit_predict(self, logs: list[dict]):
        features = self.extract_features(logs)
        self.model.fit(features)
        preds = self.model.predict(features)
        return [logs[i] for i, pred in enumerate(preds) if pred == -1]
''',
    'frontend/package.json': '''{
  "name": "sentinel-ai-x-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "axios": "^1.6.8",
    "lucide-react": "^0.359.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.66",
    "@types/react-dom": "^18.2.22",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.38",
    "tailwindcss": "^3.4.1",
    "vite": "^5.1.6"
  }
}
''',
    'frontend/vite.config.js': '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})
''',
    'frontend/tailwind.config.js': '''/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
''',
    'frontend/postcss.config.js': '''export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
''',
    'frontend/index.html': '''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>SentinelAI-X SOC</title>
  </head>
  <body class="bg-slate-950 text-slate-100">
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
''',
    'frontend/src/index.css': '''@tailwind base;
@tailwind components;
@tailwind utilities;

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.6);
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(51, 65, 85, 0.8);
  border-radius: 4px;
}
''',
    'frontend/src/main.jsx': '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
''',
    'frontend/src/components/LiveFeed.jsx': '''import React from 'react';
import { Activity, ShieldAlert, CheckCircle2, Wifi } from 'lucide-react';

export default function LiveFeed({ logs = [] }) {
  return (
    <div className="flex flex-col h-full bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
      <div className="flex items-center justify-between px-4 py-3 bg-slate-950/80 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-emerald-400 animate-pulse" />
          <h2 className="font-semibold text-sm tracking-wide text-slate-100 uppercase">
            Real-Time Telemetry Stream
          </h2>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
          <span>Ingesting</span>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto font-mono text-xs divide-y divide-slate-800/60 custom-scrollbar">
        {logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500 p-8">
            <Wifi className="w-8 h-8 mb-2 stroke-[1.5] text-slate-600" />
            <p>Awaiting incoming network telemetry...</p>
          </div>
        ) : (
          logs.map((log) => {
            const isAnomaly = log.is_anomaly === 1 || log.is_anomaly === -1;
            return (
              <div
                key={log.id}
                className={`flex items-center justify-between px-4 py-2.5 transition-colors ${
                  isAnomaly
                    ? 'bg-rose-950/30 hover:bg-rose-900/40 text-rose-200 border-l-2 border-rose-500'
                    : 'hover:bg-slate-800/40 text-slate-300'
                }`}
              >
                <div className="flex items-center gap-3 min-w-0">
                  {isAnomaly ? (
                    <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0" />
                  ) : (
                    <CheckCircle2 className="w-4 h-4 text-slate-600 shrink-0" />
                  )}
                  <span className="text-slate-500 shrink-0">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </span>
                  <span className="font-semibold text-slate-200 truncate">
                    {log.src_ip}:{log.dest_port}
                  </span>
                  <span className="text-slate-500">→</span>
                  <span className="truncate text-slate-400">{log.dest_ip}</span>
                </div>
                <div className="flex items-center gap-3 shrink-0 ml-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700">
                    {log.proto}
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                      isAnomaly
                        ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                        : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    }`}
                  >
                    {isAnomaly ? (log.mitre_technique || 'ANOMALY') : log.status}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
''',
    'frontend/src/components/AttackTimeline.jsx': '''import React from 'react';
import { GitCommit, Layers, Terminal, ArrowRight } from 'lucide-react';

const STAGE_COLORS = {
  Reconnaissance: 'border-amber-500 text-amber-400 bg-amber-950/20',
  'Initial Access': 'border-orange-500 text-orange-400 bg-orange-950/20',
  'Lateral Movement': 'border-rose-500 text-rose-400 bg-rose-950/20',
  Exfiltration: 'border-red-600 text-red-400 bg-red-950/30',
};

export default function AttackTimeline({ stages = [] }) {
  return (
    <div className="flex flex-col h-full bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
      <div className="flex items-center justify-between px-4 py-3 bg-slate-950/80 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Layers className="w-5 h-5 text-indigo-400" />
          <h2 className="font-semibold text-sm tracking-wide text-slate-100 uppercase">
            MITRE ATT&CK Causal Timeline
          </h2>
        </div>
        <span className="text-xs text-slate-400 font-mono">
          {stages.length} Stage{stages.length !== 1 ? 's' : ''} Correlated
        </span>
      </div>
      <div className="flex-1 overflow-y-auto p-5 space-y-6 custom-scrollbar">
        {stages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500">
            <GitCommit className="w-8 h-8 mb-2 stroke-[1.5] text-slate-600" />
            <p className="text-sm">No active multi-stage campaign identified.</p>
          </div>
        ) : (
          stages.map((stage, idx) => {
            const colorClass = STAGE_COLORS[stage.stage] || 'border-slate-600 text-slate-300 bg-slate-800/40';
            return (
              <div key={idx} className="relative pl-6 border-l-2 border-slate-800 last:border-l-transparent">
                <div className="absolute -left-[9px] top-1 w-4 h-4 rounded-full bg-slate-900 border-2 border-indigo-500 flex items-center justify-center" />
                <div className={`p-4 rounded-lg border ${colorClass} transition-all`}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-slate-900/60 border border-current">
                      {stage.stage}
                    </span>
                    <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-slate-900/80 text-slate-300 border border-slate-700">
                      {stage.technique_id} - {stage.technique_name}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed mb-3">
                    Observed anomalous activity targeting internal assets via {stage.proto || 'TCP'}.
                  </p>
                  <div className="flex flex-wrap items-center gap-4 text-[11px] font-mono text-slate-400 bg-slate-950/60 px-3 py-2 rounded">
                    <div className="flex items-center gap-1.5">
                      <Terminal className="w-3.5 h-3.5 text-slate-500" />
                      <span>{stage.src_ip}</span>
                      <ArrowRight className="w-3 h-3 text-slate-600" />
                      <span>{stage.dest_ip}:{stage.dest_port}</span>
                    </div>
                    {stage.bytes_out && (
                      <div>Bytes: <span className="text-slate-200">{stage.bytes_out.toLocaleString()}</span></div>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
''',
    'frontend/src/components/AgentReasoningStream.jsx': '''import React from 'react';
import { Bot, Cpu, Search, FileText, CheckCircle } from 'lucide-react';

const AGENT_META = {
  Triage: { icon: Search, color: 'text-amber-400', border: 'border-amber-500/30' },
  Investigator: { icon: Cpu, color: 'text-indigo-400', border: 'border-indigo-500/30' },
  'Threat Hunter': { icon: Bot, color: 'text-rose-400', border: 'border-rose-500/30' },
  Reporter: { icon: FileText, color: 'text-emerald-400', border: 'border-emerald-500/30' },
};

export default function AgentReasoningStream({ agentLogs = [], isAnalyzing = false }) {
  return (
    <div className="flex flex-col h-full bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
      <div className="flex items-center justify-between px-4 py-3 bg-slate-950/80 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-indigo-400" />
          <h2 className="font-semibold text-sm tracking-wide text-slate-100 uppercase">
            Autonomous SOC Crew Reasoning
          </h2>
        </div>
        {isAnalyzing && (
          <div className="flex items-center gap-2 text-xs text-indigo-400">
            <span className="inline-block w-2 h-2 rounded-full bg-indigo-500 animate-ping" />
            <span>Reasoning Active</span>
          </div>
        )}
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-4 font-mono text-xs custom-scrollbar">
        {agentLogs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500 p-8">
            <Cpu className="w-8 h-8 mb-2 stroke-[1.5] text-slate-600" />
            <p>Agent crew standing by for anomalous detections.</p>
          </div>
        ) : (
          agentLogs.map((log, i) => {
            const meta = AGENT_META[log.agent_name] || { icon: Bot, color: 'text-slate-400', border: 'border-slate-700' };
            const Icon = meta.icon;
            return (
              <div key={i} className={`p-3.5 rounded-lg bg-slate-950/50 border ${meta.border} space-y-2`}>
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-2">
                  <div className="flex items-center gap-2">
                    <Icon className={`w-4 h-4 ${meta.color}`} />
                    <span className={`font-semibold ${meta.color}`}>{log.agent_name}</span>
                  </div>
                  <span className="text-[10px] text-slate-500">{log.timestamp}</span>
                </div>
                <div className="text-slate-300 leading-relaxed whitespace-pre-wrap">{log.thought_process}</div>
                {log.verdict && (
                  <div className="flex items-center gap-1.5 pt-1 text-emerald-400 text-[11px] font-semibold">
                    <CheckCircle className="w-3.5 h-3.5" />
                    <span>Verdict: {log.verdict}</span>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
''',
    'frontend/src/components/ContainmentGate.jsx': '''import React, { useState } from 'react';
import { ShieldCheck, Check, X, AlertOctagon, Lock } from 'lucide-react';

export default function ContainmentGate({ incident, onAuthorize, isProcessing = false }) {
  const [operatorInitials, setOperatorInitials] = useState('');

  if (!incident) {
    return (
      <div className="flex flex-col items-center justify-center h-full bg-slate-900 border border-slate-800 rounded-xl p-6 text-slate-500 shadow-xl">
        <ShieldCheck className="w-8 h-8 mb-2 stroke-[1.5] text-slate-600" />
        <p className="text-sm">No critical incidents awaiting containment authorization.</p>
      </div>
    );
  }

  const handleAction = (approved) => {
    if (!operatorInitials.trim()) return;
    onAuthorize({
      incident_id: incident.id,
      approved,
      approved_by: operatorInitials.trim(),
    });
  };

  return (
    <div className="flex flex-col justify-between h-full bg-slate-900 border border-rose-900/40 rounded-xl p-5 shadow-2xl relative overflow-hidden">
      <div className="absolute -top-12 -right-12 w-36 h-36 bg-rose-600/10 rounded-full blur-3xl pointer-events-none" />
      <div>
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <AlertOctagon className="w-5 h-5 text-rose-500" />
            <h2 className="font-semibold text-sm tracking-wide text-slate-100 uppercase">
              Containment Gate
            </h2>
          </div>
          <span className="px-2 py-0.5 rounded bg-rose-950 border border-rose-700 text-rose-300 font-mono text-[10px] font-bold">
            HITL REQUIRED
          </span>
        </div>

        <div className="mt-4 space-y-3">
          <div>
            <span className="text-xs text-slate-400">Target Asset:</span>
            <p className="font-mono text-sm font-bold text-slate-100 mt-0.5">
              {incident.target_host || '10.0.4.15 (Host Isolation)'}
            </p>
          </div>

          <div className="p-3 rounded-lg bg-slate-950/70 border border-slate-800 text-xs text-slate-300 space-y-1.5 font-mono">
            <div className="text-rose-400 font-semibold mb-1">Proposed Countermeasures:</div>
            <ul className="list-disc list-inside space-y-1 text-slate-300">
              {incident.actions?.map((act, idx) => (
                <li key={idx}>{act}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      <div className="mt-5 pt-4 border-t border-slate-800 space-y-3">
        <div>
          <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
            Operator Call-sign
          </label>
          <div className="relative">
            <Lock className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
            <input
              type="text"
              value={operatorInitials}
              onChange={(e) => setOperatorInitials(e.target.value)}
              placeholder="e.g. OP-SOC-01"
              className="w-full bg-slate-950 border border-slate-700 rounded-lg pl-9 pr-3 py-2 text-xs font-mono text-slate-100 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        <div className="flex gap-3">
          <button
            onClick={() => handleAction(false)}
            disabled={!operatorInitials.trim() || isProcessing}
            className="flex-1 flex items-center justify-center gap-2 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed text-xs font-semibold text-slate-300 transition-colors border border-slate-700"
          >
            <X className="w-4 h-4 text-slate-400" />
            Reject
          </button>
          <button
            onClick={() => handleAction(true)}
            disabled={!operatorInitials.trim() || isProcessing}
            className="flex-1 flex items-center justify-center gap-2 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 disabled:opacity-40 disabled:cursor-not-allowed text-xs font-semibold text-white transition-colors shadow-lg shadow-rose-950"
          >
            <Check className="w-4 h-4" />
            Authorize
          </button>
        </div>
      </div>
    </div>
  );
}
''',
    'frontend/src/App.jsx': '''import React, { useState } from 'react';
import LiveFeed from './components/LiveFeed';
import AttackTimeline from './components/AttackTimeline';
import AgentReasoningStream from './components/AgentReasoningStream';
import ContainmentGate from './components/ContainmentGate';
import { Shield, Play, RefreshCw } from 'lucide-react';
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

export default function App() {
  const [logs, setLogs] = useState([]);
  const [timeline, setTimeline] = useState([]);
  const [agentLogs, setAgentLogs] = useState([]);
  const [pendingIncident, setPendingIncident] = useState(null);
  const [loading, setLoading] = useState(false);

  const runSimulation = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/campaign/simulate`);
      const telemetry = res.data.anomalies || [];
      setLogs(telemetry);

      const stages = telemetry
        .filter((l) => l.stage)
        .map((l) => ({
          stage: l.stage,
          technique_id: l.mitre_technique,
          technique_name: l.stage,
          src_ip: l.src_ip,
          dest_ip: l.dest_ip,
          dest_port: l.dest_port,
          proto: l.proto,
          bytes_out: l.bytes_out,
        }));
      setTimeline(stages);

      setAgentLogs([
        {
          agent_name: 'Triage',
          timestamp: new Date().toLocaleTimeString(),
          thought_process: 'Identified 4 anomalous event signatures. Filtered 46 background baseline records.',
          verdict: 'Confirmed Multi-Stage Intrusion Campaign',
        },
        {
          agent_name: 'Investigator',
          timestamp: new Date().toLocaleTimeString(),
          thought_process: 'Mapped attack path: Active Scanning (T1595) -> Web Exploit (T1190) -> SMB Lateral Movement (T1021.002) -> DNS Exfil (T1048).',
          verdict: 'Target Compromised (Host: 10.0.4.15)',
        },
        {
          agent_name: 'Threat Hunter',
          timestamp: new Date().toLocaleTimeString(),
          thought_process: 'Formulating containment boundaries. Proposing network layer isolation to prevent C2 sync.',
          verdict: 'Pending Human Operator Gate Authorization',
        },
      ]);

      setPendingIncident({
        id: 'INC-2026-9901',
        target_host: '10.0.4.15 (Host Isolation)',
        actions: [
          'Isolate host 10.0.4.15 at switch level',
          'Block external IP 198.51.100.44 on perimeter edge',
          'Flush active SMB user sessions on internal subnet',
        ],
      });
    } catch (err) {
      console.error('Simulation error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleContainment = async (payload) => {
    try {
      await axios.post(`${API_BASE}/containment/authorize`, payload);
      setPendingIncident(null);
      setAgentLogs((prev) => [
        ...prev,
        {
          agent_name: 'Reporter',
          timestamp: new Date().toLocaleTimeString(),
          thought_process: `Action ${payload.approved ? 'AUTHORIZED' : 'REJECTED'} by operator ${payload.approved_by}. Containment workflow closed.`,
          verdict: payload.approved ? 'Remediation Applied' : 'Operator Aborted',
        },
      ]);
    } catch (err) {
      console.error('Authorization failed:', err);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <header className="flex items-center justify-between px-6 py-3.5 bg-slate-900 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-indigo-600/20 border border-indigo-500/40">
            <Shield className="w-5 h-5 text-indigo-400" />
          </div>
          <div>
            <h1 className="font-bold text-sm tracking-wider uppercase">SentinelAI-X</h1>
            <p className="text-[10px] text-slate-400">Autonomous SOC Multi-Agent Detection & Response Engine</p>
          </div>
        </div>

        <button
          onClick={runSimulation}
          disabled={loading}
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white transition-all shadow-md shadow-indigo-900/40 disabled:opacity-50"
        >
          {loading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
          Generate Attack Simulation
        </button>
      </header>

      <main className="flex-1 p-6 grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-4 gap-6 overflow-hidden">
        <div className="h-[750px]"><LiveFeed logs={logs} /></div>
        <div className="h-[750px]"><AttackTimeline stages={timeline} /></div>
        <div className="h-[750px]"><AgentReasoningStream agentLogs={agentLogs} isAnalyzing={loading} /></div>
        <div className="h-[750px]"><ContainmentGate incident={pendingIncident} onAuthorize={handleContainment} isProcessing={loading} /></div>
      </main>
    </div>
  );
}
'''
}

for path, content in files.items():
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print("\n>>> All files and folders successfully written to disk! <<<\n")