import {
  Component,
  OnInit,
  OnDestroy,
  OnChanges,
  AfterViewInit,
  SimpleChanges,
  Input,
  ElementRef,
  ViewChild,
  inject,
  signal,
  computed,
  effect,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  createChart,
  IChartApi,
  ISeriesApi,
  CandlestickSeries,
  LineSeries,
  HistogramSeries,
  ColorType,
  CrosshairMode,
  LineStyle,
} from 'lightweight-charts';
import { isPlatformBrowser } from '@angular/common';
import { Inject, PLATFORM_ID } from '@angular/core';

// ─── Domain types ────────────────────────────────────────────────────────────

export interface OhlcvBar {
  date: string;     // "2024-01-15" — ISO date from your /price-history/ endpoint
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface IndicatorRow {
  date: string;
  sma_20?: number | null;
  sma_50?: number | null;
  ema_12?: number | null;
  ema_26?: number | null;
  rsi?: number | null;
  macd?: number | null;
  macd_signal?: number | null;
  macd_hist?: number | null;
  bb_upper?: number | null;
  bb_lower?: number | null;
  bb_middle?: number | null;
  vwap?: number | null;
}

export type OverlayKey = 'sma_20' | 'sma_50' | 'ema_12' | 'ema_26' | 'bb_upper' | 'bb_lower' | 'bb_middle' | 'vwap';
export type PaneIndicator = 'rsi' | 'macd' | 'volume';

interface OverlayConfig {
  key: OverlayKey;
  label: string;
  color: string;
}

interface PaneConfig {
  key: PaneIndicator;
  label: string;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function toTime(dateStr: string): number {
  // Lightweight Charts v4 needs UTC epoch seconds
  return Math.floor(new Date(dateStr).getTime() / 1000);
}

function toCandle(bar: OhlcvBar) {
  return {
    time: toTime(bar.date) as any,
    open: bar.open,
    high: bar.high,
    low: bar.low,
    close: bar.close,
  };
}

function toLine(row: IndicatorRow, key: OverlayKey) {
  const value = row[key];
  if (value == null) return null;
  return { time: toTime(row.date) as any, value };
}

function toVolume(bar: OhlcvBar) {
  return {
    time: toTime(bar.date) as any,
    value: bar.volume,
    color: bar.close >= bar.open ? 'rgba(38, 166, 154, 0.4)' : 'rgba(239, 83, 80, 0.4)',
  };
}

// ─── Component ───────────────────────────────────────────────────────────────

@Component({
  selector: 'app-chart-widget',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './chart.component.html',
  styleUrl: './chart.component.scss',
})
export class ChartWidgetComponent implements AfterViewInit, OnChanges, OnDestroy {
  // ── Inputs ────────────────────────────────────────────────────────────────

  /** Raw OHLCV array from /api/stock/{symbol}/price-history/ */
  @Input() ohlcv: OhlcvBar[] = [];

  /** Latest indicator rows from /api/technical/{symbol}/indicators */
  @Input() indicators: IndicatorRow[] = [];

  /** Symbol display label */
  @Input() symbol = '';

  /** Timeframe label (cosmetic only) */
  @Input() timeframe = '6mo';

  // ── Chart container refs ──────────────────────────────────────────────────

  @ViewChild('mainChart', { static: false }) mainChartRef!: ElementRef<HTMLDivElement>;
  @ViewChild('subChart', { static: false }) subChartRef!: ElementRef<HTMLDivElement>;

  // ── UI state (signals) ────────────────────────────────────────────────────

  activeOverlays = signal<Set<OverlayKey>>(new Set(['sma_20', 'sma_50']));
  activePane = signal<PaneIndicator>('volume');

  overlayConfigs: OverlayConfig[] = [
    { key: 'sma_20',    label: 'SMA 20',   color: '#F59E0B' },
    { key: 'sma_50',    label: 'SMA 50',   color: '#3B82F6' },
    { key: 'ema_12',    label: 'EMA 12',   color: '#8B5CF6' },
    { key: 'ema_26',    label: 'EMA 26',   color: '#EC4899' },
    { key: 'bb_upper',  label: 'BB Upper', color: '#6B7280' },
    { key: 'bb_lower',  label: 'BB Lower', color: '#6B7280' },
    { key: 'vwap',      label: 'VWAP',     color: '#10B981' },
  ];

  paneConfigs: PaneConfig[] = [
    { key: 'volume', label: 'Volume' },
    { key: 'rsi',    label: 'RSI' },
    { key: 'macd',   label: 'MACD' },
  ];

  crosshairPrice = signal<string>('');
  crosshairDate  = signal<string>('');
  crosshairData  = signal<{ o: string; h: string; l: string; c: string; v: string } | null>(null);

  // ── Private chart state ───────────────────────────────────────────────────

  private mainChart!: IChartApi;
  private subChart!: IChartApi;

  private candleSeries!: ISeriesApi<'Candlestick'>;
  private overlaySeries = new Map<OverlayKey, ISeriesApi<'Line'>>();
  private volumeSeries!: ISeriesApi<'Histogram'>;
  private rsiSeries!: ISeriesApi<'Line'>;
  private macdLineSeries!: ISeriesApi<'Line'>;
  private macdSignalSeries!: ISeriesApi<'Line'>;
  private macdHistSeries!: ISeriesApi<'Histogram'>;

  private ro!: ResizeObserver;
  private ohlcvByTime = new Map<number, OhlcvBar>();

  constructor(@Inject(PLATFORM_ID) private platformId: Object) {}

  // ── Lifecycle ─────────────────────────────────────────────────────────────

  ngAfterViewInit(): void {
    if (!isPlatformBrowser(this.platformId)) return;
    
    this.buildCharts();   // ✅ only runs in browser
    
    this.applyOhlcv();
    this.applyAllOverlays();
    this.applyPane(this.activePane());
    this.watchResize();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (!this.mainChart) return; // not yet initialised

    if (changes['ohlcv']) {
      this.applyOhlcv();
    }
    if (changes['indicators']) {
      this.applyAllOverlays();
      this.applyPane(this.activePane());
    }
  }

  ngOnDestroy(): void {
    this.ro?.disconnect();
    this.mainChart?.remove();
    this.subChart?.remove();
  }

  // ── Public UI handlers ────────────────────────────────────────────────────

  toggleOverlay(key: OverlayKey): void {
    const set = new Set(this.activeOverlays());
    if (set.has(key)) {
      set.delete(key);
      this.hideSeries(key);
    } else {
      set.add(key);
      this.showSeries(key);
    }
    this.activeOverlays.set(set);
  }

  isOverlayActive(key: OverlayKey): boolean {
    return this.activeOverlays().has(key);
  }

  selectPane(key: PaneIndicator): void {
    this.activePane.set(key);
    this.applyPane(key);
  }

  overlayColor(key: OverlayKey): string {
    return this.overlayConfigs.find(c => c.key === key)?.color ?? '#fff';
  }

  // ── Chart construction ────────────────────────────────────────────────────

  private buildCharts(): void {
    if (typeof window === 'undefined') return;
    const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    const sharedLayout = {
      background:   { type: ColorType.Solid, color: 'transparent' },
      textColor:    isDark ? '#9CA3AF' : '#6B7280',
      fontSize:     11,
    };

    // Main price chart
    this.mainChart = createChart(this.mainChartRef.nativeElement, {
      autoSize: true, 
      layout: sharedLayout,
      grid: {
        vertLines: { color: isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)' },
        horzLines: { color: isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)' },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: { labelBackgroundColor: isDark ? '#374151' : '#F3F4F6' },
        horzLine: { labelBackgroundColor: isDark ? '#374151' : '#F3F4F6' },
      },
      rightPriceScale: {
        borderVisible: false,
        scaleMargins: { top: 0.1, bottom: 0.08 },
      },
      timeScale: {
        borderVisible: false,
        timeVisible: true,
        fixRightEdge: true,
        fixLeftEdge: true,
      },
      handleScroll: { mouseWheel: true, pressedMouseMove: true },
      handleScale:  { mouseWheel: true, pinch: true, axisPressedMouseMove: true },
    });

    // Sub indicator chart
    this.subChart = createChart(this.subChartRef.nativeElement, {
      layout: sharedLayout,
      autoSize: true, 
      grid: {
        vertLines: { visible: false },
        horzLines: { color: isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)' },
      },
      rightPriceScale: {
        borderVisible: false,
        scaleMargins: { top: 0.1, bottom: 0.1 },
      },
      timeScale: {
        borderVisible: false,
        timeVisible: true,
        visible: false, // hidden — synced from main
      },
      crosshair: { mode: CrosshairMode.Normal },
    });

    // Sync sub-chart time range with main
    this.mainChart.timeScale().subscribeVisibleLogicalRangeChange(range => {
      if (range) this.subChart.timeScale().setVisibleLogicalRange(range);
    });
    this.subChart.timeScale().subscribeVisibleLogicalRangeChange(range => {
      if (range) this.mainChart.timeScale().setVisibleLogicalRange(range);
    });

    this.buildSeries();
    this.bindCrosshair();
  }

  private buildSeries(): void {
    // Candlestick
    this.candleSeries = this.mainChart.addSeries(CandlestickSeries, {
      upColor:          '#26a69a',
      downColor:        '#ef5350',
      borderUpColor:    '#26a69a',
      borderDownColor:  '#ef5350',
      wickUpColor:      '#26a69a',
      wickDownColor:    '#ef5350',
    });

    // Overlay line series (created for all, shown/hidden by toggle)
    for (const cfg of this.overlayConfigs) {
      const s = this.mainChart.addSeries(LineSeries, {
        color:      cfg.color,
        lineWidth:  1,
        priceLineVisible: false,
        lastValueVisible: false,
        crosshairMarkerVisible: false,
        lineStyle: cfg.key.startsWith('bb') ? LineStyle.Dashed : LineStyle.Solid,
        visible: this.activeOverlays().has(cfg.key),
      });
      this.overlaySeries.set(cfg.key, s);
    }

    // Sub-chart series — volume (default visible)
    this.volumeSeries = this.subChart.addSeries(HistogramSeries, {
      priceFormat:     { type: 'volume' },
      priceScaleId:    'volume',
    });

    // RSI
    this.rsiSeries = this.subChart.addSeries(LineSeries, {
      color:     '#8B5CF6',
      lineWidth: 1,
      priceLineVisible: false,
      lastValueVisible: true,
      visible: false,
    });

    // MACD
    this.macdLineSeries = this.subChart.addSeries(LineSeries, {
      color: '#3B82F6', lineWidth: 1, priceLineVisible: false,
      lastValueVisible: false, visible: false,
    });
    this.macdSignalSeries = this.subChart.addSeries(LineSeries, {
      color: '#F59E0B', lineWidth: 1, priceLineVisible: false,
      lastValueVisible: false, visible: false,
    });
    this.macdHistSeries = this.subChart.addSeries(HistogramSeries, {
      priceLineVisible: false, lastValueVisible: false, visible: false,
    });
  }

  // ── Data application ──────────────────────────────────────────────────────

  // Update applyOhlcv() to rebuild the map:
private applyOhlcv(): void {
  if (!this.ohlcv?.length) return;

  const sorted = [...this.ohlcv].sort((a, b) => a.date.localeCompare(b.date));
  const mappedData = sorted.map(toCandle);
  console.log('Mapped Chart Data:', mappedData); 
  try {
    this.candleSeries.setData(mappedData);
    console.log('setData SUCCEEDED!'); // ADD THIS
  } catch (error) {
    console.error('Lightweight Charts Error:', error); // THIS WILL CATCH SILENT CRASHES
  }

  // Rebuild crosshair lookup map with fresh data ← ADD THIS
  this.ohlcvByTime.clear();
  for (const bar of sorted) {
    this.ohlcvByTime.set(toTime(bar.date), bar);
  }

  if (this.activePane() === 'volume') {
    this.volumeSeries.setData(sorted.map(toVolume));
  }

  this.mainChart.timeScale().fitContent();
}

  private applyAllOverlays(): void {
    if (!this.indicators?.length) return;
    if (this.indicators.length < 2) {
    console.warn('Only 1 indicator row received — overlays need full history from backend');
    return;
  }
    const sorted = [...this.indicators].sort((a, b) => a.date.localeCompare(b.date));

    for (const cfg of this.overlayConfigs) {
      const series = this.overlaySeries.get(cfg.key);
      if (!series) continue;
      const points = sorted.map(r => toLine(r, cfg.key)).filter(Boolean) as any[];
      series.setData(points);
    }
  }

  private applyPane(key: PaneIndicator): void {
    if (!this.ohlcv?.length && !this.indicators?.length) return;

    // Hide all sub-chart series first
    this.volumeSeries.applyOptions({ visible: false });
    this.rsiSeries.applyOptions({ visible: false });
    this.macdLineSeries.applyOptions({ visible: false });
    this.macdSignalSeries.applyOptions({ visible: false });
    this.macdHistSeries.applyOptions({ visible: false });

    const sortedOhlcv  = [...(this.ohlcv || [])].sort((a, b) => a.date.localeCompare(b.date));
    const sortedInds   = [...(this.indicators || [])].sort((a, b) => a.date.localeCompare(b.date));

    if (key === 'volume') {
      this.volumeSeries.applyOptions({ visible: true });
      this.volumeSeries.setData(sortedOhlcv.map(toVolume));
    }

    if (key === 'rsi') {
      this.rsiSeries.applyOptions({ visible: true });
      const pts = sortedInds
        .map(r => r.rsi != null ? { time: toTime(r.date) as any, value: r.rsi! } : null)
        .filter(Boolean) as any[];
      this.rsiSeries.setData(pts);
    }

    if (key === 'macd') {
      this.macdLineSeries.applyOptions({ visible: true });
      this.macdSignalSeries.applyOptions({ visible: true });
      this.macdHistSeries.applyOptions({ visible: true });

      const macdPts   = sortedInds.map(r => r.macd        != null ? { time: toTime(r.date) as any, value: r.macd!        } : null).filter(Boolean) as any[];
      const sigPts    = sortedInds.map(r => r.macd_signal  != null ? { time: toTime(r.date) as any, value: r.macd_signal! } : null).filter(Boolean) as any[];
      const histPts   = sortedInds.map(r => r.macd_hist    != null ? {
        time: toTime(r.date) as any,
        value: r.macd_hist!,
        color: r.macd_hist! >= 0 ? 'rgba(38,166,154,0.7)' : 'rgba(239,83,80,0.7)',
      } : null).filter(Boolean) as any[];

      this.macdLineSeries.setData(macdPts);
      this.macdSignalSeries.setData(sigPts);
      this.macdHistSeries.setData(histPts);
    }
  }

  // ── Series visibility ─────────────────────────────────────────────────────

  private showSeries(key: OverlayKey): void {
    this.overlaySeries.get(key)?.applyOptions({ visible: true });
  }

  private hideSeries(key: OverlayKey): void {
    this.overlaySeries.get(key)?.applyOptions({ visible: false });
  }

  // ── Crosshair tooltip ─────────────────────────────────────────────────────

  private bindCrosshair(): void {
  // Remove the local ohlcvByTime map that was here — now uses this.ohlcvByTime
  this.mainChart.subscribeCrosshairMove(param => {
    if (!param.time) {
      this.crosshairData.set(null);
      return;
    }
    const t = param.time as number;
    const bar = this.ohlcvByTime.get(t);   // ← uses class field
    if (bar) {
      this.crosshairData.set({
        o: bar.open.toFixed(2),
        h: bar.high.toFixed(2),
        l: bar.low.toFixed(2),
        c: bar.close.toFixed(2),
        v: (bar.volume / 1_000_000).toFixed(2) + 'M',
      });
      const d = new Date(t * 1000);
      this.crosshairDate.set(d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }));
    }
  });
}

  // ── Responsive resize ─────────────────────────────────────────────────────

  private watchResize(): void {
    if (typeof window === 'undefined' || typeof ResizeObserver === 'undefined') return;
    this.ro = new ResizeObserver(entries => {
      const width = entries[0]?.contentRect.width;
      if (!width) return;
      this.mainChart.applyOptions({ width });
      this.subChart.applyOptions({ width });
    });
    this.ro.observe(this.mainChartRef.nativeElement.parentElement!);
  }
}