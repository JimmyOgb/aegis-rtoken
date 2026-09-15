import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AegisrToken — Autonomous Event-Driven Sentinel",
  description:
    "AegisrToken is an autonomous event-driven sentinel for tokenized U.S. equity markets, combining real market data, Bitget Qwen intelligence, deterministic risk controls, and Demo/Paper Trading safeguards.",
  openGraph: {
    title: "AegisrToken — Autonomous Event-Driven Sentinel",
    description:
      "AegisrToken is an autonomous event-driven sentinel for tokenized U.S. equity markets, combining real market data, Bitget Qwen intelligence, deterministic risk controls, and Demo/Paper Trading safeguards.",
    siteName: "AegisrToken",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "AegisrToken — Autonomous Event-Driven Sentinel",
    description:
      "AegisrToken is an autonomous event-driven sentinel for tokenized U.S. equity markets, combining real market data, Bitget Qwen intelligence, deterministic risk controls, and Demo/Paper Trading safeguards.",
  },
  icons: {
    icon: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 antialiased selection:bg-cyan-500/20 selection:text-cyan-300">
        {children}
      </body>
    </html>
  );
}
