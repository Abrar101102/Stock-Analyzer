import { Component, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators, FormGroup } from '@angular/forms';
import { forkJoin, finalize, catchError, of } from 'rxjs';
import { StockApi, NewsResponse, NewsArticle } from '../../core/api/stock-api';
import { ChartWidgetComponent, OhlcvBar, IndicatorRow } from '../chart-widget/chart.component';
import { ThesisResponseModel } from '../../core/models/thesis-response.model';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, ChartWidgetComponent],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss',
})
export class DashboardComponent {
  readonly timeframes = ['1mo', '3mo', '6mo', '1y', '2y', '5y'];
  readonly tabs: Array<'fundamentals' | 'news' | 'signals' | 'overview' | 'thesis' | 'watchlist'> = ['fundamentals', 'news', 'signals', 'overview', 'thesis', 'watchlist'];

  // ── State (signals — no need for cdr.detectChanges()) ─────────────────────
  loading     = signal(false);
  errorMsg    = signal('');
  ohlcvData   = signal<OhlcvBar[]>([]);
  indicators  = signal<IndicatorRow[]>([]);
  screener    = signal<any>(null);
  signals     = signal<Record<string, string>>({});
  news        = signal<NewsResponse | null>(null);
  thesis      = signal<ThesisResponseModel | null>(null);
  activeSymbol = signal('');

  activeTab    = signal<'fundamentals' | 'news' | 'signals' | 'overview' | 'thesis' | 'watchlist'>('fundamentals');

  watchlistData = signal<any[]>([]);
  watchlistLoading = signal(false);


  // ── Form ──────────────────────────────────────────────────────────────────
  form: FormGroup;
  response: boolean = false;

  constructor(private fb: FormBuilder, private stockApi: StockApi) {
    this.form = this.fb.group({
      symbol:    ['', [Validators.required, Validators.pattern(/^[A-Za-z.\-]{1,10}$/)]],
      timeframe: ['6mo', Validators.required],
    });
  }

  // ── Analyze ───────────────────────────────────────────────────────────────

  onAnalyze(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }

    const symbol    = (this.form.value.symbol ?? '').toUpperCase().trim();
    const timeframe = this.form.value.timeframe ?? '6mo';

    this.loading.set(true);
    this.errorMsg.set('');
    this.activeSymbol.set(symbol);
    this.activeTab.set('thesis');

    // Replace nested subscribes with forkJoin — all 3 fire in parallel
    forkJoin({
      ohlcv:      this.stockApi.getPriceHistory(symbol, timeframe),
      technical:  this.stockApi.getTechnical(symbol, timeframe),
      screener:   this.stockApi.getScreener(symbol),
      signals:    this.stockApi.getSignals(symbol, timeframe),
      news:       this.stockApi.getNews(symbol, 8),
      thesis:     this.stockApi.getThesis(symbol).pipe(catchError(() => of(null))),
    })
    .pipe(finalize(() => this.loading.set(false)))
    .subscribe({
      next: ({ ohlcv, technical, screener, signals, news,thesis }) => {
        console.log('OHLCV:', ohlcv);
  console.log('Technical:', technical);
  console.log('Screener:', screener);
  console.log('Signals:', signals);
  console.log('News:', news);
  console.log('Thesis:',thesis)
  // ✅ OHLCV — correct
  this.ohlcvData.set(ohlcv?.data ?? []);

  // ✅ Remap technical field names to match IndicatorRow interface
  const rawIndicators = Array.isArray(technical?.data) ? technical.data : [];
  const remapped = rawIndicators.map((row: any) => ({
    date:         row.date,
    sma_20:       row.sma_20       ?? null,
    sma_50:       row.sma_50       ?? null,
    ema_12:       row.ema_12       ?? null,
    ema_26:       row.ema_26       ?? null,
    rsi:          row.rsi_14       ?? null,   // ← rsi_14 → rsi
    macd:         row.macd_line    ?? null,   // ← macd_line → macd
    macd_signal:  row.macd_signal  ?? null,   // ← same name ✓
    macd_hist:    row.macd_histogram ?? null, // ← macd_histogram → macd_hist
    bb_upper:     row.bb_upper     ?? null,
    bb_lower:     row.bb_lower     ?? null,
    bb_middle:    row.bb_middle    ?? null,
    vwap:         row.vwap         ?? null,
  }));
  this.indicators.set(remapped);

  // ✅ Screener — dig into data.items[0]
  const item = screener?.data?.items?.[0] ?? null;
  this.screener.set(item ? { ...item, provider: screener.provider } : null);

  // ✅ Signals — already correct shape
  this.signals.set(signals?.signals ?? {});
  this.news.set(news);
  this.thesis.set(thesis)
  console.log('Thesis set in component:', this.thesis());
  this.response = true
},
      error: err => this.errorMsg.set(this.extractError(err)),
    });
  }

  setTab(tab: 'fundamentals' | 'news' | 'signals' | 'overview' | 'thesis'| 'watchlist'): void {
    this.activeTab.set(tab);
       if (tab === 'watchlist') {
      this.loadWatchlist();
    }
  }

  tabLabel(tab: 'fundamentals' | 'news' | 'signals' | 'overview' | 'thesis'|'watchlist'): string {
    if (tab === 'fundamentals') return 'Fundamental Analysis';
    if (tab === 'news') return 'News & Sentiment';
    if (tab === 'signals') return 'Signals';
    if (tab ==='thesis') return 'Investment Thesis';
    if (tab === 'watchlist') return 'Watchlist';
    return 'Overview';
  }

  onSymbolInput(): void {
    const ctrl = this.form.controls['symbol'];
    const upper = (ctrl.value ?? '').toUpperCase();
    if (ctrl.value !== upper) ctrl.setValue(upper, { emitEvent: false });
  }

  // ── Screener helpers ──────────────────────────────────────────────────────

// Replace these two computed properties:

screenerEntries = computed(() => {
  const sc = this.screener();
  if (!sc) return [];

  const skip = ['provider', 'status', 'symbol', 'name'];
  const rows: [string, any][] = [];

  // Top-level fields: name, sector, market_cap, price
  for (const [k, v] of Object.entries(sc)) {
    if (skip.includes(k) || k === 'metrics') continue;
    rows.push([k, v]);
  }

  // Flatten nested metrics object
  if (sc.metrics && typeof sc.metrics === 'object') {
    for (const [k, v] of Object.entries(sc.metrics)) {
      rows.push([k, v]);
    }
  }

  return rows;
});

signalEntries = computed(() => {
  const s = this.signals();
  console.log('Signals:', s);
  // Handle both array ["rsioversold"] and object { RSI: "OVERSOLD" } shapes
  if (Array.isArray(s)) {
    return (s as string[]).map(raw => {
      // Parse "rsioversold" → ["RSI", "OVERSOLD"]
      const match = raw.match(/^(rsi|macd|sma|bb|ema|vwap)/i);
      const key = match ? match[1].toUpperCase() : raw;
      const val = raw.replace(/^(rsi|macd|sma|bb|ema|vwap)/i, '') || 'SIGNAL';
      return [key, val.toUpperCase()] as [string, string];
    });
  }
  return Object.entries(s);
});

newsArticles = computed<NewsArticle[]>(() => {
  return this.news()?.articles ?? [];
});

newsGaugeSegments = computed(() => {
  const gauge = this.news()?.gauge;
  if (!gauge) {
    return [
      { label: 'positive', value: 0 },
      { label: 'neutral', value: 100 },
      { label: 'negative', value: 0 },
    ];
  }

  return [
    { label: 'positive', value: gauge.positive ?? 0 },
    { label: 'neutral', value: gauge.neutral ?? 0 },
    { label: 'negative', value: gauge.negative ?? 0 },
  ];
});

sentimentTone = computed(() => {
  const sentiment = this.news()?.overall_sentiment;
  return sentiment ?? 'neutral';
});

overallSentimentText = computed(() => {
  const sentiment = this.news()?.overall_sentiment ?? 'neutral';
  return sentiment.charAt(0).toUpperCase() + sentiment.slice(1);
});

overallSentimentScore = computed(() => {
  const score = this.news()?.overall_score;
  return typeof score === 'number' ? score.toFixed(2) : '0.00';
});

thesisSignalEntries = computed(() => {
  const ths = this.thesis();
  if (!ths?.signals) return [];

  const entries: [string, string][] = [];
  if (ths.signals.fundamental) entries.push(['Fundamental', ths.signals.fundamental]);
  if (ths.signals.technical) entries.push(['Technical', ths.signals.technical]);
  if (ths.signals.sentiment) entries.push(['Sentiment', ths.signals.sentiment]);
  if (ths.signals.valuation) entries.push(['Valuation', ths.signals.valuation]);

  return entries;
});

fundamentalRatioCards = computed(() => {
  const screener = this.screener();
  const metrics = screener?.metrics ?? {};

  return [
    {
      key: 'pe_ratio',
      label: 'P/E',
      value: this.getMetricValue(metrics, ['pe_ratio', 'pe']),
      suffix: '',
    },
    {
      key: 'roe',
      label: 'ROE',
      value: this.getMetricValue(metrics, ['roe']),
      suffix: '%',
    },
    {
      key: 'roce',
      label: 'ROCE',
      value: this.getMetricValue(metrics, ['roce']),
      suffix: '%',
    },
    {
      key: 'debt_to_equity',
      label: 'Debt / Equity',
      value: this.getMetricValue(metrics, ['debt_to_equity', 'de_ratio']),
      suffix: '',
    },
    {
      key: 'revenue_growth_yoy',
      label: 'Revenue Growth YoY',
      value: this.getMetricValue(metrics, ['revenue_growth_yoy', 'sales_growth_yoy']),
      suffix: '%',
    },
  ];
});

private getMetricValue(metrics: Record<string, unknown>, keys: string[]): number | null {
  for (const key of keys) {
    const raw = metrics[key];
    if (typeof raw === 'number' && Number.isFinite(raw)) {
      return raw;
    }
    if (typeof raw === 'string') {
      const parsed = Number(raw.replace(/,/g, '').trim());
      if (Number.isFinite(parsed)) {
        return parsed;
      }
    }
  }
  return null;
}

formatRatio(value: number | null, suffix = ''): string {
  if (value === null) {
    return 'N/A';
  }
  return `${value.toFixed(2)}${suffix}`;
}

formatDate(date: string | Date | null | undefined): string {
  if (!date) return 'N/A';
  try {
    const d = new Date(date);
    if (isNaN(d.getTime())) return 'N/A';
    return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
  } catch {
    return 'N/A';
  }
}



  loadWatchlist(): void {
    this.watchlistLoading.set(true);
    this.stockApi.compareWatchlist().pipe(
      finalize(() => this.watchlistLoading.set(false))
    ).subscribe({
      next: (data) => this.watchlistData.set(data),
      error: (err) => console.error('Failed to load watchlist', err)
    });
  }

  onAddToWatchlist(symbol: string): void {
    // const symbol = this.activeSymbol();
    if (!symbol) return;
    this.stockApi.addToWatchlist(symbol).subscribe({
      next: () => {
        alert(`${symbol} added to watchlist`);
        this.loadWatchlist();
      },
      error: (err) => alert(`Failed to add: ${this.extractError(err)}`)
    });
  }

  onRemoveFromWatchlist(symbol: string): void {
    this.stockApi.removeFromWatchlist(symbol).subscribe({
      next: () => this.loadWatchlist(),
      error: (err) => alert(`Failed to remove: ${this.extractError(err)}`)
    });
  }

  private extractError(err: any): string {
    return err?.error?.error?.message || err?.error?.message || err?.message || 'An unknown error occurred.';
  }
  isInWatchlist(symbol: string): boolean {
  return this.watchlistData().some(item => item.symbol === symbol);
}

onToggleWatchlist(symbol: string) {
  if (this.isInWatchlist(symbol)) {
    this.onRemoveFromWatchlist(symbol);
  } else {
    this.onAddToWatchlist(symbol);
  }
}
}