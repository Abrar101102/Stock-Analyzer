import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { TechnicalResponse } from '../models/technical-response';
import { ScreenerResponse } from '../models/screener-response';

@Injectable({
  providedIn: 'root',
})
export class StockApi {
  private readonly baseUrl = environment.apiBaseUrl;

  constructor(private http: HttpClient) {}

  // Backend route: GET /technical/{symbol}/indicators?period=1y&force_refresh=false
  getTechnical(symbol: string, period: string): Observable<TechnicalResponse> {
    const cleanSymbol = symbol.toUpperCase().trim();
    const params = new HttpParams().set('period', period);
    return this.http.get<TechnicalResponse>(
      `${this.baseUrl}/technical/${cleanSymbol}/indicators`,
      { params }
    );
  }

  // Optional: if you want quick signal-only route
  getTechnicalSignals(symbol: string, period: string): Observable<any> {
    const cleanSymbol = symbol.toUpperCase().trim();
    const params = new HttpParams().set('period', period);
    return this.http.get<any>(
      `${this.baseUrl}/technical/${cleanSymbol}/signals`,
      { params }
    );
  }

  // TODO: replace path once your actual screener route is confirmed
  getScreener(symbol: string): Observable<ScreenerResponse> {
    const cleanSymbol = symbol.toUpperCase().trim();
    const params = new HttpParams().set('symbol', cleanSymbol);
    return this.http.get<ScreenerResponse>(`${this.baseUrl}/screener`, { params });
  }
}