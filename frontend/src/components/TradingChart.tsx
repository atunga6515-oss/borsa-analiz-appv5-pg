"use client";

import { useEffect, useRef } from "react";
import { createChart, ColorType, CandlestickSeries, LineSeries, createSeriesMarkers } from "lightweight-charts";

interface ChartData {
  time: string | number;
  open: number;
  high: number;
  low: number;
  close: number;
  sma20?: number;
  ema50?: number;
  signal?: "AL" | "SAT" | null;
}

export default function TradingChart({ data }: { data: ChartData[] }) {
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

        // Add SMA20 Line Series
        const smaSeries = chart.addSeries(LineSeries, {
            color: '#2962FF',
            lineWidth: 2,
            title: 'SMA 20',
        });

        // Add EMA50 Line Series
        const emaSeries = chart.addSeries(LineSeries, {
            color: '#FF6D00',
            lineWidth: 2,
            title: 'EMA 50',
        });

        if (data && data.length > 0) {
            candlestickSeries.setData(data as any);
            
            const smaData = data.filter((d: any) => d.sma20).map((d: any) => ({ time: d.time, value: d.sma20 }));
            if (smaData.length > 0) smaSeries.setData(smaData);
            
            const emaData = data.filter((d: any) => d.ema50).map((d: any) => ({ time: d.time, value: d.ema50 }));
            if (emaData.length > 0) emaSeries.setData(emaData);

            // Add Markers (AL/SAT signals)
            const markers: any[] = [];
            data.forEach((d) => {
                if (d.signal === "AL") {
                    markers.push({
                        time: d.time,
                        position: 'belowBar',
                        color: '#0ecb81',
                        shape: 'arrowUp',
                        text: 'AL',
                        size: 2
                    });
                } else if (d.signal === "SAT") {
                    markers.push({
                        time: d.time,
                        position: 'aboveBar',
                        color: '#f6465d',
                        shape: 'arrowDown',
                        text: 'SAT',
                        size: 2
                    });
                }
            });
            
            if (markers.length > 0) {
                createSeriesMarkers(candlestickSeries, markers);
            }
        }

        window.addEventListener("resize", handleResize);

        return () => {
            window.removeEventListener("resize", handleResize);
            chart.remove();
        };
    }, [data]);

    return (
        <div className="w-full h-full min-h-[500px]" ref={chartContainerRef} />
    );
}
