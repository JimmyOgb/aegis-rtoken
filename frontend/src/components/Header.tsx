import React from "react";
import { ShieldCheck, Activity, AlertTriangle } from "lucide-react";

interface HeaderProps {
  statusText?: string;
  isBackendOnline: boolean;
  tradingMode: string;
  bitgetDemoStatus?: string;
  qwenStatus?: string;
  marketDataStatus?: string;
  assetSupportStatus?: string;
  orderStatusLabel?: string;
}

export const Header: React.FC<HeaderProps> = ({
  statusText = "SYSTEM INITIALIZING",
  isBackendOnline,
  tradingMode,
  bitgetDemoStatus = "Bitget Demo Disconnected",
  qwenStatus = "Qwen Unavailable",
  marketDataStatus = "Market Data Unavailable",
  assetSupportStatus = "Supported Asset",
  orderStatusLabel = "No Orders Submitted",
}) => {
  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur px-6 py-4 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shadow-sm shadow-cyan-500/20">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold tracking-wider text-slate-100 uppercase">
                AegisrToken
              </h1>
              <span className="px-2 py-0.5 text-xs font-semibold rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                v0.1.0
              </span>
            </div>
            <p className="text-xs text-slate-400 tracking-wide">
              Autonomous Event-Driven Sentinel — Bitget UTA / Paper Trading
            </p>
          </div>
        </div>

        {/* Prominent Professional Status Indicator: BITGET DEMO / PAPER TRADING */}
        <div className="flex items-center gap-2.5 bg-amber-500/10 border border-amber-500/30 rounded-lg px-3.5 py-1.5">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-amber-500"></span>
          </span>
          <div className="flex flex-col">
            <span className="text-[11px] font-bold font-mono tracking-wider text-amber-300 uppercase">
              BITGET DEMO / PAPER TRADING
            </span>
            <span className="text-[9px] font-mono text-amber-400/80">
              Simulated Environment · Live Mainnet Disabled
            </span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 text-xs">
          {/* Bitget Demo Auth Status */}
          <div className={`border rounded-md px-2.5 py-1 flex items-center gap-1.5 font-mono ${
            bitgetDemoStatus.includes("CONNECTED")
              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
              : "bg-amber-500/10 border-amber-500/30 text-amber-400"
          }`}>
            <span className={`h-1.5 w-1.5 rounded-full ${bitgetDemoStatus.includes("CONNECTED") ? "bg-emerald-400" : "bg-amber-400"}`}></span>
            <span>{bitgetDemoStatus}</span>
          </div>

          {/* Qwen Status */}
          <div className={`border rounded-md px-2.5 py-1 flex items-center gap-1.5 font-mono ${
            qwenStatus === "Qwen Connected"
              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
              : "bg-rose-500/10 border-rose-500/30 text-rose-400"
          }`}>
            <span className={`h-1.5 w-1.5 rounded-full ${qwenStatus === "Qwen Connected" ? "bg-emerald-400" : "bg-rose-400"}`}></span>
            <span>{qwenStatus}</span>
          </div>

          {/* Market Data Status */}
          <div className={`border rounded-md px-2.5 py-1 flex items-center gap-1.5 font-mono ${
            marketDataStatus === "Market Data Connected"
              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
              : "bg-rose-500/10 border-rose-500/30 text-rose-400"
          }`}>
            <span className={`h-1.5 w-1.5 rounded-full ${marketDataStatus === "Market Data Connected" ? "bg-emerald-400" : "bg-rose-400"}`}></span>
            <span>{marketDataStatus}</span>
          </div>

          {/* Asset Support Label */}
          <div className={`border rounded-md px-2.5 py-1 flex items-center gap-1.5 font-mono ${
            assetSupportStatus === "Supported Asset"
              ? "bg-cyan-500/10 border-cyan-500/30 text-cyan-400"
              : "bg-rose-500/10 border-rose-500/30 text-rose-400"
          }`}>
            <span>{assetSupportStatus}</span>
          </div>

          {/* Order Status Label */}
          <div className={`border rounded-md px-2.5 py-1 flex items-center gap-1.5 font-mono ${
            orderStatusLabel.includes("Confirmed")
              ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
              : orderStatusLabel.includes("Blocked")
              ? "bg-amber-500/10 border-amber-500/30 text-amber-400"
              : "bg-slate-900 border-slate-800 text-slate-400"
          }`}>
            <span>{orderStatusLabel}</span>
          </div>
        </div>
      </div>
    </header>
  );
};
