"use client";

import dynamic from "next/dynamic";
import type { ChartDefinition } from "@/types/profile";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

export function ChartsPanel({ charts }: { charts: ChartDefinition[] }) {
  return (
    <section className="chart-grid">
      {charts.map((chart) => (
        <article key={chart.id} className="chart-card">
          <h3>{chart.title}</h3>
          <p>{chart.description}</p>
          <ReactECharts option={chart.option} style={{ height: 280, width: "100%" }} />
        </article>
      ))}
    </section>
  );
}

