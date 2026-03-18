export interface TechnicalIndicatorMap { [key: string]: number | string | boolean | null; }

export interface TechnicalSignal { name: string; value: string; // e.g., "bullish" | "bearish" | "neutral" 
score?: number; // optional normalized score 
reason?: string; 
}

export interface TechnicalData { trend?: 'bullish' | 'bearish' | 'neutral'; summary_score?: number; indicators?: TechnicalIndicatorMap; signals?: TechnicalSignal[]; }

export interface ApiError { code?: string; message: string; }

export interface TechnicalResponse { symbol: string; provider?: string; timeframe?: string; timestamp?: string; status: 'ok' | 'error'; data?: TechnicalData; error?: ApiError; }