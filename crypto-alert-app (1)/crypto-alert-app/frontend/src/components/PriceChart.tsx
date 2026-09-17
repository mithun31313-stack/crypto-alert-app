import { useEffect, useRef } from "react";
import { createChart, ColorType, type IChartApi } from "lightweight-charts";

type Candle = { open_time: string; open: number; high: number; low: number; close: number; volume: number };

export default function PriceChart({ candles, height = 320 }: { candles: Candle[]; height?: number }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const chart = createChart(containerRef.current, {
      height,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#8892A0",
        fontFamily: "IBM Plex Mono, monospace",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: "#1C222B" },
        horzLines: { color: "#1C222B" },
      },
      rightPriceScale: { borderColor: "#232933" },
      timeScale: { borderColor: "#232933" },
    });
    const series = chart.addCandlestickSeries({
      upColor: "#35C488", downColor: "#E2574C",
      borderVisible: false,
      wickUpColor: "#35C488", wickDownColor: "#E2574C",
    });
    series.setData(
      candles.map((c) => ({
        time: (new Date(c.open_time).getTime() / 1000) as any,
        open: c.open, high: c.high, low: c.low, close: c.close,
      }))
    );
    chart.timeScale().fitContent();
    chartRef.current = chart;

    const resize = () => chart.applyOptions({ width: containerRef.current!.clientWidth });
    resize();
    window.addEventListener("resize", resize);
    return () => {
      window.removeEventListener("resize", resize);
      chart.remove();
    };
  }, [candles, height]);

  return <div ref={containerRef} style={{ width: "100%" }} />;
}
