"use client";

import React from "react";
import { MarketOverviewItem } from "@/types";
import { Globe, ArrowRight, ShieldAlert, Cpu, Zap, Activity } from "lucide-react";

interface MultiMarketOverviewProps {
  markets: MarketOverviewItem[];
  selectedSymbol: string;
  onSelectSymbol: (symbol: string) => void;
}

export const MultiMarketOverview: React.FC<MultiMarketOverviewProps> = ({
  markets,
  selectedSymbol,
  onSelectSymbol,
}) => {
  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-800 gap-2">
        <div className="flex items-center gap-2">
          <Globe className="h-5 w-5 text-indigo-400" />
          <h3 className="font-semibold text-sm tracking-wide text-slate-100 uppercase">
            Market Universe &amp; Sentinel Status
          </h3>
          <span className="text-[10px] bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded font-mono">
            {markets.length} DISCOVERED rTOKENS
          </span>
        </div>
        <div className="text-xs text-slate-400 font-mono">
          Dynamic Discovery: Bitget UTA SPOT Instruments &bull; Zero Mocks
        </div>
      </div>

      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 font-mono uppercase text-[11px] bg-slate-950/40">
              <th className="py-2.5 px-3">Market</th>
              <th className="py-2.5 px-3">Status</th>
              <th className="py-2.5 px-3 text-right">Bid</th>
              <th className="py-2.5 px-3 text-right">Ask</th>
              <th className="py-2.5 px-3 text-right">Spread</th>
              <th className="py-2.5 px-3">Catalyst Feed</th>
              <th className="py-2.5 px-3">Qwen Analysis</th>
              <th className="py-2.5 px-3">Risk Gate</th>
              <th className="py-2.5 px-3 text-center">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono">
            {markets.length === 0 ? (
              <tr>
                <td colSpan={9} className="py-6 text-center text-slate-500 font-mono">
                  Connecting to Bitget UTA instrument stream...
                </td>
              </tr>
            ) : (
              markets.map((m) => {
                const isSelected = m.symbol.toUpperCase() === selectedSymbol.toUpperCase();
                const isOnline = m.status.toLowerCase() === "online" && m.market_connected;
                const spreadFormatted = m.spread_percent > 0 ? `${m.spread_percent.toFixed(3)}%` : "--";

                return (
                  <tr
                    key={m.symbol}
                    onClick={() => onSelectSymbol(m.symbol)}
                    className={`cursor-pointer transition-colors ${
                      isSelected
                        ? "bg-indigo-950/40 border-l-2 border-indigo-500 hover:bg-indigo-950/60"
                        : "hover:bg-slate-800/40"
                    }`}
                  >
                    <td className="py-3 px-3">
                      <div className="flex items-center gap-1.5 font-bold text-slate-200">
                        <span>{m.symbol}</span>
                        <span className="text-[10px] text-slate-400 font-normal">
                          ({m.underlying || m.base_coin})
                        </span>
                        {isSelected && (
                          <span className="text-[9px] bg-cyan-500/20 text-cyan-300 px-1 rounded uppercase font-semibold">
                            ACTIVE
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-3">
                      <span
                        className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${
                          isOnline
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                            : "bg-rose-500/10 text-rose-400 border border-rose-500/30"
                        }`}
                      >
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            isOnline ? "bg-emerald-400" : "bg-rose-400"
                          }`}
                        />
                        {isOnline ? "ONLINE" : "UNAVAILABLE"}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right text-slate-300">
                      {m.bid > 0 ? `$${m.bid.toFixed(2)}` : "--"}
                    </td>
                    <td className="py-3 px-3 text-right text-slate-300">
                      {m.ask > 0 ? `$${m.ask.toFixed(2)}` : "--"}
                    </td>
                    <td className="py-3 px-3 text-right font-semibold text-slate-200">
                      {spreadFormatted}
                    </td>
                    <td className="py-3 px-3 max-w-[200px] truncate text-slate-400">
                      {m.latest_event ? (
                        <span className="text-slate-300 truncate block" title={m.latest_event}>
                          {m.latest_event}
                        </span>
                      ) : (
                        <span className="text-slate-600 italic">Pending Catalyst</span>
                      )}
                    </td>
                    <td className="py-3 px-3 text-slate-300">
                      {m.latest_qwen ? (
                        <span className="inline-flex items-center gap-1 text-[11px] text-cyan-300">
                          <Cpu className="h-3 w-3 text-cyan-400" />
                          {m.latest_qwen}
                        </span>
                      ) : (
                        <span className="text-slate-600 italic">Awaiting</span>
                      )}
                    </td>
                    <td className="py-3 px-3">
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${
                          m.latest_risk === "TRADE"
                            ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                            : m.latest_risk === "BLOCKED"
                            ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                            : "bg-slate-800 text-slate-400"
                        }`}
                      >
                        {m.latest_risk || "ARMED"}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-center">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectSymbol(m.symbol);
                        }}
                        className={`px-2 py-1 rounded text-[10px] font-sans font-semibold transition-colors flex items-center gap-1 mx-auto ${
                          isSelected
                            ? "bg-cyan-600 text-white"
                            : "bg-slate-800 hover:bg-slate-700 text-slate-300"
                        }`}
                      >
                        <span>{isSelected ? "Inspecting" : "Select"}</span>
                        <ArrowRight className="h-3 w-3" />
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
