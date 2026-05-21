import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Counter Escrow Console",
  description: "AI diligence and escrow workflow console for real estate transactions.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
