# Chat UI Mockup

## Processing Message Example

```
┌────────────────────────────────────────────────────┐
│                                                    │
│  🤖 CHAETRA                                        │
│                                                    │
│  Can I buy apple?                                  │
│                                                    │
│  [Current Processing: Fetching data for AAPL...] ◷ │
│                                                    │
│  Updates:                                          │
│  [processing: Understanding query intent...]        │
│  [intent: stock_price]                             │
│                                                    │
└────────────────────────────────────────────────────┘
```

## Error Message Example

```
┌────────────────────────────────────────────────────┐
│                                                    │
│  🤖 CHAETRA                                        │
│                                                    │
│  Can I buy apple?                                  │
│                                                    │
│  [Current Processing: An unexpected error occurred] ⓧ│
│                                                    │
│  Updates:                                          │
│  [processing: Understanding query intent...]        │
│  [intent: stock_price]                             │
│  [processing: Fetching data for AAPL...]        │
│  [error: object async_generator can't be used...]   │
│                                                    │
└────────────────────────────────────────────────────┘
```

Key:
- ◷ = Loading indicator
- ⓧ = Error indicator

This mockup shows:
1. Current processing status with a loading indicator
2. Previous updates displayed as chips below
3. Error messages are clearly marked

Would you like me to proceed with implementing these changes?