import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const symbol = (searchParams.get("symbol") || "RAAPLUSDT").toUpperCase();

  const upstream =
    process.env.AEGIS_BACKEND_URL ||
    (process.env.NODE_ENV === "development" ? "http://127.0.0.1:8000" : undefined);

  if (upstream) {
    try {
      const res = await fetch(
        `${upstream.replace(/\/+$/, "")}/api/market?symbol=${encodeURIComponent(symbol)}`,
        {
          cache: "no-store",
          headers: { Accept: "application/json" },
        }
      );
      if (res.ok) {
        const data = await res.json();
        return NextResponse.json(data);
      }
    } catch {
      // Fall through to direct Bitget fetch
    }
  }

  // Direct fetch from Bitget UTA public tickers
  try {
    const res = await fetch(
      `https://api.bitget.com/api/v3/market/tickers?category=SPOT&symbol=${symbol}`,
      { cache: "no-store" }
    );
    if (res.ok) {
      const payload = await res.json();
      const dataList = payload?.data || [];
      if (dataList.length > 0) {
        const item = dataList[0];
        const bestBid = item.bid1Price ? parseFloat(item.bid1Price) : 0;
        const bestAsk = item.ask1Price ? parseFloat(item.ask1Price) : 0;
        const mid = (bestBid + bestAsk) / 2;
        const spread = mid > 0 ? ((bestAsk - bestBid) / mid) * 100 : 0;
        const isConnected = bestBid > 0 && bestAsk > 0;

        return NextResponse.json({
          asset: symbol,
          symbol: symbol,
          status: "online",
          connected: isConnected,
          is_connected: isConnected,
          bid: bestBid,
          ask: bestAsk,
          spread_percent: Math.max(0, spread),
          quote_freshness: 0.5,
          min_order_qty: 0.0001,
          min_order_amount: 10.0,
          base_coin: symbol.replace("USDT", ""),
          quote_coin: "USDT",
          market_status: "online",
          provider: "Bitget UTA SPOT (Public BBO)",
        });
      }
    }
  } catch {
    // Return honest unavailable
  }

  return NextResponse.json({
    asset: symbol,
    symbol: symbol,
    status: "UNAVAILABLE",
    connected: false,
    is_connected: false,
    bid: 0,
    ask: 0,
    spread_percent: 0,
    quote_freshness: 0,
    min_order_qty: 0.0001,
    min_order_amount: 10.0,
    base_coin: symbol.replace("USDT", ""),
    quote_coin: "USDT",
    market_status: "disconnected",
  });
}
