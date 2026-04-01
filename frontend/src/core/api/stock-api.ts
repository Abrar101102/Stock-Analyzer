// ── ADD these methods to your existing StockApi service ──────────────────────
// File: src/app/core/api/stock-api.ts

import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
const BASE = environment.apiBaseUrl;

export interface NewsArticle {
  title: string;
  source: string;
  url: string;
  published_at: string;
  description: string;
  sentiment_label: 'positive' | 'neutral' | 'negative';
  sentiment_score: number;
}

export interface NewsResponse {
  symbol: string;
  query: string;
  total_results: number;
  overall_sentiment: 'positive' | 'neutral' | 'negative';
  overall_score: number;
  gauge: {
    positive: number;
    neutral: number;
    negative: number;
  };
  articles: NewsArticle[];
}

@Injectable({ providedIn: 'root' })
export class StockApi {
  constructor(private http: HttpClient) {}

  // ── Already exists in your codebase ───────────────────────────────────────

  getTechnical(symbol: string, period = '6mo'): Observable<any> {
    return this.http.get(`${BASE}/technical/${symbol}/indicators`, {
      params: new HttpParams().set('period', period),
    });
  }

  getScreener(symbol: string): Observable<any> {
    // Your screener endpoint takes symbol as a query param, adjust if needed
    return this.http.get(`${BASE}/screener`, {
      params: new HttpParams().set('symbol', symbol),
    });
  }

  // ── NEW — add these ────────────────────────────────────────────────────────

  /**
   * Maps to:  GET /api/stock/{symbol}/price-history/?period=6mo
   * Returns:  { data: OhlcvBar[] }
   */
  getPriceHistory(symbol: string, period = '6mo'): Observable<any> {
    return this.http.get(`${BASE}/stock/${symbol}/price-history/`, {
      params: new HttpParams().set('period', period),
    });
  }

  /**
   * Maps to:  GET /api/technical/{symbol}/signals?period=6mo
   * Returns:  { signals: Record<string, string> }
   *
   * Expected signal shape from your TechnicalAnalysisService.get_signals():
   * {
   *   "RSI":  "OVERBOUGHT" | "OVERSOLD" | "NEUTRAL",
   *   "MACD": "BULLISH"    | "BEARISH"  | "NEUTRAL",
   *   "SMA":  "GOLDEN_CROSS" | "DEATH_CROSS" | "NEUTRAL"
   * }
   */
  getSignals(symbol: string, period = '6mo'): Observable<any> {
    return this.http.get(`${BASE}/technical/${symbol}/signals`, {
      params: new HttpParams().set('period', period),
    });
  }

  getNews(symbol: string, limit = 8): Observable<NewsResponse> {
    return this.http.get<NewsResponse>(`${BASE}/news/${symbol}`, {
      params: new HttpParams().set('limit', String(limit)),
    });
  }
}