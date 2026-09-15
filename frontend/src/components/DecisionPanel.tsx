import React from "react";
import { DecisionRecord } from "@/types";
import { AlertCircle, CheckCircle2, PauseCircle, ShieldAlert, Cpu } from "lucide-react";

interface DecisionPanelProps {
  latestDecision?: DecisionRecord | null;
}

export const DecisionPanel: React.FC<DecisionPanelProps> = ({ latestDecision }) => {
  const getDecisionBadge = () => {
    if (!latestDecision) {
      return (
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-800 border border-slate-700 text-slate-300 font-mono text-sm font-bold">
          <PauseCircle className="h-4 w-4 text-slate-400" />
          <span>WAITING FOR EVENT</span>
        </div>
      );
    }

    switch (latestDecision.decision) {
      case "TRADE":
        return (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-mono text-sm font-bold animate-pulse">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            <span>TRADE APPROVED</span>
          </div>
        );
      case "HOLD":
        return (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-amber-500/10 border border-amber-500/30 text-amber-400 font-mono text-sm font-bold">
            <AlertCircle className="h-4 w-4 text-amber-400" />
            <span>HOLD</span>
          </div>
        );
      case "BLOCKED":
        return (
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-rose-500/10 border border-rose-500/30 text-rose-400 font-mono text-sm font-bold">
            <ShieldAlert className="h-4 w-4 text-rose-400" />
            <span>BLOCKED BY RISK GATE</span>
          </div>
        );
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4 mb-4">
        <div>
          <span className="text-xs font-semibold text-slate-400 tracking-wider uppercase">
            LATEST DECISION
          </span>
          <h2 className="text-lg font-bold text-slate-100 mt-0.5">
            Autonomous Gate Evaluation
          </h2>
        </div>
        <div>{getDecisionBadge()}</div>
      </div>

      {latestDecision ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Model Intelligence Column */}
          <div className="bg-slate-950/60 border border-slate-800/80 rounded-md p-3.5">
            <div className="flex items-center justify-between gap-2 mb-2 text-xs font-semibold text-cyan-400 uppercase">
              <div className="flex items-center gap-1.5">
                <Cpu className="h-4 w-4" />
                <span>Qwen Analysis</span>
              </div>
              <span className="bg-cyan-500/20 text-cyan-300 font-mono text-[10px] px-1.5 py-0.5 rounded">
                {latestDecision.symbol || latestDecision.asset}
              </span>
            </div>
            <p className="text-sm font-medium text-slate-200 line-clamp-2 mb-2">
              &quot;{latestDecision.headline}&quot;
            </p>
            <div className="flex items-center gap-4 text-xs font-mono text-slate-400">
              <div>
                Sentiment:{" "}
                <span className="text-slate-200 font-bold">{latestDecision.sentiment}</span>
              </div>
              <div>
                Model Confidence:{" "}
                <span className="text-cyan-400 font-bold">
                  {((latestDecision.model_confidence ?? latestDecision.confidence ?? 0) * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>

          {/* Risk Gate Column */}
          <div className="bg-slate-950/60 border border-slate-800/80 rounded-md p-3.5">
            <div className="flex items-center gap-2 mb-2 text-xs font-semibold text-emerald-400 uppercase">
              <ShieldAlert className="h-4 w-4" />
              <span>Deterministic Risk Gate</span>
            </div>
            <p className="text-sm font-mono text-slate-300 mb-2">
              Reason: <span className="font-semibold text-slate-100">{latestDecision.reason}</span>
            </p>
            <div className="flex items-center gap-4 text-xs font-mono text-slate-400">
              <div>
                Market Spread:{" "}
                <span className="text-slate-200">{latestDecision.spread_percent.toFixed(3)}%</span>
              </div>
              <div>
                Mode:{" "}
                <span className="text-slate-200">{latestDecision.execution_mode}</span>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="py-8 text-center text-slate-500 font-mono text-xs">
          WAITING FOR EVENT — Sentinel monitoring market feeds for real-time catalysts...
        </div>
      )}
    </div>
  );
};
