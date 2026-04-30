Priority 1 — Complete the Thesis Core (High Impact, Low Effort)
Wire real signals into ThesisService (thesis_service.py, line 10 #TODO): Replace the four hardcoded stubs by calling TechnicalAnalysisService.get_signals() for the technical signal, NewsService.get_news_and_sentiment() for the sentiment signal, ValuationService.get_valuation() for the valuation signal (map P/E to cheap/fair/expensive), and FundamentalReadService for the fundamental signal (e.g., based on net margin and ROE). This single change makes the thesis feature genuinely data-driven.

Fix the typo "posetive" → "positive" in \_rule_based_verdict's score_map (thesis_service.py, line 48) and the hardcoded signals dict (line 12), which currently causes every "positive" fundamental signal to score 0 instead of +1.

Wire a real Gemini provider: thesis_dependency.py line 14 stubs Gemini with StubLLMProvider. Implement a GeminiProvider class that calls the Gemini REST API using settings.GEMINI_API_KEY, parallel to LlamaCppLoraProvider.

Enrich the LLM prompt: \_build_prompt sends only the four signal labels. Pass the actual metric values (e.g., P/E, RSI, revenue growth, sentiment score) so the LLM can generate a more specific, quantitative thesis paragraph.

Priority 2 — Stock Health Composite Score (High Impact, Medium Effort)
Composite Scoring Engine — new CompositeScoreService: Aggregate all four dimensions (fundamental, technical, sentiment, valuation) into a 0–100 score with configurable weights. Return it as composite_score alongside the ThesisResponseModel. This aligns directly with the existing RoadMap (RoadMap.md, Phase 4: "Composite Stock Health Score").

Score history and caching: Persist thesis verdicts and composite scores in a new thesis_cache DB table keyed by (symbol, date), so repeated calls within the same day return the cached result instantly, and historical verdict trends can be queried.

Priority 3 — Sector Comparison Expansion (Medium Impact, Medium Effort)
Expand SectorComparisionService (services/sector_comparision.py): Currently only compares P/E. Add comparisons for EV/EBITDA, P/B, ROE, and revenue growth so the Overview tab can show how a stock ranks against peers on multiple dimensions.

Sector-level thesis: Generate a thesis verdict relative to peers — e.g., "RELIANCE trades at a P/E 20% below sector median with above-average ROE, suggesting relative value."

Priority 4 — UX & Workflow Improvements (Medium Impact, Low Effort)
Thesis confidence indicator: Add a confidence field to ThesisResponseModel derived from how extreme the composite score is (e.g., score 80–100 = High, 50–80 = Medium, <50 = Low). Display a confidence pill in the UI next to the verdict badge.

Thesis tab auto-selection: After analysis, auto-switch to the Thesis tab (instead of always landing on Fundamentals), since it's the highest-level summary. This is a one-line change in dashboard.ts line 55 (this.activeTab.set('thesis')).

Watchlist / symbol comparison: Allow users to add symbols to a watchlist and compare thesis verdicts side-by-side, leveraging the already-built StockRegistry and SectorComparisionService.

Priority 5 — Data Quality & Infrastructure (Lower Immediate Impact, High Long-term Value)
Anomaly detection using scikit-learn (already in requirements.txt): Flag unusual volume spikes or price deviations from historical patterns and surface them as an additional signal in the thesis.

Redis caching layer: Add caching for screener data (scraped from screener.in), news, and technical indicators to avoid redundant API/scrape calls and reduce latency. The RoadMap (RoadMap.md, Phase 6) explicitly lists this.

Macro-economic signal: Pull interest rates and CPI/inflation from the free FRED API and incorporate them as a fifth signal dimension in the thesis (especially relevant for valuation judgments like "expensive given rising rates").

FinBERT news sentiment (replace the lexicon-based scorer): The current NewsService.\_score_sentiment() uses a 36-word lexicon. Replace or augment it with FinBERT (HuggingFace ProsusAI/finbert) for financial-domain NLP accuracy, as the RoadMap recommends (RoadMap.md, Phase 3).
