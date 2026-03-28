import { Component, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators, FormGroup } from '@angular/forms';
import { forkJoin, finalize } from 'rxjs';
import { StockApi } from '../../core/api/stock-api';
import { ChartWidgetComponent, OhlcvBar, IndicatorRow } from '../chart-widget/chart.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, ChartWidgetComponent],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss',
})
export class DashboardComponent {
  readonly timeframes = ['1mo', '3mo', '6mo', '1y', '2y', '5y'];

  // ── State (signals — no need for cdr.detectChanges()) ─────────────────────
  loading     = signal(false);
  errorMsg    = signal('');
  ohlcvData   = signal<OhlcvBar[]>([]);
  indicators  = signal<IndicatorRow[]>([]);
  screener    = signal<any>(null);
  signals     = signal<Record<string, string>>({});
  activeSymbol = signal('');

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

    // Replace nested subscribes with forkJoin — all 3 fire in parallel
    forkJoin({
      ohlcv:      this.stockApi.getPriceHistory(symbol, timeframe),
      technical:  this.stockApi.getTechnical(symbol, timeframe),
      screener:   this.stockApi.getScreener(symbol),
      signals:    this.stockApi.getSignals(symbol, timeframe),
    })
    .pipe(finalize(() => this.loading.set(false)))
    .subscribe({
      next: ({ ohlcv, technical, screener, signals }) => {
        console.log('OHLCV:', ohlcv);
  console.log('Technical:', technical);
  console.log('Screener:', screener);
  console.log('Signals:', signals);

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
  this.response = true
},
      error: err => this.errorMsg.set(this.extractError(err)),
    });
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

  private extractError(err: any): string {
    return err?.error?.error?.message || err?.error?.message || err?.message || 'An unknown error occurred.';
  }
}