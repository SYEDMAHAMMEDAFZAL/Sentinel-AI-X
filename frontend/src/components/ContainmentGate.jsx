import React, { useState } from 'react';
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
