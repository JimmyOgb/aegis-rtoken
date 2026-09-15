"use client";

import React from "react";
import { MarketSnapshot, MarketOverviewItem } from "@/types";
import { Radio, ArrowUpDown, Clock, Layers, ShieldCheck, DollarSign } from "lucide-react";

interface ActiveMarketDetailProps {
  symbol: string;
  market: MarketSnapshot | null;
  overviewItem?: MarketOverviewItem | null;
  discoveredSymbols: string[];
  isBackendOnline?: boolean;
  onSelectSymbol: (symbol: string) => void;
}

export const ActiveMarketDetail: React.FC<ActiveMarketDetailProps> = ({
  symbol,
  market,
  overviewItem,
  discoveredSymbols,
  isBackendOnline = true,
  onSelectSymbol,
}) => {
  // Determine granular, honest status
  let statusText = "UNAVAILABLE";
  let badgeColor = "rose";

  if (!isBackendOnline) {
    statusText = "BACKEND OFFLINE";
    badgeColor = "rose";
  } else if (market?.status === "not_found") {
    statusText = "MARKET NOT FOUND";
    badgeColor = "amber";
  } else if (market && (market.is_connected || market.connected) && market.bid > 0) {
    if (market.quote_freshness !== undefined && market.quote_freshness > 10) {
      statusText = "STALE QUOTE";
      badgeColor = "amber";
    } else {
      statusText = "ACTIVE";
      badgeColor = "emerald";
    }
  } else if (market && market.status === "online" && (market.bid <= 0 || !market.is_connected)) {
    statusText = "MARKET DATA UNAVAILABLE";
    badgeColor = "amber";
  } else {
    statusText = "UNAVAILABLE";
    badgeColor = "rose";
  }

  const isLive = statusText === "ACTIVE" || statusText === "STALE QUOTE";

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl">
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-slate-800 gap-3">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <Radio className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-slate-100 font-mono tracking-tight">
                Active Market: {symbol}
              </h2>
              <span
                className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold font-mono uppercase ${
                  badgeColor === "emerald"
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                    : badgeColor === "amber"
                    ? "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                    : "bg-rose-500/10 text-rose-400 border border-rose-500/30"
                }`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    badgeColor === "emerald"
                      ? "bg-emerald-400 animate-pulse"
                      : badgeColor === "amber"
                      ? "bg-amber-400"
                      : "bg-rose-400"
                  }`}
                />
                {statusText}
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Monitoring multiple tokenized U.S. equity markets &bull; Bitget UTA SPOT Feed
            </p>
          </div>
        </div>

        {/* Market Selector Dropdown */}
        <div className="flex items-center gap-2">
          <label htmlFor="market-select" className="text-xs font-mono text-slate-400 uppercase">
            Switch Market:
          </label>
          <select
            id="market-select"
            value={symbol}
            onChange={(e) => onSelectSymbol(e.target.value)}
            className="bg-slate-950 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-1.5 font-mono focus:outline-none focus:border-indigo-500"
          >
            {discoveredSymbols.length > 0 ? (
              discoveredSymbols.map((sym) => (
                <option key={sym} value={sym}>
                  {sym} {sym === "RAAPLUSDT" ? "(Apple rToken)" : sym === "RNVDAUSDT" ? "(Nvidia rToken)" : sym === "RTSLAUSDT" ? "(Tesla rToken)" : sym === "RMSFTUSDT" ? "(Microsoft rToken)" : sym === "RAMZNUSDT" ? "(Amazon rToken)" : sym === "RGOOGLUSDT" ? "(Google rToken)" : sym === "RMETAUSDT" ? "(Meta rToken)" : ""}
                </option>
              ))
            ) : (
              <option value="RAAPLUSDT">RAAPLUSDT (Apple rToken)</option>
            )}
          </select>
        </div>
      </div>

      {/* Grid of details for active market */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 mt-4">
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3">
          <span className="text-[11px] font-mono text-slate-400 block uppercase">Base / Quote</span>
          <span className="text-sm font-bold font-mono text-slate-200">
            {market?.base_coin || symbol.replace("USDT", "")} / {market?.quote_coin || "USDT"}
          </span>
          <span className="text-[10px] text-slate-500 font-mono block mt-0.5">
            Underlying: {overviewItem?.underlying || symbol.slice(1, -4)}
          </span>
        </div>

        <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3">
          <span className="text-[11px] font-mono text-slate-400 block uppercase">Best Bid</span>
          <span className="text-sm font-bold font-mono text-emerald-400">
            {isLive && market && market.bid > 0 ? `$${market.bid.toFixed(2)}` : "--"}
          </span>
          <span className="text-[10px] text-slate-500 font-mono block mt-0.5">Bitget BBO</span>
        </div>

        <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3">
          <span className="text-[11px] font-mono text-slate-400 block uppercase">Best Ask</span>
          <span className="text-sm font-bold font-mono text-rose-400">
            {isLive && market && market.ask > 0 ? `$${market.ask.toFixed(2)}` : "--"}
          </span>
          <span className="text-[10px] text-slate-500 font-mono block mt-0.5">Bitget BBO</span>
        </div>

        <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3">
          <span className="text-[11px] font-mono text-slate-400 block uppercase">Spread %</span>
          <span className="text-sm font-bold font-mono text-cyan-400">
            {isLive && market && market.spread_percent > 0 ? `${market.spread_percent.toFixed(3)}%` : "--"}
          </span>
          <span className="text-[10px] text-slate-500 font-mono block mt-0.5">Max Threshold: 0.50%</span>
        </div>

        <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3">
          <span className="text-[11px] font-mono text-slate-400 block uppercase">Order Bounds</span>
          <span className="text-sm font-bold font-mono text-slate-200">
            Min {market?.min_order_qty ?? overviewItem?.min_order_qty ?? 0.0001}
          </span>
          <span className="text-[10px] text-slate-500 font-mono block mt-0.5">
            Min Notional: ${market?.min_order_amount ?? overviewItem?.min_order_amount ?? 10.0}
          </span>
        </div>

        <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3">
          <span className="text-[11px] font-mono text-slate-400 block uppercase">Quote Freshness</span>
          <span className="text-sm font-bold font-mono text-emerald-300">
            {isLive && market?.quote_freshness !== undefined ? `${market.quote_freshness.toFixed(1)}s ago` : "--"}
          </span>
          <span className="text-[10px] text-slate-500 font-mono block mt-0.5">
            {market?.provider || "Bitget UTA SPOT"}
          </span>
        </div>
      </div>
    </div>
  );
};
