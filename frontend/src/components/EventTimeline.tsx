import React from "react";
import { DecisionRecord } from "@/types";
import { History } from "lucide-react";

interface EventTimelineProps {
  decisions: DecisionRecord[];
}

export const EventTimeline: React.FC<EventTimelineProps> = ({ decisions }) => {
  const getDecisionStyle = (dec: string) => {
    switch (dec) {
      case "TRADE":
        return "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";
      case "HOLD":
        return "text-amber-400 bg-amber-500/10 border-amber-500/20";
      case "BLOCKED":
        return "text-rose-400 bg-rose-500/10 border-rose-500/20";
      default:
        return "text-slate-400 bg-slate-800 border-slate-700";
    }
  };

  const getSentimentStyle = (sent: string) => {
    switch (sent) {
      case "BULLISH":
        return "text-emerald-400";
      case "BEARISH":
        return "text-rose-400";
      default:
        return "text-slate-400";
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <History className="h-4 w-4 text-cyan-400" />
          <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
            Event Decision History
          </h3>
        </div>
        <span className="text-xs text-slate-500 font-mono">
          {decisions.length} Records
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-mono">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[11px]">
              <th className="pb-3 pr-4 font-semibold">TIME</th>
              <th className="pb-3 pr-4 font-semibold">EVENT</th>
              <th className="pb-3 pr-4 font-semibold">ASSET</th>
              <th className="pb-3 pr-4 font-semibold">SENTIMENT</th>
              <th className="pb-3 pr-4 font-semibold">CONFIDENCE</th>
              <th className="pb-3 pr-4 font-semibold">SPREAD</th>
              <th className="pb-3 font-semibold text-right">DECISION</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {decisions.length > 0 ? (
              decisions.map((d) => (
                <tr key={d.event_id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-3 pr-4 text-slate-400 whitespace-nowrap">
                    {new Date(d.timestamp).toLocaleTimeString()}
                  </td>
                  <td className="py-3 pr-4 text-slate-200 font-sans max-w-xs truncate" title={d.headline}>
                    {d.headline}
                  </td>
                  <td className="py-3 pr-4 text-slate-300 font-bold whitespace-nowrap">
                    {d.symbol || d.asset}
                  </td>
                  <td className={`py-3 pr-4 font-bold whitespace-nowrap ${getSentimentStyle(d.sentiment)}`}>
                    {d.sentiment}
                  </td>
                  <td className="py-3 pr-4 text-cyan-400 whitespace-nowrap">
                    {(((d.model_confidence ?? d.confidence ?? 0)) * 100).toFixed(1)}%
                  </td>
                  <td className="py-3 pr-4 text-slate-400 whitespace-nowrap">
                    {d.spread_percent.toFixed(3)}%
                  </td>
                  <td className="py-3 text-right whitespace-nowrap">
                    <span className={`px-2 py-0.5 rounded border text-[10px] font-bold ${getDecisionStyle(d.decision)}`}>
                      {d.decision}
                    </span>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={7} className="py-8 text-center text-slate-500 font-mono text-xs">
                  Awaiting real-time catalysts &bull; Telemetry pipeline active across all monitored rToken markets.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
