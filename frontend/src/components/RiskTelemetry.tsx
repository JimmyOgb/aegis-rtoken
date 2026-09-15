import React from "react";
import { RiskGateReport } from "@/types";
import { Check, X, Shield, Lock } from "lucide-react";

interface RiskTelemetryProps {
  report?: RiskGateReport | null;
  circuitBreakerActive: boolean;
  executionMode: string;
  maxSpreadLimit?: number;
  minConfidenceLimit?: number;
  maxAllocationLimit?: number;
}

export const RiskTelemetry: React.FC<RiskTelemetryProps> = ({
  report,
  circuitBreakerActive,
  executionMode,
  maxSpreadLimit = 0.8,
  minConfidenceLimit = 75,
  maxAllocationLimit = 500,
}) => {
  const gates = [
    {
      name: "Market Connectivity",
      passed: report ? report.connectivity : true,
      meta: "Heartbeat < 10s",
    },
    {
      name: "Book Freshness",
      passed: report ? report.freshness : true,
      meta: "Latency < 5s",
    },
    {
      name: "Spread Limit",
      passed: report ? report.spread_within_limit : true,
      meta: `Max ${maxSpreadLimit}%`,
    },
    {
      name: "Model Confidence",
      passed: report ? report.confidence_sufficient : true,
      meta: `Min ${minConfidenceLimit}%`,
    },
    {
      name: "Allocation Limit",
      passed: report ? report.allocation_within_limit : true,
      meta: `Max $${maxAllocationLimit}`,
    },
    {
      name: "Duplicate Event",
      passed: report ? report.deduplication_pass : true,
      meta: "60m Bloom Filter",
    },
    {
      name: "Circuit Breaker",
      passed: !circuitBreakerActive,
      meta: circuitBreakerActive ? "TRIPPED" : "ARMED",
    },
    {
      name: "Execution Mode",
      passed: true,
      meta: executionMode.toUpperCase(),
    },
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-5 shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
        <div className="flex items-center gap-2">
          <Shield className="h-4 w-4 text-cyan-400" />
          <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
            Risk Telemetry & Deterministic Gates
          </h3>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-slate-400 font-mono">
          <Lock className="h-3.5 w-3.5 text-emerald-400" />
          <span>Fail-Closed Policy</span>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {gates.map((g) => (
          <div
            key={g.name}
            className="bg-slate-950/70 border border-slate-800/80 rounded-md p-3 flex flex-col justify-between"
          >
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[11px] font-medium text-slate-400">
                {g.name}
              </span>
              {g.passed ? (
                <div className="h-4 w-4 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center">
                  <Check className="h-3 w-3" />
                </div>
              ) : (
                <div className="h-4 w-4 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center">
                  <X className="h-3 w-3" />
                </div>
              )}
            </div>
            <div className="flex items-center justify-between text-[10px] font-mono text-slate-500">
              <span>{g.meta}</span>
              <span className={g.passed ? "text-emerald-400 font-bold" : "text-rose-400 font-bold"}>
                {g.passed ? "PASS" : "FAIL"}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
