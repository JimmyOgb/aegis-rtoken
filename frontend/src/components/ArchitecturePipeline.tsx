import React from "react";
import {
  Zap,
  Cpu,
  ShieldCheck,
  Terminal,
  FileText,
  ChevronRight,
  ArrowDown,
  Lock,
} from "lucide-react";

interface ArchitecturePipelineProps {
  catalystConnected?: boolean;
  qwenConnected?: boolean;
  riskEngineArmed?: boolean;
  demoExecutionBlocked?: boolean;
  telemetryCount?: number;
}

export const ArchitecturePipeline: React.FC<ArchitecturePipelineProps> = ({
  catalystConnected = true,
  qwenConnected = true,
  riskEngineArmed = true,
  demoExecutionBlocked = true,
  telemetryCount = 0,
}) => {
  const stages = [
    {
      step: "01",
      title: "REAL CATALYST",
      subtitle: "Yahoo Finance & SEC Filings",
      detail: "Real-time event extraction (rAAPL / Equities)",
      badge: catalystConnected ? "LIVE FEED" : "OFFLINE",
      badgeColor: catalystConnected ? "emerald" : "rose",
      icon: <Zap className="h-4 w-4" />,
      authority: "Originating Trigger",
    },
    {
      step: "02",
      title: "QWEN ANALYSIS",
      subtitle: "Bitget Qwen 3.8 Max Provider",
      detail: "Sentiment, confidence score, and horizon",
      badge: qwenConnected ? "CONNECTED" : "UNAVAILABLE",
      badgeColor: qwenConnected ? "emerald" : "rose",
      icon: <Cpu className="h-4 w-4" />,
      authority: "Advisory Bias Only (No Exec)",
    },
    {
      step: "03",
      title: "RISK ENGINE",
      subtitle: "Deterministic Safety Gates",
      detail: "Quote, spread, model, duplicate & instrument checks",
      badge: riskEngineArmed ? "ARMED (FAIL-CLOSED)" : "HALTED",
      badgeColor: riskEngineArmed ? "cyan" : "rose",
      icon: <ShieldCheck className="h-4 w-4" />,
      authority: "Final Gatekeeper Authority",
    },
    {
      step: "04",
      title: "BITGET DEMO / PAPER EXEC",
      subtitle: "Bitget Agent CLI (`bgc`)",
      detail: "--paper-trading · paptrading: 1 header",
      badge: demoExecutionBlocked ? "BLOCKED: DEMO_AUTH_REQUIRED" : "READY",
      badgeColor: demoExecutionBlocked ? "amber" : "emerald",
      icon: <Terminal className="h-4 w-4" />,
      authority: "Demo/Paper Only (Mainnet Disabled)",
    },
    {
      step: "05",
      title: "TELEMETRY",
      subtitle: "Immutable JSONL Ledger",
      detail: `${telemetryCount} verified decision records stored`,
      badge: "ACTIVE",
      badgeColor: "emerald",
      icon: <FileText className="h-4 w-4" />,
      authority: "Zero-Mock Audit Trail",
    },
  ];

  const getBadgeStyle = (color: string) => {
    switch (color) {
      case "emerald":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
      case "cyan":
        return "bg-cyan-500/10 text-cyan-400 border-cyan-500/20";
      case "amber":
        return "bg-amber-500/10 text-amber-400 border-amber-500/20";
      case "rose":
        return "bg-rose-500/10 text-rose-400 border-rose-500/20";
      default:
        return "bg-slate-800 text-slate-300 border-slate-700";
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse"></div>
          <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
            Autonomous Pipeline Architecture
          </h3>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-400 font-mono">
          <Lock className="h-3.5 w-3.5 text-cyan-400" />
          <span>Strict Hierarchy: Real Data → Qwen → Risk Gate → Bitget Demo</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-3">
        {stages.map((stage, idx) => (
          <div key={stage.title} className="relative flex flex-col justify-between">
            <div className="bg-slate-950/70 border border-slate-800/80 rounded-md p-3.5 h-full flex flex-col justify-between hover:border-slate-700/80 transition-colors">
              <div>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <span className="text-[10px] font-mono text-slate-500 font-bold">
                    STAGE {stage.step}
                  </span>
                  <span
                    className={`text-[10px] px-1.5 py-0.5 rounded border font-mono font-bold ${getBadgeStyle(
                      stage.badgeColor
                    )}`}
                  >
                    {stage.badge}
                  </span>
                </div>

                <div className="flex items-center gap-2 text-slate-200 font-bold text-xs tracking-wide mb-1">
                  <span className="text-cyan-400">{stage.icon}</span>
                  <span>{stage.title}</span>
                </div>

                <p className="text-[11px] font-medium text-slate-400 mb-1">
                  {stage.subtitle}
                </p>
                <p className="text-[10px] text-slate-500">
                  {stage.detail}
                </p>
              </div>

              <div className="mt-3 pt-2 border-t border-slate-900 flex items-center justify-between text-[9px] font-mono text-slate-400">
                <span className="text-slate-500">Authority:</span>
                <span className="text-slate-300 font-semibold">{stage.authority}</span>
              </div>
            </div>

            {/* Arrow connector for large screens */}
            {idx < stages.length - 1 && (
              <div className="hidden lg:flex absolute -right-2 top-1/2 -translate-y-1/2 z-10 bg-slate-900 rounded-full p-0.5 border border-slate-700 text-slate-400">
                <ChevronRight className="h-3 w-3" />
              </div>
            )}
            {/* Arrow connector for small screens */}
            {idx < stages.length - 1 && (
              <div className="lg:hidden flex justify-center py-1 text-slate-600">
                <ArrowDown className="h-3.5 w-3.5" />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
