import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Data Profiler AI",
  description: "Automatic data profiling, quality diagnostics and model recommendation."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>
        <div className="grain" />
        {children}
      </body>
    </html>
  );
}

