import { Component, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { StockApi } from '../../core/api/stock-api';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss'
})
export class DashboardComponent {
  readonly timeframes = ['1mo', '3mo', '6mo', '1y', '2y', '5y'];

  loading = false;
  errorMessage = '';

  technicalResponse: any = null;
  screenerResponse: any = null;

  form: any;

  constructor(
    private fb: FormBuilder,
    private stockApi: StockApi,
    private cdr: ChangeDetectorRef // <-- 1. Injected ChangeDetectorRef
  ) {
    this.form = this.fb.group({
      symbol: ['', [Validators.required, Validators.pattern(/^[A-Za-z.\-]{1,10}$/)]],
      timeframe: ['6mo', Validators.required] 
    });
  }

  onAnalyze(): void {
    this.errorMessage = '';
    this.technicalResponse = null;
    this.screenerResponse = null;

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const symbol = (this.form.value.symbol ?? '').toUpperCase().trim();
    const timeframe = this.form.value.timeframe ?? '6mo';

    this.loading = true;

    this.stockApi.getTechnical(symbol, timeframe).subscribe({
      next: (technical) => {
        this.technicalResponse = technical;

        this.stockApi.getScreener(symbol).subscribe({
          next: (screener) => {
            this.screenerResponse = screener;
            this.loading = false;
            this.cdr.detectChanges(); // <-- 2. Force UI Update
          },
          error: (err) => {
            this.errorMessage = this.extractError(err) || 'Failed to fetch screener data.';
            this.loading = false;
            this.cdr.detectChanges(); // <-- Force UI Update
          }
        });
      },
      error: (err) => {
        this.loading = false;
        this.errorMessage = this.extractError(err) || 'Failed to fetch technical analysis.';
        this.cdr.detectChanges(); // <-- Force UI Update
      }
    });
  }

  onSymbolInput(): void {
    const control = this.form.controls.symbol;
    const current = control.value ?? '';
    const upper = current.toUpperCase();
    if (current !== upper) {
      control.setValue(upper, { emitEvent: false });
    }
  }

  private extractError(err: any): string {
    return err?.error?.error?.message || err?.error?.message || err?.message || '';
  }

  // 3. Fixed to read the FIRST row of your data array (the latest day)
  indicatorEntries(): [string, any][] {
    if (!this.technicalResponse || !this.technicalResponse.data) {
      return [];
    }

    // Your backend returns an array of 100 rows. We want the most recent one (index 0).
    const latestData = Array.isArray(this.technicalResponse.data) 
      ? this.technicalResponse.data[0] 
      : this.technicalResponse.data;

    if (!latestData) return [];

    // Filter out database fields so we ONLY show the actual indicators
    const ignoredKeys = ['id', 'symbol', 'date', 'computed_at'];
    
    return Object.entries(latestData).filter(([key]) => !ignoredKeys.includes(key));
  }
}