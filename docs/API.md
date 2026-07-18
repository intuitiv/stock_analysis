# API Documentation

## Overview

The NAETRA system provides both REST APIs and WebSocket interfaces for real-time data and interactions. All API endpoints are versioned and require authentication (except where noted).

## Authentication

```http
POST /api/v1/auth/token
```

Request:
```json
{
    "username": "your_username",
    "password": "your_password"
}
```

Response:
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "bearer",
    "expires_in": 3600
}
```

## REST API Endpoints

### Market Data

1. **Get Stock Data**
```http
GET /api/v1/market/stock/{symbol}
```

Parameters:
- `symbol` (string): Stock symbol
- `timeframe` (string, optional): Time period (1D, 1W, 1M, etc.)
- `indicators` (array, optional): Technical indicators to include

Response:
```json
{
    "symbol": "AAPL",
    "data": {
        "price": {
            "open": 150.23,
            "high": 152.45,
            "low": 149.89,
            "close": 151.34,
            "volume": 75234567
        },
        "indicators": {
            "ma_50": 148.56,
            "rsi_14": 65.4
        },
        "timestamp": "2025-06-07T12:00:00Z"
    }
}
```

2. **Compare Multiple Stocks**
```http
GET /api/v1/market/compare
```

Parameters:
- `symbols` (array): List of stock symbols
- `metrics` (array, optional): Metrics to compare

Response:
```json
{
    "comparison": [
        {
            "symbol": "AAPL",
            "metrics": {
                "price_change": 2.5,
                "volume_change": 15.3,
                "relative_strength": 1.2
            }
        },
        {
            "symbol": "MSFT",
            "metrics": {
                "price_change": 1.8,
                "volume_change": 10.5,
                "relative_strength": 0.95
            }
        }
    ],
    "timestamp": "2025-06-07T12:00:00Z"
}
```

### CHAETRA Interactions

1. **Query Knowledge**
```http
POST /api/v1/chaetra/query
```

Request:
```json
{
    "query": "What's your analysis of tech sector trends?",
    "context": {
        "timeframe": "6_months",
        "focus": "semiconductor_stocks"
    }
}
```

Response:
```json
{
    "analysis": {
        "summary": "Tech sector showing strong momentum...",
        "confidence": 0.85,
        "supporting_evidence": [
            {
                "type": "pattern",
                "description": "Consistent growth in revenue...",
                "confidence": 0.9
            }
        ],
        "recommendations": [
            {
                "action": "monitor_closely",
                "reason": "Potential breakout forming",
                "confidence": 0.75
            }
        ]
    }
}
```

2. **Get Opinion**
```http
GET /api/v1/chaetra/opinion/{topic}
```

Response:
```json
{
    "topic": "semiconductor_market",
    "opinion": {
        "summary": "Bullish outlook based on supply chain improvements...",
        "confidence": 0.82,
        "factors": [
            {
                "name": "supply_chain",
                "impact": "positive",
                "weight": 0.7
            }
        ],
        "timestamp": "2025-06-07T12:00:00Z"
    }
}
```

### Strategy Management

1. **Create Strategy**
```http
POST /api/v1/strategy
```

Request:
```json
{
    "name": "Tech Momentum",
    "description": "Momentum-based strategy for tech stocks",
    "rules": {
        "entry": [
            {
                "indicator": "RSI",
                "condition": "less_than",
                "value": 30
            }
        ],
        "exit": [
            {
                "indicator": "RSI",
                "condition": "greater_than",
                "value": 70
            }
        ]
    },
    "parameters": {
        "timeframe": "daily",
        "position_size": 0.1
    }
}
```

Response:
```json
{
    "strategy_id": "strat_123xyz",
    "status": "created",
    "validation": {
        "passed": true,
        "messages": []
    }
}
```

2. **Backtest Strategy**
```http
POST /api/v1/strategy/{strategy_id}/backtest
```

Request:
```json
{
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "initial_capital": 100000,
    "symbols": ["AAPL", "MSFT", "GOOGL"]
}
```

Response:
```json
{
    "backtest_id": "bt_456abc",
    "summary": {
        "total_return": 15.4,
        "sharpe_ratio": 1.8,
        "max_drawdown": -8.5,
        "win_rate": 0.65
    },
    "trades": [
        {
            "symbol": "AAPL",
            "entry": {
                "date": "2024-03-15",
                "price": 150.25
            },
            "exit": {
                "date": "2024-04-15",
                "price": 165.75
            },
            "return": 10.3
        }
    ]
}
```

## WebSocket APIs

### Market Data Stream

1. **Connect to Price Stream**
```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://api.naetra.com/ws/v1/market');

// Subscribe to symbols
ws.send(JSON.stringify({
    action: 'subscribe',
    symbols: ['AAPL', 'MSFT'],
    data_type: 'price'
}));

// Receive updates
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(data);
    // {
    //     "symbol": "AAPL",
    //     "price": 150.25,
    //     "timestamp": "2025-06-07T12:00:00.123Z"
    // }
};
```

2. **Pattern Recognition Stream**
```javascript
// Subscribe to pattern recognition
ws.send(JSON.stringify({
    action: 'subscribe',
    symbols: ['AAPL'],
    data_type: 'patterns'
}));

// Receive pattern updates
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(data);
    // {
    //     "symbol": "AAPL",
    //     "pattern": "double_bottom",
    //     "confidence": 0.85,
    //     "timestamp": "2025-06-07T12:00:00.123Z"
    // }
};
```

### Strategy Execution

1. **Strategy Monitor**
```javascript
// Connect to strategy WebSocket
const ws = new WebSocket('ws://api.naetra.com/ws/v1/strategy');

// Subscribe to strategy updates
ws.send(JSON.stringify({
    action: 'monitor',
    strategy_id: 'strat_123xyz'
}));

// Receive strategy signals
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(data);
    // {
    //     "strategy_id": "strat_123xyz",
    //     "signal": "entry",
    //     "symbol": "AAPL",
    //     "price": 150.25,
    //     "timestamp": "2025-06-07T12:00:00.123Z"
    // }
};
```

## Error Handling

All API endpoints use standard HTTP status codes and return error details in a consistent format:

```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid parameter value",
        "details": {
            "field": "timeframe",
            "reason": "Must be one of: 1D, 1W, 1M"
        }
    }
}
```

Common Error Codes:
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `429`: Too Many Requests
- `500`: Internal Server Error

## Rate Limiting

API endpoints are rate-limited based on the user's tier:

- Free Tier: 60 requests per minute
- Pro Tier: 300 requests per minute
- Enterprise Tier: Custom limits

Rate limit information is included in response headers:
```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1623067200
```

## Pagination

List endpoints support pagination using cursor-based pagination:

```http
GET /api/v1/market/history?symbol=AAPL&limit=100&cursor=eyJpZCI6MTIzfQ==
```

Response includes pagination metadata:
```json
{
    "data": [...],
    "pagination": {
        "next_cursor": "eyJpZCI6MTI0fQ==",
        "has_more": true
    }
}
```

## API Versioning

- API versions are included in the URL path: `/api/v1/`
- Multiple versions may be supported simultaneously
- Deprecation notices will be provided in response headers:
```http
X-API-Deprecation: Version v1 will be deprecated on 2026-01-01
X-API-Alternative: Please migrate to v2: /api/v2/
```

## WebSocket Connection Management

1. **Heartbeat**
```javascript
// Send heartbeat every 30 seconds
setInterval(() => {
    ws.send(JSON.stringify({
        action: 'ping',
        timestamp: Date.now()
    }));
}, 30000);

// Handle heartbeat response
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.action === 'pong') {
        // Connection is alive
    }
};
```

2. **Reconnection Strategy**
```javascript
function connect() {
    const ws = new WebSocket('ws://api.naetra.com/ws/v1/market');
    
    ws.onclose = (event) => {
        console.log('Connection closed. Reconnecting...');
        setTimeout(connect, 1000); // Reconnect after 1 second
    };
    
    return ws;
}
```

## Example Integration

```javascript
class NaetraClient {
    constructor(apiKey) {
        this.apiKey = apiKey;
        this.baseUrl = 'https://api.naetra.com/v1';
    }
    
    async getMarketData(symbol) {
        const response = await fetch(
            `${this.baseUrl}/market/stock/${symbol}`,
            {
                headers: {
                    'Authorization': `Bearer ${this.apiKey}`,
                    'Content-Type': 'application/json'
                }
            }
        );
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }
        
        return await response.json();
    }
    
    connectToStream(symbols) {
        const ws = new WebSocket('ws://api.naetra.com/ws/v1/market');
        
        ws.onopen = () => {
            ws.send(JSON.stringify({
                action: 'subscribe',
                symbols: symbols
            }));
        };
        
        return ws;
    }
}

// Usage
const client = new NaetraClient('your-api-key');

// REST API
const data = await client.getMarketData('AAPL');
console.log(data);

// WebSocket
const stream = client.connectToStream(['AAPL', 'MSFT']);
stream.onmessage = (event) => {
    const update = JSON.parse(event.data);
    console.log(update);
};
