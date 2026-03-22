

export interface ScreenerMetricMap {
  [key: string]: number | string | boolean | null;
}

export interface ScreenerItem {
  symbol: string;
  name?: string;
  sector?: string;
  industry?: string;
  price?: number;
  change_percent?: number;
  volume?: number;
  market_cap?: number;
  metrics?: ScreenerMetricMap;
}

export interface ApiError {
  code?: string;
  message: string;
}

export interface ScreenerData {
  items: ScreenerItem[];
  count?: number | null;
}

export interface ScreenerResponse {
  symbol?: string; // optional if endpoint returns list instead
  provider?: string;
  timestamp?: string;
  status: 'ok' | 'error';
  data?: ScreenerData;
  error?: ApiError;
}