import { NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const symbol = searchParams.get("symbol");
  const limit = searchParams.get("limit") || "25";

  const upstream = process.env.AEGIS_BACKEND_URL;
  if (upstream) {
    try {
      const q = new URLSearchParams();
      if (symbol) q.set("symbol", symbol);
      q.set("limit", limit);
      const res = await fetch(`${upstream.replace(/\/+$/, "")}/api/decisions?${q.toString()}`, {
        cache: "no-store",
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        const data = await res.json();
        return NextResponse.json(data);
      }
    } catch {
      // Fall through to empty genuine list
    }
  }

  // Zero-mock policy: return empty list when no persistent decision database is attached
  return NextResponse.json([]);
}
