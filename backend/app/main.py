from fastapi import FastAPI
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
