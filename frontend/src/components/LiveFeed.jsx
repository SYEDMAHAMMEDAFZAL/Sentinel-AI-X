import React from 'react';
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
