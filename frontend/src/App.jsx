import React, { useState } from 'react';
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
