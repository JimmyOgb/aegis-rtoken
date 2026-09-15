import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET() {
  const upstream = process.env.AEGIS_BACKEND_URL;
  if (upstream) {
    try {
      const res = await fetch(`${upstream.replace(/\/+$/, "")}/api/circuit-breaker`, {
        cache: "no-store",
        headers: { Accept: "application/json" },
      });
      if (res.ok) {
        const data = await res.json();
        return NextResponse.json(data);
      }
    } catch {
      // Fall through to default armed state
    }
  }

  return NextResponse.json({
    is_tripped: false,
    consecutive_faults: 0,
    trip_reason: null,
    remaining_cooldown_seconds: 0,
  });
}
