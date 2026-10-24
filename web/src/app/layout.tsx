import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Fundly | AI Marketing Agent",
  description: "A local demo marketing workspace for the Fundly brand.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
