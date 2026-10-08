# Alpaca Live Trading Setup

Status (2026-10-08): **not connected yet.** User chose the **live** (real money) account.

## Blockers
1. Cloud environment network policy blocks Alpaca hosts (HTTP 403 on CONNECT).
2. No Alpaca API keys are set in the environment.

## Steps for the user (environment settings, then start a new session)
1. Session title bar > cloud environment menu > **Edit**.
2. **Network access** > Allowed domains (keep "Allow package managers" ticked):
   - `api.alpaca.markets` (live trading)
   - `data.alpaca.markets` (market data)
   - `paper-api.alpaca.markets` (optional, for testing with fake money)
3. Add environment variables (or Network secrets, if offered):
   - `APCA_API_KEY_ID`
   - `APCA_API_SECRET_KEY`
   - `APCA_API_BASE_URL=https://api.alpaca.markets`
4. Never paste keys into chat.

## Safety rules agreed for live trading
- Claude shows full order details and waits for explicit "yes" before every order.
- Alpaca keys cannot be read-only; live keys can place real trades.
- Pattern Day Trader rule: margin accounts under $25,000 are limited to 3 day trades in 5 business days.

## Verify connection (once set up)
```bash
curl -sS -H "APCA-API-KEY-ID: $APCA_API_KEY_ID" \
     -H "APCA-API-SECRET-KEY: $APCA_API_SECRET_KEY" \
     https://api.alpaca.markets/v2/account
```

## References
- Network access: https://code.claude.com/docs/en/cloud-environments#network-access
- Alpaca authentication: https://docs.alpaca.markets/docs/authentication
- Alpaca account endpoint: https://docs.alpaca.markets/reference/getaccount-1
- Alpaca PDT rule: https://docs.alpaca.markets/docs/user-protection
- Alpaca official MCP server: https://github.com/alpacahq/alpaca-mcp-server
