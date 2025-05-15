# Configuration Guide

## Market Data Provider Setup

### Current Setup (As of May 2025)
The application supports multiple market data providers with automatic fallback mechanisms. Here's how to configure them:

### Environment Variables
Add these settings to your `.env` file:

```env
# Market Data Providers
YAHOO_FINANCE_ENABLED=true
ALPHA_VANTAGE_ENABLED=true
ALPHA_VANTAGE_API_KEY=RKNUNUYE30H7KD68
MARKET_DATA_PROVIDER=yahoo_finance  # Primary provider

# Cache Settings
MARKET_DATA_CACHE_TTL_SECONDS=300
```

### Provider Configuration Details

1. **Yahoo Finance (Primary)**
   - Enabled by default
   - No API key required
   - Rate limited (built-in handling)
   - Used as primary data source

2. **Alpha Vantage (Fallback)**
   - API Key: `RKNUNUYE30H7KD68`
   - Rate Limits:
     - Standard API: 5 calls per minute
     - Built-in rate limit handling
   - Used as fallback when Yahoo Finance fails

### Automatic Fallback Mechanism
The system will:
1. Try Yahoo Finance first
2. If Yahoo Finance fails (429 rate limit or other errors), automatically try Alpha Vantage
3. Use cached data when available to minimize API calls

### Testing Configuration
You can test different providers by adding the `provider` query parameter to API calls:
```
GET /api/v1/market/overview?provider=alpha_vantage
GET /api/v1/market/overview?provider=yahoo_finance
```

### Troubleshooting
If experiencing rate limits:
1. Data is cached for 5 minutes by default
2. The system automatically retries with exponential backoff
3. Automatic provider fallback handles failures gracefully
