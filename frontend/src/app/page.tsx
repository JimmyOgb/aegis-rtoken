"use client";

import React from "react";
import { useAegis } from "@/hooks/useAegis";
import { Header } from "@/components/Header";
import { MetricCard } from "@/components/MetricCard";
import { ActiveMarketDetail } from "@/components/ActiveMarketDetail";
import { MultiMarketOverview } from "@/components/MultiMarketOverview";
import { DecisionPanel } from "@/components/DecisionPanel";
import { RiskTelemetry } from "@/components/RiskTelemetry";
import { EventTimeline } from "@/components/EventTimeline";
import { ArchitecturePipeline } from "@/components/ArchitecturePipeline";
import { Activity, Globe, Radio, Cpu, ShieldAlert, Zap } from "lucide-react";

export default function DashboardPage() {
  const {
    status,
    market,
    markets,
    decisions,
    selectedSymbol,
    setSelectedSymbol,
    isConnectedToBackend,
  } = useAegis();

  // Find latest decision for active market, or fallback to overall latest decision
  const activeMarketDecision = decisions.find(
    (d) => (d.symbol || d.asset).toUpperCase() === selectedSymbol.toUpperCase()
  );
  const latestDecision = activeMarketDecision || (decisions.length > 0 ? decisions[0] : null);

  const isMarketConnected = Boolean(market && (market.is_connected || market.connected) && market.bid > 0);
  const activeOverviewItem = markets.find(
    (m) => m.symbol.toUpperCase() === selectedSymbol.toUpperCase()
  );

  const discoveredSymbols = markets.length > 0 
    ? markets.map((m) => m.symbol) 
    : (status?.monitored_markets || ["RAAPLUSDT", "RNVDAUSDT", "RTSLAUSDT", "RMSFTUSDT"]);

  return (
    <div className="min-h-screen flex flex-col bg-slate-950 text-slate-100">
      <Header
        statusText={
          isConnectedToBackend
            ? (status?.status_label || status?.agent_status || "INITIALIZING")
            : "BACKEND: DISCONNECTED"
        }
        isBackendOnline={isConnectedToBackend}
        tradingMode={status?.trading_mode || "DISCONNECTED"}
        bitgetDemoStatus={status?.bitget_demo_status}
        qwenStatus={status?.qwen_status}
        marketDataStatus={status?.market_data_status}
        assetSupportStatus={status?.asset_support_status || `Monitored Markets (${discoveredSymbols.length} rTokens)`}
        orderStatusLabel={status?.order_status_label}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 space-y-6">
        {/* Offline Banner */}
        {!isConnectedToBackend && (
          <div className="bg-rose-500/10 border border-rose-500/30 rounded-lg p-3.5 text-xs text-rose-300 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span className="font-semibold uppercase tracking-wider bg-rose-500/20 text-rose-400 px-2 py-0.5 rounded text-[10px]">
                BACKEND OFFLINE
              </span>
              <span>
                AegisrToken API gateway unreachable. Risk engine armed to FAIL CLOSED.
              </span>
            </div>
            <span className="font-mono text-[11px] text-slate-400">
              Run: python scripts/run_agent.py
            </span>
          </div>
        )}

        {/* 6 Main Metric Cards with Refined UX Terminology */}
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4">
          <MetricCard
            label="Agent Status"
            value={isConnectedToBackend ? (status?.agent_status || "STANDBY") : "DISCONNECTED"}
            subValue={status?.trading_mode ? `Mode: ${status.trading_mode}` : "Runtime offline"}
            badge={isConnectedToBackend ? "ARMED" : "OFFLINE"}
            badgeColor={isConnectedToBackend ? "emerald" : "rose"}
            icon={<Activity className="h-4 w-4" />}
          />
          <MetricCard
            label="Market Universe"
            value={`${markets.length || discoveredSymbols.length} rTokens`}
            subValue="Dynamic Bitget UTA"
            badge="DISCOVERED"
            badgeColor="cyan"
            icon={<Globe className="h-4 w-4" />}
          />
          <MetricCard
            label="Active Market"
            value={selectedSymbol}
            subValue={
              isMarketConnected
                ? `Mid: $${(((market?.bid || 0) + (market?.ask || 0)) / 2).toFixed(2)}`
                : "No live quote"
            }
            badge={isMarketConnected ? "LIVE BBO" : "DISCONNECTED"}
            badgeColor={isMarketConnected ? "emerald" : "rose"}
            icon={<Radio className="h-4 w-4" />}
          />
          <MetricCard
            label="Catalyst Feed"
            value={latestDecision ? latestDecision.event_type : "RSS SENTINEL"}
            subValue={latestDecision ? latestDecision.headline : "Monitoring RSS feeds"}
            badge={latestDecision ? latestDecision.sentiment : "ACTIVE"}
            badgeColor={
              latestDecision?.sentiment === "BULLISH"
                ? "emerald"
                : latestDecision?.sentiment === "BEARISH"
                ? "rose"
                : "slate"
            }
            icon={<Zap className="h-4 w-4" />}
          />
          <MetricCard
            label="Qwen Analysis"
            value={
              latestDecision
                ? `${((latestDecision.model_confidence ?? latestDecision.confidence ?? 0) * 100).toFixed(0)}% Conf`
                : "QWEN 3.8 MAX"
            }
            subValue={
              latestDecision
                ? `Sentiment: ${latestDecision.sentiment}`
                : "Bitget AI Intelligence"
            }
            badge={latestDecision && (latestDecision.model_confidence ?? latestDecision.confidence ?? 0) >= 0.75 ? "VERIFIED" : "STANDBY"}
            badgeColor={latestDecision && (latestDecision.model_confidence ?? latestDecision.confidence ?? 0) >= 0.75 ? "cyan" : "slate"}
            icon={<Cpu className="h-4 w-4" />}
          />
          <MetricCard
            label="Risk Gate"
            value={
              status?.circuit_breaker.is_tripped
                ? "TRIPPED"
                : isConnectedToBackend
                ? "GATES ARMED"
                : "BLOCKED"
            }
            subValue={
              status?.circuit_breaker.is_tripped
                ? `Faults: ${status.circuit_breaker.consecutive_faults}`
                : isConnectedToBackend
                ? "Fail-closed active"
                : "No backend connection"
            }
            badge={status?.circuit_breaker.is_tripped ? "TRIPPED" : isConnectedToBackend ? "ARMED" : "BLOCKED"}
            badgeColor={status?.circuit_breaker.is_tripped ? "rose" : isConnectedToBackend ? "emerald" : "amber"}
            icon={<ShieldAlert className="h-4 w-4" />}
          />
        </section>

        {/* Active Market Inspector & Switcher */}
        <ActiveMarketDetail
          symbol={selectedSymbol}
          market={market}
          overviewItem={activeOverviewItem}
          discoveredSymbols={discoveredSymbols}
          onSelectSymbol={setSelectedSymbol}
        />

        {/* Multi-Market Overview Matrix */}
        <MultiMarketOverview
          markets={markets}
          selectedSymbol={selectedSymbol}
          onSelectSymbol={setSelectedSymbol}
        />

        {/* 5-Stage Autonomous Architecture Pipeline */}
        <ArchitecturePipeline
          catalystConnected={Boolean(decisions.length > 0 || isConnectedToBackend)}
          qwenConnected={status?.qwen_status === "Qwen Connected"}
          riskEngineArmed={Boolean(isConnectedToBackend && !status?.circuit_breaker.is_tripped)}
          demoExecutionBlocked={true}
          telemetryCount={status?.telemetry_count || decisions.length}
        />

        {/* Autonomous Gate Evaluation & Decision Panel */}
        <DecisionPanel latestDecision={latestDecision} />

        {/* Deterministic Risk Telemetry */}
        <RiskTelemetry
          report={latestDecision ? latestDecision.risk_checks : null}
          circuitBreakerActive={Boolean(status?.circuit_breaker.is_tripped)}
          executionMode={status?.trading_mode || "DISCONNECTED"}
        />

        {/* Event Decision History Timeline */}
        <EventTimeline decisions={decisions} />
      </main>

      <footer className="border-t border-slate-800/80 bg-slate-950 py-4 px-6 text-center text-xs text-slate-500 font-mono">
        AegisrToken &bull; Autonomous Event-Driven Sentinel for Tokenized U.S. Equities &bull; Zero Mocks &bull; Bitget Demo Only &copy; 2026
      </footer>
    </div>
  );
}
