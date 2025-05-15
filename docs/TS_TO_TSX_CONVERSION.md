# TypeScript to TSX Conversion Plan

## Overview
This document outlines the plan for converting TypeScript (.ts) files to TypeScript with JSX (.tsx) files for consistency across the project.

## Files to Convert

### 1. Types
- `frontend/src/types/portfolio.ts` → `portfolio.tsx`

### 2. Utils
- `frontend/src/utils/api.ts` → `api.tsx`
- `frontend/src/utils/formatters.ts` → `formatters.tsx`

### 3. Store
- `frontend/src/store/analysis.ts` → `analysis.tsx`
- `frontend/src/store/market.ts` → `market.tsx`
- `frontend/src/store/settings.ts` → `settings.tsx`

### 4. Hooks
- `frontend/src/hooks/useMarketData.ts` → `useMarketData.tsx`
- `frontend/src/hooks/usePortfolioData.ts` → `usePortfolioData.tsx`

## Implementation Process

### Configuration Verification ✅
- Verified tsconfig.json configuration
- Confirmed proper JSX support with "jsx": "react-jsx"
- Confirmed proper module and target settings
- No configuration changes needed

### Conversion Steps
1. Convert files in this specific order:
   - Types (portfolio.ts)
   - Utils (api.ts, formatters.ts)
   - Store files (analysis.ts, market.ts, settings.ts)
   - Hooks (useMarketData.ts, usePortfolioData.ts)

2. For each file:
   - Create backup of current version
   - Rename from .ts to .tsx
   - Update any necessary imports in other files
   - Verify functionality

### Testing Strategy
After each group of conversions:
1. Run TypeScript compiler to check for errors
2. Verify all imports are working
3. Test affected functionality
4. Run the application to ensure no regressions

### Quality Checks
- [ ] All imports updated and working
- [ ] TypeScript compilation passes
- [ ] Application runs without errors
- [ ] All functionality preserved
- [ ] No performance impact

## Rollback Plan
If issues are encountered:
1. Restore from backup
2. Document the specific issue
3. Address any configuration or code problems
4. Retry conversion with fixes in place