"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { AgentStatus, DecisionRecord, MarketSnapshot, MarketOverviewItem } from "@/types";
import {
  fetchAgentStatus,
  fetchMarketSnapshot,
  fetchRecentDecisions,
  fetchMarkets,
} from "@/lib/api";

export function useAegis() {
  const [status, setStatus] = useState<AgentStatus | null>(null);
  const [selectedSymbol, setSelectedSymbol] = useState<string>("RAAPLUSDT");
  const [market, setMarket] = useState<MarketSnapshot | null>(null);
  const [markets, setMarkets] = useState<MarketOverviewItem[]>([]);
  const [decisions, setDecisions] = useState<DecisionRecord[]>([]);
  const [isConnectedToBackend, setIsConnectedToBackend] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const selectedSymbolRef = useRef(selectedSymbol);
  useEffect(() => {
    selectedSymbolRef.current = selectedSymbol;
  }, [selectedSymbol]);

  const refresh = useCallback(async () => {
    try {
      const activeSym = selectedSymbolRef.current;
      const [statusRes, marketRes, marketsRes, decisionsRes] = await Promise.all([
        fetchAgentStatus(),
        fetchMarketSnapshot(activeSym),
        fetchMarkets(),
        fetchRecentDecisions(50),
      ]);

      if (statusRes) {
        setStatus(statusRes);
        setIsConnectedToBackend(true);
      } else {
        setStatus(null);
        setIsConnectedToBackend(false);
      }

      setMarket(marketRes);
      setMarkets(marketsRes || []);
      setDecisions(decisionsRes || []);
    } catch {
      setStatus(null);
      setIsConnectedToBackend(false);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // When symbol selection changes, refresh immediately
  const handleSelectSymbol = useCallback((sym: string) => {
    setSelectedSymbol(sym);
    selectedSymbolRef.current = sym;
    fetchMarketSnapshot(sym).then((res) => {
      if (res) setMarket(res);
    });
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 3000);
    return () => clearInterval(interval);
  }, [refresh]);

  return {
    status,
    market,
    markets,
    decisions,
    selectedSymbol,
    setSelectedSymbol: handleSelectSymbol,
    isConnectedToBackend,
    isLoading,
    refresh,
  };
}

