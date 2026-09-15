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

export async function GET() {
  const upstream =
    process.env.AEGIS_BACKEND_URL ||
    (process.env.NODE_ENV === "development" ? "http://127.0.0.1:8000" : undefined);

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

  // Fetch genuine real Bitget market quotes using public tickers endpoint
  try {
    const res = await fetch("https://api.bitget.com/api/v3/market/tickers?category=SPOT", {
      cache: "no-store",
    });
    if (res.ok) {
      const payload = await res.json();
      const dataList: Array<Record<string, any>> = payload?.data || [];
      const tickerMap = new Map(dataList.map((item) => [String(item.symbol).toUpperCase(), item]));

      const results = CORE_RTOKENS.map((tok) => {
        const item = tickerMap.get(tok.symbol);
        const bestBid = item?.bid1Price ? parseFloat(item.bid1Price) : 0;
        const bestAsk = item?.ask1Price ? parseFloat(item.ask1Price) : 0;
        const mid = (bestBid + bestAsk) / 2;
        const spread = mid > 0 ? ((bestAsk - bestBid) / mid) * 100 : 0;
        const isConnected = bestBid > 0 && bestAsk > 0;

        return {
          symbol: tok.symbol,
          underlying: tok.underlying,
          base_coin: tok.base,
          quote_coin: "USDT",
          status: "online",
          min_order_qty: tok.minQty,
          min_order_amount: tok.minAmt,
          bid: bestBid,
          ask: bestAsk,
          spread_percent: spread,
          market_connected: isConnected,
          connection_status: isConnected ? "CONNECTED" : "UNAVAILABLE",
          quote_freshness: isConnected ? 0.5 : 0.0,
          latest_event: null,
          latest_qwen: null,
          latest_risk: "PENDING_CATALYST",
        };
      });
      return NextResponse.json(results);
    }
  } catch {
    // If external fetch fails, return honest unavailable state
  }

  return NextResponse.json(
    CORE_RTOKENS.map((tok) => ({
      symbol: tok.symbol,
      underlying: tok.underlying,
      base_coin: tok.base,
      quote_coin: "USDT",
      status: "online",
      min_order_qty: tok.minQty,
      min_order_amount: tok.minAmt,
      bid: 0,
      ask: 0,
      spread_percent: 0,
      market_connected: false,
      connection_status: "UNAVAILABLE",
      quote_freshness: 0,
      latest_event: null,
      latest_qwen: null,
      latest_risk: "PENDING_CATALYST",
    }))
  );
}
