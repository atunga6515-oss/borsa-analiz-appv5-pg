"use client";
import React, { useEffect, useRef, useState } from 'react';
import { createChart, IChartApi, ISeriesApi, CandlestickSeries, LineSeries, HistogramSeries, createSeriesMarkers } from 'lightweight-charts';

interface LayeredChartProps {
  data: {
    candles: any[]; poc_price: number;
    layers: {
      auto_trend: any[]; supertrend: any[]; alpha_signal: any[]; smc_fvg: any[]; squeeze: any[]; wavetrend: any[];
      divergence: any[]; anchored_vwap: any[]; chandelier: any[]; adx_dmi: any[]; stoch_rsi: any[]; cmf: any[];
      donchian: any[]; ichimoku: any[]; bollinger: any[];
    };
  };
}

type LayerKeys = 'autoTrend' | 'supertrend' | 'alphaSignal' | 'smcFvg' | 'squeeze' | 'wavetrend' | 'divergence' | 'anchoredVwap' | 'volProfilePoc' | 'chandelier' | 'adxDmi' | 'stochRSI' | 'cmf' | 'donchian' | 'ichimoku' | 'bollinger';

export default function LayeredChart({ data }: LayeredChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const markersApiRef = useRef<any>(null);
  
  const [activeLayers, setActiveLayers] = useState<Record<LayerKeys, boolean>>({
    autoTrend: false, supertrend: false, alphaSignal: false, smcFvg: false, squeeze: false, wavetrend: false,
    divergence: false, anchoredVwap: false, volProfilePoc: false, chandelier: false, adxDmi: false, stochRSI: false, cmf: false, donchian: false, ichimoku: false, bollinger: false
  });

  const activeSeriesRef = useRef<Record<string, ISeriesApi<any>>>({});
  const pocLineRef = useRef<any>(null);

  useEffect(() => {
    if (!chartContainerRef.current || !data || !data.candles || data.candles.length === 0) return;

    // 1. SAFELY PURGE AND REMOVE ALL EXISTING INDICATOR SERIES FROM THE CHART BEFORE RESETTING
    if (chartRef.current) {
      // Remove all standard line/histogram indicator series
      Object.values(activeSeriesRef.current).forEach((series) => {
        if (series && chartRef.current) {
          try {
            chartRef.current.removeSeries(series as ISeriesApi<any>);
          } catch (e) {
            console.log("Series already removed or invalid:", e);
          }
        }
      });

      // Remove Volume Profile POC price lines if attached
      if (pocLineRef.current && candleSeriesRef.current) {
        try {
          candleSeriesRef.current.removePriceLine(pocLineRef.current);
        } catch (e) {
          console.log("Price line already removed:", e);
        }
      }

      // 2. DESTROY THE ENTIRE CHART INSTANCE TO ENSURE A 100% CLEAN CANVAS
      chartRef.current.remove();
      chartRef.current = null;
    }

    // 3. RECREATE THE FRESH CHART INSTANCE FOR THE NEW SELECTED TICKER
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth, height: 550,
      layout: { background: { color: '#181a20' }, textColor: '#d1d4dc' },
      grid: { vertLines: { color: '#2b3139' }, horzLines: { color: '#2b3139' } },
      timeScale: { borderColor: '#2b3139', timeVisible: true },
      rightPriceScale: { autoScale: true, borderColor: '#2b3139' }
    });
    chartRef.current = chart;

    const candlestickSeries = chart.addSeries(CandlestickSeries, { upColor: '#26a69a', downColor: '#ef5350', borderVisible: false, wickUpColor: '#26a69a', wickDownColor: '#ef5350' });
    candlestickSeries.setData(data.candles);
    candleSeriesRef.current = candlestickSeries;
    markersApiRef.current = createSeriesMarkers(candlestickSeries, []);
    chart.timeScale().fitContent();

    // Clean structural reset
    setActiveLayers({
      autoTrend: false, supertrend: false, alphaSignal: false, smcFvg: false, squeeze: false, wavetrend: false,
      divergence: false, anchoredVwap: false, volProfilePoc: false, chandelier: false, adxDmi: false, stochRSI: false, cmf: false, donchian: false, ichimoku: false, bollinger: false
    });
    activeSeriesRef.current = {};
    pocLineRef.current = null;

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.resize(chartContainerRef.current.clientWidth, 550);
      }
    };
    window.addEventListener('resize', handleResize);
    return () => { 
      window.removeEventListener('resize', handleResize); 
      if (chartRef.current) {
        try { chartRef.current.remove(); } catch (e) {}
        chartRef.current = null;
      }
    };
  }, [data]);

  const updateMarkersOnChart = (updatedMatrix: Record<LayerKeys, boolean>) => {
    const candleSeries = candleSeriesRef.current;
    if (!candleSeries) return;
    let combined: any[] = [];
    if (updatedMatrix.alphaSignal) combined.push(...data.layers.alpha_signal);
    if (updatedMatrix.smcFvg) combined.push(...data.layers.smc_fvg);
    if (updatedMatrix.divergence) combined.push(...data.layers.divergence);
    combined.sort((a, b) => a.time - b.time);
    if (markersApiRef.current) {
      markersApiRef.current.setMarkers(combined);
    }
  };

  const handleToggle = (key: LayerKeys) => {
    const chart = chartRef.current;
    if (!chart) return;
    const nextState = !activeLayers[key];
    const newMatrix = { ...activeLayers, [key]: nextState };
    setActiveLayers(newMatrix);

    if (key === 'alphaSignal' || key === 'smcFvg' || key === 'divergence') { updateMarkersOnChart(newMatrix); return; }

    if (key === 'volProfilePoc') {
      const candleSeries = candleSeriesRef.current; if (!candleSeries) return;
      if (nextState) { pocLineRef.current = candleSeries.createPriceLine({ price: data.poc_price, color: '#eab308', lineWidth: 2, lineStyle: 2, title: 'POC' }); }
      else if (pocLineRef.current) { candleSeries.removePriceLine(pocLineRef.current); pocLineRef.current = null; }
      return;
    }

    if (nextState) {
      if (key === 'supertrend') { const s = chart.addSeries(LineSeries, { lineWidth: 2, title: 'SuperTrend' }); s.setData(data.layers.supertrend); activeSeriesRef.current[key] = s; }
      if (key === 'autoTrend') { const s = chart.addSeries(LineSeries, { color: '#ff9800', lineWidth: 2, title: 'Auto Trend' }); s.setData(data.layers.auto_trend); activeSeriesRef.current[key] = s; }
      if (key === 'anchoredVwap') { const s = chart.addSeries(LineSeries, { color: '#2563eb', lineWidth: 2, title: 'AVWAP' }); s.setData(data.layers.anchored_vwap); activeSeriesRef.current[key] = s; }
      if (key === 'chandelier') { const s = chart.addSeries(LineSeries, { color: '#ea580c', lineWidth: 1, lineStyle: 3, title: 'Chandelier' }); s.setData(data.layers.chandelier); activeSeriesRef.current[key] = s; }
      if (key === 'donchian') {
        const u = chart.addSeries(LineSeries, { color: '#a855f7', lineWidth: 1, title: 'Donchian U' }); u.setData(data.layers.donchian.map(v => ({ time: v.time, value: v.upper }))); activeSeriesRef.current['donU'] = u;
        const l = chart.addSeries(LineSeries, { color: '#a855f7', lineWidth: 1, title: 'Donchian L' }); l.setData(data.layers.donchian.map(v => ({ time: v.time, value: v.lower }))); activeSeriesRef.current['donL'] = l;
      }
      if (key === 'ichimoku') {
        const a = chart.addSeries(LineSeries, { color: '#22c55e', lineWidth: 1, lineStyle: 2, title: 'Senkou A' }); a.setData(data.layers.ichimoku.filter(v => v.span_a !== null).map(v => ({ time: v.time, value: v.span_a }))); activeSeriesRef.current['ichiA'] = a;
        const b = chart.addSeries(LineSeries, { color: '#ef4444', lineWidth: 1, lineStyle: 2, title: 'Senkou B' }); b.setData(data.layers.ichimoku.filter(v => v.span_b !== null).map(v => ({ time: v.time, value: v.span_b }))); activeSeriesRef.current['ichiB'] = b;
      }
      if (key === 'bollinger') {
        const u = chart.addSeries(LineSeries, { color: '#10b981', lineWidth: 1, title: 'BB Upper' }); u.setData(data.layers.bollinger.map(v => ({ time: v.time, value: v.upper }))); activeSeriesRef.current['bbU'] = u;
        const l = chart.addSeries(LineSeries, { color: '#10b981', lineWidth: 1, title: 'BB Lower' }); l.setData(data.layers.bollinger.map(v => ({ time: v.time, value: v.lower }))); activeSeriesRef.current['bbL'] = l;
      }
      // Isolated Scale Oscillators Pane (Strict non-overlapping margins)
      if (key === 'squeeze') { const s = chart.addSeries(HistogramSeries, { priceScaleId: 'sqz_s', title: 'Squeeze' }); chart.priceScale('sqz_s').applyOptions({ scaleMargins: { top: 0.80, bottom: 0.16 } }); s.setData(data.layers.squeeze); activeSeriesRef.current[key] = s; }
      if (key === 'wavetrend') { const s = chart.addSeries(LineSeries, { color: '#00ffff', priceScaleId: 'wt_s', title: 'WT1' }); chart.priceScale('wt_s').applyOptions({ scaleMargins: { top: 0.84, bottom: 0.12 } }); s.setData(data.layers.wavetrend.map(v => ({ time: v.time, value: v.wt1 }))); activeSeriesRef.current[key] = s; }
      if (key === 'adxDmi') { const s = chart.addSeries(LineSeries, { color: '#ffffff', priceScaleId: 'adx_s', title: 'ADX' }); chart.priceScale('adx_s').applyOptions({ scaleMargins: { top: 0.88, bottom: 0.08 } }); s.setData(data.layers.adx_dmi.map(v => ({ time: v.time, value: v.adx }))); activeSeriesRef.current[key] = s; }
      if (key === 'stochRSI') { const s = chart.addSeries(LineSeries, { color: '#3b82f6', priceScaleId: 'st_s', title: '%K' }); chart.priceScale('st_s').applyOptions({ scaleMargins: { top: 0.92, bottom: 0.04 } }); s.setData(data.layers.stoch_rsi.map(v => ({ time: v.time, value: v.k }))); activeSeriesRef.current[key] = s; }
      if (key === 'cmf') { const s = chart.addSeries(HistogramSeries, { priceScaleId: 'cmf_s', title: 'CMF' }); chart.priceScale('cmf_s').applyOptions({ scaleMargins: { top: 0.96, bottom: 0.00 } }); s.setData(data.layers.cmf.map(v => ({ time: v.time, value: v.value, color: v.value >= 0 ? 'rgba(34,197,94,0.5)' : 'rgba(239,68,68,0.5)' }))); activeSeriesRef.current[key] = s; }
    } else {
      if (activeSeriesRef.current[key]) { chart.removeSeries(activeSeriesRef.current[key]); delete activeSeriesRef.current[key]; }
      if (key === 'donchian') { chart.removeSeries(activeSeriesRef.current['donU']); chart.removeSeries(activeSeriesRef.current['donL']); delete activeSeriesRef.current['donU']; delete activeSeriesRef.current['donL']; }
      if (key === 'ichimoku') { chart.removeSeries(activeSeriesRef.current['ichiA']); chart.removeSeries(activeSeriesRef.current['ichiB']); delete activeSeriesRef.current['ichiA']; delete activeSeriesRef.current['ichiB']; }
      if (key === 'bollinger') { chart.removeSeries(activeSeriesRef.current['bbU']); chart.removeSeries(activeSeriesRef.current['bbL']); delete activeSeriesRef.current['bbU']; delete activeSeriesRef.current['bbL']; }
    }
  };

  const renderButton = (key: LayerKeys, label: string, colorClass: string, tooltipText: string) => (
    <div className="relative group inline-block">
      <button onClick={() => handleToggle(key)} className={`px-3 py-1.5 rounded text-xs font-bold transition-all border ${activeLayers[key] ? `${colorClass} text-white shadow-md` : 'bg-[#2b3139] text-gray-400 border-transparent hover:text-white'}`}>
        {label}
      </button>
      <div className="absolute hidden group-hover:block bg-[#1c2030] text-gray-200 text-xs rounded p-2 min-w-[220px] max-w-[280px] top-full left-4 mt-2 z-50 shadow-xl border border-gray-700 pointer-events-none">
        {tooltipText}
        <div className="absolute -top-2 left-4 border-4 border-transparent border-b-[#1c2030]" />
      </div>
    </div>
  );

  return (
    <div className="w-full flex flex-col bg-[#1e2329] p-4 rounded-lg border border-gray-800">
      <div className="flex flex-wrap gap-2 mb-4 bg-[#181a20] p-2 rounded border border-gray-800">
        {renderButton('autoTrend', '✍️ Auto Trend', 'bg-amber-600 border-amber-400', 'Grafikteki en son pivot tepe ve dip noktalarını birleştirerek mekanik destek/direnç hatları çizer.')}
        {renderButton('supertrend', '📈 SuperTrend', 'bg-emerald-600 border-emerald-400', 'Fiyat oynaklığını (ATR) baz alarak trend yönünü yeşil veya kırmızı bir takip çizgisiyle izler.')}
        {renderButton('alphaSignal', '✨ Alpha Signal', 'bg-purple-600 border-purple-400', '9 ve 21 periyotluk hareketli ortalamaların momentum kesişimlerine göre onaylı giriş-çıkış sinyalleri üretir.')}
        {renderButton('smcFvg', '🔍 SMC (FVG)', 'bg-teal-600 border-teal-400', 'Kurumsal alıcıların geride bıraktığı yapısal adil değer boşluklarını ve dengesizlik alanlarını saptar.')}
        {renderButton('squeeze', '📊 Squeeze Mom.', 'bg-rose-600 border-rose-400', 'Bollinger Bantları ile Keltner Kanalları arasındaki fiyat sıkışmasını ve patlama ivmesini ölçer.')}
        {renderButton('wavetrend', '🌊 WaveTrend', 'bg-cyan-600 border-cyan-400', 'Aşırı alım ve satım bölgelerindeki döngüsel dalga dönüşlerini hassas bir şekilde yakalar.')}
        {renderButton('divergence', '🔀 Divergence', 'bg-yellow-600 border-yellow-400', 'Fiyat ile RSI osilatörü arasındaki uyumsuzlukları bularak erken trend dönüş uyanışları üretir.')}
        {renderButton('anchoredVwap', '⚓ Anchored VWAP', 'bg-blue-600 border-blue-400', 'Belirlenen kritik bir geçmiş dipten itibaren hacim ağırlıklı ortalama kurumsal maliyeti hesaplar.')}
        {renderButton('volProfilePoc', '🧱 Vol. Profile POC', 'bg-orange-600 border-orange-400', 'Hissenin tüm zaman diliminde en yüksek işlem hacmine ulaştığı en güçlü takoz fiyat seviyesini çizer.')}
        {renderButton('chandelier', '🪂 Chandelier Exit', 'bg-red-600 border-red-400', 'En yüksek fiyattan ATR kadar aşağıya dinamik stop yerleştirerek kârı ralli boyunca korur.')}
        {renderButton('adxDmi', '📊 ADX & DMI', 'bg-neutral-600 border-neutral-400', 'Trendin yönünü, alıcı ve satıcıların gerçek savaş gücünün trendi başlatıp başlatamayacağını ölçer.')}
        {renderButton('stochRSI', '⚡ Stoch RSI', 'bg-indigo-600 border-indigo-400', 'Klasik RSI indikatörünü hızlandırarak dipten kalkış dalgalarını en erken aşamada yakalar.')}
        {renderButton('cmf', '💵 Chaikin CMF', 'bg-green-700 border-green-500', 'Hisse fiyatı yatay kalırken arkada kurumsal bir gizli toplama (para girişi) olup olmadığını süzgeçten geçirir.')}
        {renderButton('donchian', '🧱 Donchian Channels', 'bg-violet-600 border-violet-400', 'Belirlenen periyottaki en yüksek zirve kırılımını saptayarak momentum rüzgarını arkana almanı sağlar.')}
        {renderButton('ichimoku', '☁️ Ichimoku Kumo', 'bg-rose-700 border-rose-500', 'Fiyatın Japon bulut yapısını (Kumo) yukarı yönlü yırtarak dirençsiz alana geçişini yakalar.')}
        {renderButton('bollinger', '🔘 Bollinger Bands', 'bg-sky-600 border-sky-400', 'Fiyatın standart sapma sınırlarını çizerek istatistiksel olarak aşırı sarsıldığı fiyat alanlarını bulur.')}
      </div>
      <div ref={chartContainerRef} className="w-full h-[550px]" />
    </div>
  );
}
