# Frontend Structure and File-by-File Analysis

Scope notes:
- Included: all files under frontend/.
- Excluded: node_modules/, .angular/, dist/.

## File Analysis

- frontend/.editorconfig — Enforces consistent code formatting conventions across editors.
- frontend/.gitignore — Excludes build artifacts, dependency folders, and local IDE files from git.
- frontend/angular.json — Angular CLI workspace configuration for build/serve/test targets and assets.
- frontend/package-lock.json — Exact dependency lockfile for reproducible installs.
- frontend/package.json — Frontend package manifest with scripts, Angular deps, SSR deps, and chart/UI libs.
- frontend/README.md — Project usage notes (serve/build/test defaults from Angular scaffold).
- frontend/tsconfig.app.json — TypeScript config for application source compilation.
- frontend/tsconfig.json — Base TypeScript config and strict compiler options.
- frontend/tsconfig.spec.json — TypeScript config for unit tests/spec files.

### VS Code Local Config
- frontend/.vscode/extensions.json — Recommended VS Code extensions.
- frontend/.vscode/launch.json — Debug launch profiles (browser/tests).
- frontend/.vscode/tasks.json — Task definitions for common npm workflows.

### Public Assets
- frontend/public/favicon.ico — Browser tab icon.

### App Bootstrap and SSR
- frontend/src/index.html — Root HTML shell where Angular app mounts.
- frontend/src/main.ts — Browser bootstrap entrypoint.
- frontend/src/main.server.ts — Server-side bootstrap entrypoint for SSR.
- frontend/src/server.ts — Express SSR server and static file serving.
- frontend/src/styles.scss — Global stylesheet (currently minimal).

### Root App Module/Config (Standalone Angular)
- frontend/src/app/app.config.server.ts — Server-specific app provider config.
- frontend/src/app/app.config.ts — Root providers setup (router/http/hydration).
- frontend/src/app/app.html — Root template hosting router outlet.
- frontend/src/app/app.routes.server.ts — Server-side/prerender route config.
- frontend/src/app/app.routes.ts — Client route table.
- frontend/src/app/app.scss — Root component styles.
- frontend/src/app/app.spec.ts — Unit tests for root app component.
- frontend/src/app/app.ts — Root standalone component class.

### Core Layer
- frontend/src/core/api/stock-api.spec.ts — Unit test scaffold for API service.
- frontend/src/core/api/stock-api.ts — Central HTTP client for stock/fundamental/technical/news endpoints.
- frontend/src/core/models/screener-response.ts — Typed interfaces for screener responses.
- frontend/src/core/models/technical-response.ts — Typed interfaces for technical response payloads.

### Environments
- frontend/src/environments/environment.prod.ts — Production environment config (API base URL).
- frontend/src/environments/environment.ts — Development environment config (local API URL).

### Feature: Chart Widget
- frontend/src/features/chart-widget/chart.component.html — Chart widget template (controls + render container).
- frontend/src/features/chart-widget/chart.component.scss — Chart widget visual styling.
- frontend/src/features/chart-widget/chart.component.ts — Lightweight-charts integration and indicator rendering logic.

### Feature: Dashboard
- frontend/src/features/dashboard/dashboard.html — Main dashboard UI (search, tabs, cards, sections).
- frontend/src/features/dashboard/dashboard.scss — Dashboard layout and responsive styles.
- frontend/src/features/dashboard/dashboard.spec.ts — Dashboard component test scaffold.
- frontend/src/features/dashboard/dashboard.ts — Dashboard orchestration: form handling, API fan-out, computed display state.

## Frontend Architecture Summary

- Angular standalone-component architecture with SSR support.
- Single core API service layer used by feature components.
- Feature-centric folder design (dashboard, chart-widget).
- Signal-based local state and computed UI values in dashboard.
- Reactive forms for stock input/timeframe controls.
- Environment-based API base URL switching.
- Component-scoped SCSS with mostly minimal global styles.
- Lightweight Charts used for market/indicator visualizations.

## Potential Cleanup and Risks

- Production API URL placeholder needs a real deployed backend URL.
- Very light test coverage (mostly scaffolds) for critical UI/data flows.
- Endpoint paths are hardcoded in API service; backend path changes can break UI quickly.
- Inconsistent timeframe labeling risk (UI labels vs backend accepted period strings).
- SSR/hydration edge cases may appear without integration tests.
- Limited shared design tokens/global style system may cause styling drift over time.
- Error/loading handling can be expanded for partial-failure scenarios (when one API fails in parallel calls).
- Dependency set should be reviewed periodically for unused libs.
