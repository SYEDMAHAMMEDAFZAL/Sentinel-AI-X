import random
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
