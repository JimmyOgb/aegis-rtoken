import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const CORE_RTOKENS = [
  { symbol: "RAAPLUSDT", underlying: "AAPL", base: "rAAPL", minQty: 0.0001, minAmt: 10.0 },
  { symbol: "RNVDAUSDT", underlying: "NVDA", base: "rNVDA", minQty: 0.0001, minAmt: 10.0 },
  { symbol: "RTSLAUSDT", underlying: "TSLA", base: "rTSLA", minQty: 0.0001, minAmt: 10.0 },
  { symbol: "RMSFTUSDT", underlying: "MSFT", base: "rMSFT", minQty: 0.0001, minAmt: 10.0 },
  { symbol: "RAMZNUSDT", underlying: "AMZN", base: "rAMZN", minQty: 0.0001, minAmt: 10.0 },
  { symbol: "RGOOGLUSDT", underlying: "GOOGL", base: "rGOOGL", minQty: 0.0001, minAmt: 10.0 },
  { symbol: "RMETAUSDT", underlying: "META", base: "rMETA", minQty: 0.0001, minAmt: 10.0 },
];

async function fetchRealBBO(symbol: string): Promise<{ bid: number; ask: number; spread: number; connected: boolean }> {
  try {
    const res = await fetch(`https://api.bitget.com/api/v3/market/orderbook?symbol=${symbol}&type=step0&limit=5`, {
      cache: "no-store",
    });
    if (!res.ok) return { bid: 0, ask: 0, spread: 0, connected: false };
    const payload = await res.json();
    const data = payload?.data || {};
    const bids = data.bids || [];
    const asks = data.asks || [];
    const bestBid = bids.length > 0 ? parseFloat(bids[0][0]) : 0;
    const bestAsk = asks.length > 0 ? parseFloat(asks[0][0]) : 0;
    const mid = (bestBid + bestAsk) / 2;
    const spread = mid > 0 ? ((bestAsk - bestBid) / mid) * 100 : 0;
    return {
      bid: bestBid,
      ask: bestAsk,
      spread: Math.max(0, spread),
      connected: bestBid > 0 && bestAsk > 0,
    };
  } catch {
    return { bid: 0, ask: 0, spread: 0, connected: false };
  }
}

export async function GET() {
  const upstream = process.env.AEGIS_BACKEND_URL;
  if (upstream) {
    try {
      const res = await fetch(`${upstream.replace(/\/+$/, "")}/api/markets`, {
        cache: "no-store",
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        const data = await res.json();
        return NextResponse.json(data);
      }
    } catch {
      // Fall through to real Bitget fetch
    }
  }

  // Fetch genuine real Bitget market quotes
  const results = await Promise.all(
    CORE_RTOKENS.map(async (tok) => {
      const quote = await fetchRealBBO(tok.symbol);
      return {
        symbol: tok.symbol,
        underlying: tok.underlying,
        base_coin: tok.base,
        quote_coin: "USDT",
        status: "online",
        min_order_qty: tok.minQty,
        min_order_amount: tok.minAmt,
        bid: quote.bid,
        ask: quote.ask,
        spread_percent: quote.spread,
        market_connected: quote.connected,
        latest_event: null,
        latest_qwen: null,
        latest_risk: "PENDING_CATALYST",
      };
    })
  );

  return NextResponse.json(results);
}
