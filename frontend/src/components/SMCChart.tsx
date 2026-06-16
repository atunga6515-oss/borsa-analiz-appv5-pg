"use client";

import { useEffect, useRef } from "react";
import { createChart, ColorType, CandlestickSeries, LineStyle } from "lightweight-charts";

interface SMCChartData {
  time: string | number;
  open: number;
  high: number;
  low: number;
  close: number;
}

interface SMCChartProps {
  data: SMCChartData[];
  lastPeak: number | null;
  lastTrough: number | null;
}

export default function SMCChart({ data, lastPeak, lastTrough }: SMCChartProps) {
    const chartContainerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!chartContainerRef.current) return;

        const handleResize = () => {
            chart.applyOptions({ width: chartContainerRef.current?.clientWidth || 0 });
        };

        const chart = createChart(chartContainerRef.current, {
            layout: {
                background: { type: ColorType.Solid, color: "transparent" },
                textColor: "#848e9c",
            },
            grid: {
                vertLines: { color: "#2b3139", style: 1 },
                horzLines: { color: "#2b3139", style: 1 },
            },
            width: chartContainerRef.current.clientWidth,
            height: chartContainerRef.current.clientHeight || 500,
            rightPriceScale: {
                borderColor: "#2b3139",
            },
            timeScale: {
                borderColor: "#2b3139",
                timeVisible: true,
            },
            crosshair: {
                mode: 1, // Magnet mode
                vertLine: { color: '#848e9c', labelBackgroundColor: '#181a20' },
                horzLine: { color: '#848e9c', labelBackgroundColor: '#181a20' },
            }
        });

        const candlestickSeries = chart.addSeries(CandlestickSeries, {
            upColor: "#0ecb81",
            downColor: "#f6465d",
            borderVisible: false,
            wickUpColor: "#0ecb81",
            wickDownColor: "#f6465d",
        });

        if (data && data.length > 0) {
            candlestickSeries.setData(data as any);
        }

        // Add SMC Level Lines
        if (lastPeak) {
            candlestickSeries.createPriceLine({
                price: lastPeak,
                color: '#f6465d',
                lineWidth: 2,
                lineStyle: LineStyle.Dashed,
                axisLabelVisible: true,
                title: 'BOS Kırılım Zirvesi',
            });
        }

        if (lastTrough) {
            candlestickSeries.createPriceLine({
                price: lastTrough,
                color: '#0ecb81',
                lineWidth: 2,
                lineStyle: LineStyle.Dashed,
                axisLabelVisible: true,
                title: 'Dip Destek',
            });
        }

        window.addEventListener("resize", handleResize);

        return () => {
            window.removeEventListener("resize", handleResize);
            chart.remove();
        };
    }, [data, lastPeak, lastTrough]);

    return (
        <div className="w-full h-full relative" ref={chartContainerRef} />
    );
}
