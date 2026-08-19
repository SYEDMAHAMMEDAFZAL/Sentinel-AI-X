import React from 'react';
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
