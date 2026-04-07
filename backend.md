# Backend Structure and File-by-File Use Cases

This document analyzes the backend folder and explains the use case of each file.

Scope notes:

- Included: all project backend files under `backend/`.
- Excluded: `backend/myenv/` and `__pycache__/` artifacts.

## 1) Root Backend Files

- backend/.env - Runtime environment variables (database URL, API keys, secret values).
- backend/finalized 7.1 blueprint.txt - Architecture/schema blueprint for financial snapshot design and evolution.
- backend/providers.md - Notes comparing external data providers and their free-tier capabilities.
- backend/requirements.txt - Python dependency manifest for backend runtime and tooling.
- backend/RoadMap.md - Product and engineering roadmap across phases.
- backend/skippedUnit.txt - Internal note placeholder for skipped/remaining unit tests.
- backend/test_screener.py - Smoke test script for screener provider scraping/parsing behavior.
- backend/trend_analysis_implementation.txt - Implementation notes for trend-analysis logic.

## 2) App Entry and Scheduling

- backend/app/main.py - FastAPI app bootstrap: middleware setup, exception wiring, and route registration.
- backend/app/scheduler.py - APScheduler setup for periodic ingestion jobs.

## 3) API Layer

- backend/app/api/**init**.py - Package marker for API module.
- backend/app/api/derived_metrics_route.py - Endpoints returning derived accounting/ratio metrics.
- backend/app/api/exception_handlers.py - Central HTTP mapping for domain exceptions.
- backend/app/api/fundamental_read_routes.py - Read endpoints for fundamental snapshots/statements from DB.
- backend/app/api/health.py - Health/status endpoint.
- backend/app/api/metrics.py - Endpoint exposing in-memory request/error/latency metrics.
- backend/app/api/news.py - News and sentiment endpoint for a symbol.
- backend/app/api/quarterly.py - Quarterly trend/summary endpoints.
- backend/app/api/screener.py - Screener overview endpoint (company profile + key metrics).
- backend/app/api/sector_compare.py - Sector peer comparison endpoints.
- backend/app/api/stock.py - Price history endpoint for symbols.
- backend/app/api/technical_analysis_route.py - Technical indicators and trading signal endpoints.
- backend/app/api/trend_route.py - Multi-year trend analysis endpoints.
- backend/app/api/valuation.py - Valuation metric endpoints (PE, EV-based metrics, etc.).

### Internal API

- backend/app/api/internal/fundamental_persistance.py - Internal ingestion/persistence triggers for fundamentals.

### Versioned API v1

- backend/app/api/v1/**init**.py - Package marker for v1 APIs.
- backend/app/api/v1/fundamentals.py - Stable/public v1 fundamentals API contract endpoints with auth/rate-limits.
- backend/app/api/v1/mappers.py - Translators from internal models to v1 response shapes.
- backend/app/api/v1/schemas.py - v1 schema definitions for response contract stability.

## 4) Core Infrastructure

- backend/app/core/api_keys.py - API key lookup/tier map used by auth dependency.
- backend/app/core/config.py - App configuration loading (DB URL, provider keys, environment reads).
- backend/app/core/errors.py - Structured error response models.
- backend/app/core/exceptions.py - Domain-specific exception classes.
- backend/app/core/logging.py - Logging initialization and formatter/handler setup.
- backend/app/core/logging_filter.py - Request-context filter (request id propagation into logs).
- backend/app/core/metrics.py - In-memory counters/aggregates for API metrics.
- backend/app/core/rate_limiter.py - Rate limiter implementation.
- backend/app/core/rate_limit_config.py - Per-endpoint rate-limit policies.
- backend/app/core/validators.py - Shared input validators (period/limit checks, etc.).

## 5) Data Providers and Data Source (Market Data)

- backend/app/data_providers/base_provider.py - Abstract interface for market price providers.
- backend/app/data_providers/yahoo_provider.py - Yahoo Finance implementation for OHLCV history.
- backend/app/data_providers/alpha_vantage_provider.py - Alpha Vantage implementation for OHLCV history.
- backend/app/data_sources/market_data_source.py - Source wrapper/helpers used to fetch market data.

## 6) Database Layer

- backend/app/db/base_class.py - SQLAlchemy declarative base.
- backend/app/db/session.py - SQLAlchemy engine/session factory configuration.
- backend/app/db/test_connection.py - Quick DB connectivity verification script.

## 7) Dependency Injection Layer

- backend/app/dependencies/auth_dependency.py - API key and tier enforcement dependencies.
- backend/app/dependencies/db_dependency.py - Request-scoped DB session dependency.
- backend/app/dependencies/fundamental_dependencies.py - Factory wiring for fundamental providers/services.
- backend/app/dependencies/fundamental_ingestion_dependency.py - Factory for ingestion orchestrator.
- backend/app/dependencies/fundamental_persistance_dependency.py - Factory for fundamentals persistence service.
- backend/app/dependencies/news_dependency.py - Factory for news service.
- backend/app/dependencies/quarterly_ingestion_dependency.py - Factory for quarterly ingestion service.
- backend/app/dependencies/quarterly_persistance_dependecy.py - Factory for quarterly persistence service.
- backend/app/dependencies/rate_limit_dependency.py - Dependency wrapper to apply configured limiter policies.
- backend/app/dependencies/stock_dependencies.py - Factory for stock service + market provider.
- backend/app/dependencies/technical_dependency.py - Factory for technical orchestrator and related services.

## 8) Fundamentals Domain

- backend/app/fundamentals/**init**.py - Package marker.

### Fundamentals Providers

- backend/app/fundamentals/data_providers/base_fundamental_provider.py - Abstract contract for fundamentals providers.
- backend/app/fundamentals/data_providers/alpha_vantage_provider.py - Alpha Vantage fundamentals fetch/transform.
- backend/app/fundamentals/data_providers/fallback_fundamental_provider.py - Fallback chain manager across providers.
- backend/app/fundamentals/data_providers/screener_provider.py - Screener.in scraper/parser for overview + statements.
- backend/app/fundamentals/data_providers/yahoo_fundamental_provider.py - Yahoo fundamentals fetch/transform.

### Fundamentals Mapper

- backend/app/fundamentals/mappers/fundamental_snapshot_mapper.py - Mapping between DB entities and domain snapshot model.

### Fundamentals Domain Models

- backend/app/fundamentals/models/balance_sheet_model.py - Balance sheet domain model.
- backend/app/fundamentals/models/cash_flow_model.py - Cash flow statement domain model.
- backend/app/fundamentals/models/financial_ratio_model.py - Derived financial ratio model.
- backend/app/fundamentals/models/fundamental_snapshot_model.py - Composite annual snapshot model.
- backend/app/fundamentals/models/income_statement_model.py - Income statement domain model.
- backend/app/fundamentals/models/quarterly_schema.py - Quarterly response schema model.
- backend/app/fundamentals/models/trend_model.py - Trend model used for multi-period analysis.

### Fundamentals Repositories

- backend/app/fundamentals/repositories/fundamental_read_repository.py - Read queries for annual snapshots.
- backend/app/fundamentals/repositories/fundamental_write_repository.py - Upsert/write logic for annual snapshots.
- backend/app/fundamentals/repositories/quarterly_read_repository.py - Read queries for quarterly snapshots.
- backend/app/fundamentals/repositories/quarterly_write_repository.py - Upsert/write logic for quarterly snapshots.

### Fundamentals Validation

- backend/app/fundamentals/validation/provider_sanity.py - Provider output sanity checks.

## 9) Jobs

- backend/app/jobs/fundamental_ingestiion_job.py - Scheduled job runner for fundamentals ingestion/backfill.

## 10) Market Data Service Abstraction

- backend/app/market_data/base_price_service.py - Price service interface used by valuation logic.
- backend/app/market_data/mock_price_service.py - Mock price service for testing/non-live execution.

## 11) Middleware

- backend/app/middleware/metrics.py - Middleware collecting per-request metrics.
- backend/app/middleware/request_context.py - Middleware attaching request IDs/context metadata.

## 12) ORM Models

- backend/app/models/**init**.py - Package marker for ORM models.
- backend/app/models/fundamental_snapshot.py - SQLAlchemy model for annual fundamental snapshots.
- backend/app/models/quarterly_snapshot_model.py - SQLAlchemy model for quarterly snapshots.
- backend/app/models/stock.py - Stock symbol metadata model.
- backend/app/models/technical_indicator.py - SQLAlchemy model for persisted technical indicators.

## 13) Registry

- backend/app/registry/stock_registry.py - Canonical list/metadata for supported symbols.
- backend/app/registry/symbol_resolver.py - Provider-specific symbol resolver/normalizer.

## 14) Services (Business Logic)

- backend/app/services/**init**.py - Package marker.
- backend/app/services/derived_metrics_service.py - Computes accounting/quality/ratio metrics.
- backend/app/services/fundamental_ingestion_service.py - Orchestrates ingestion from providers into storage.
- backend/app/services/fundamental_persistance.py - Persistence service for annual fundamental snapshots.
- backend/app/services/fundamental_read_service.py - Read service for annual snapshots/statements.
- backend/app/services/fundamental_service.py - Core fundamentals orchestration (provider + transformation).
- backend/app/services/news_service.py - News retrieval and sentiment scoring service.
- backend/app/services/quarterly_ingestion_service.py - Orchestrates quarterly ingestion and write flow.
- backend/app/services/quarterly_persistance.py - Persistence service for quarterly snapshots.
- backend/app/services/quarterly_trend_service.py - Computes TTM/QoQ/YoY quarterly trends.
- backend/app/services/sector_comparision.py - Sector-level peer comparisons and ranking logic.
- backend/app/services/stock_service.py - Stock price history service with symbol checks/resolution.
- backend/app/services/technical_analysis_service.py - Computes technical indicators from OHLCV.
- backend/app/services/technical_orchestrator_service.py - Coordinates technical fetch, compute, cache, persist pipeline.
- backend/app/services/technical_persistance.py - Persistence for technical indicator rows.
- backend/app/services/trend_service.py - Annual/multi-year trend calculations.
- backend/app/services/valuation_service.py - Valuation computations using price + fundamentals.

## 15) Utility Layer

- backend/app/utils/**init**.py - Package marker.
- backend/app/utils/json_sanitize.py - Recursively sanitizes JSON-unfriendly float values (NaN/Inf).
- backend/app/utils/sanitize.py - Cleans data structures for safe serialization/storage.

## 16) Valuation Models

- backend/app/valuation/models/valuation_model.py - Output model for valuation endpoint payload.

## High-Level Backend Structure (Use-Case Flow)

1. Client calls FastAPI route in `app/api/*`.
2. Route uses dependencies from `app/dependencies/*` (auth, DB, rate-limit, service factories).
3. Service in `app/services/*` executes business logic.
4. Service fetches data from provider (`app/data_providers/*` or `app/fundamentals/data_providers/*`) and/or repositories.
5. Repository persists/reads ORM models (`app/models/*`) using DB session (`app/db/*`).
6. Middleware and core modules (`app/middleware/*`, `app/core/*`) provide cross-cutting concerns (logging, metrics, throttling, exceptions).
7. Scheduler/jobs (`app/scheduler.py`, `app/jobs/*`) keep data fresh in background.

## Cleanup/Quality Notes

- Some filenames include spelling inconsistencies (`persistance`, `comparision`, `ingestiion`) that can be standardized.
- `backend/myenv/` should remain excluded from source control and architecture docs.
- Consider adding module-level docstrings in files without explicit comments to improve maintainability.
