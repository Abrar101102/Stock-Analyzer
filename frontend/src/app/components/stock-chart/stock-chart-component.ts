import { Component, OnInit, ElementRef, ViewChild, Input } from '@angular/core';
import { createChart, IChartApi, ISeriesApi, CandlestickData } from 'lightweight-charts';

@Component({
  selector: 'app-stock-chart',
  template: `
    <div #chartContainer class="chart-container"></div>
    <div class="indicator-toggles">
      <label><input type="checkbox" [(ngModel)]="showSMA" (change)="toggleOverlay('sma')"> SMA 20/50/200</label>
      <label><input type="checkbox" [(ngModel)]="showBB" (change)="toggleOverlay('bb')"> Bollinger Bands</label>
      <label><input type="checkbox" [(ngModel)]="showVWAP" (change)="toggleOverlay('vwap')"> VWAP</label>
    </div>
    <div class="signals-panel" *ngIf="signals">
      <span [class]="'signal ' + signals.rsi">RSI: {{ signals.rsi }}</span>
      <span [class]="'signal ' + signals.macd">MACD: {{ signals.macd }}</span>
      <span [class]="'signal ' + signals.bollinger">BB: {{ signals.bollinger }}</span>
    </div>
  `,
  styleUrls: ['./stock-chart.component.scss']
})
export class StockChartComponent implements OnInit {
  @ViewChild('chartContainer', { static: true }) chartContainer!: ElementRef;
  @Input() symbol: string = '';

  chart!: IChartApi;
  candleSeries!: ISeriesApi<'Candlestick'>;
  signals: any = null;
  showSMA = false;
  showBB = false;
  showVWAP = false;

  ngOnInit() {
    this.chart = createChart(this.chartContainer.nativeElement, {
      width: 800,
      height: 500,
      layout: { background: { color: '#1a1a2e' }, textColor: '#e0e0e0' },
      grid: { vertLines: { color: '#2a2a3e' }, horzLines: { color: '#2a2a3e' } },
    });
    this.candleSeries = this.chart.addCandlestickSeries();
    this.loadData();
  }

  async loadData() {
    const res = await fetch(`/api/technical/${this.symbol}/indicators?period=1y`);
    const json = await res.json();

    const candles: CandlestickData[] = json.data.map((d: any) => ({
      time: d.date,
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
    }));

    this.candleSeries.setData(candles);
    this.signals = json.signals;
  }

  toggleOverlay(type: string) {
    // Add/remove line series for SMA, BB, VWAP overlays
  }
}