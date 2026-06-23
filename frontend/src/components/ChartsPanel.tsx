"use client";

import dynamic from "next/dynamic";
import type { ChartDefinition } from "@/types/profile";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

function axisDataLength(axis: unknown) {
  const axisList = Array.isArray(axis) ? axis : [axis];
  return axisList.reduce((maxLength, item) => {
    if (!item || typeof item !== "object" || !("data" in item)) return maxLength;
    const data = (item as { data?: unknown }).data;
    return Math.max(maxLength, Array.isArray(data) ? data.length : 0);
  }, 0);
}

function chartWidth(option: ChartDefinition["option"]) {
  const categoryCount = Math.max(axisDataLength(option.xAxis), axisDataLength(option.yAxis));
  if (categoryCount <= 14) return "100%";
  return Math.min(3600, Math.max(860, categoryCount * 64));
}

export function ChartsPanel({ charts }: { charts: ChartDefinition[] }) {
  return (
    <section className="chart-grid">
      {charts.map((chart) => (
        <article key={chart.id} className="chart-card">
          <h3>{chart.title}</h3>
          <p>{chart.description}</p>
          <div className="chart-scroll">
            <div className="chart-canvas" style={{ width: chartWidth(chart.option) }}>
              <ReactECharts option={chart.option} style={{ height: 280, width: "100%" }} />
            </div>
          </div>
        </article>
      ))}
    </section>
  );
}
