import React from 'react';
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
