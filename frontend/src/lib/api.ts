import { AgentStatus, DecisionRecord, MarketSnapshot, MarketOverviewItem } from "@/types";
import { dedupeEventsById } from "./events";

const API_BASE_URL = (process.env.NEXT_PUBLIC_AEGIS_API_URL || "").replace(/\/+$/, "");

export async function fetchAgentStatus(): Promise<AgentStatus | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/status`, { cache: "no-store" });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchMarketSnapshot(symbol?: string): Promise<MarketSnapshot | null> {
  try {
    const url = symbol 
      ? `${API_BASE_URL}/api/market?symbol=${encodeURIComponent(symbol)}` 
      : `${API_BASE_URL}/api/market`;
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchMarkets(): Promise<MarketOverviewItem[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/markets`, { cache: "no-store" });
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

export async function fetchRecentDecisions(limit = 25, symbol?: string): Promise<DecisionRecord[]> {
  try {
    const url = symbol
      ? `${API_BASE_URL}/api/decisions?limit=${limit}&symbol=${encodeURIComponent(symbol)}`
      : `${API_BASE_URL}/api/decisions?limit=${limit}`;
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) return [];
    const data = await res.json();
    return dedupeEventsById(Array.isArray(data) ? data : []);
  } catch {
    return [];
  }
}

