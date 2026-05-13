---
id: spot
name: Spot
description: Use this skill when making Binance Spot API requests, signing authenticated calls, choosing testnet versus mainnet endpoints, handling API keys and secrets, or working with Spot market data and orders.
category: Blockchain
author: Binance
version: 1.0.1
---

# Binance Spot Skill

Spot request on Binance using authenticated API endpoints. Requires API key and secret key for certain endpoints. Return the result in JSON format.

## Quick Reference

| Endpoint | Description | Required | Optional | Authentication |
|----------|-------------|----------|----------|----------------|
| `/api/v3/exchangeInfo` (GET) | Exchange information | None | symbol, symbols, permissions, showPermissionSets, symbolStatus | No |
| `/api/v3/ping` (GET) | Test connectivity | None | None | No |
| `/api/v3/time` (GET) | Check server time | None | None | No |
| `/api/v3/aggTrades` (GET) | Compressed/Aggregate trades list | symbol | fromId, startTime, endTime, limit | No |
| `/api/v3/avgPrice` (GET) | Current average price | symbol | None | No |
| `/api/v3/depth` (GET) | Order book | symbol | limit, symbolStatus | No |
| `/api/v3/historicalTrades` (GET) | Old trade lookup | symbol | limit, fromId | No |
| `/api/v3/klines` (GET) | Kline/Candlestick data | symbol, interval | startTime, endTime, timeZone, limit | No |
| `/api/v3/ticker` (GET) | Rolling window price change statistics | None | symbol, symbols, windowSize, type, symbolStatus | No |
| `/api/v3/ticker/24hr` (GET) | 24hr ticker price change statistics | None | symbol, symbols, type, symbolStatus | No |
| `/api/v3/ticker/bookTicker` (GET) | Symbol order book ticker | None | symbol, symbols, symbolStatus | No |
| `/api/v3/ticker/price` (GET) | Symbol price ticker | None | symbol, symbols, symbolStatus | No |
| `/api/v3/ticker/tradingDay` (GET) | Trading Day Ticker | None | symbol, symbols, timeZone, type, symbolStatus | No |
| `/api/v3/trades` (GET) | Recent trades list | symbol | limit | No |
| `/api/v3/uiKlines` (GET) | UIKlines | symbol, interval | startTime, endTime, timeZone, limit | No |
| `/api/v3/openOrders` (DELETE) | Cancel All Open Orders on a Symbol | symbol | recvWindow | Yes |
| `/api/v3/openOrders` (GET) | Current open orders | None | symbol, recvWindow | Yes |
| `/api/v3/order` (POST) | New order | symbol, side, type | timeInForce, quantity, quoteOrderQty, price, newClientOrderId, strategyId, strategyType, stopPrice, trailingDelta, icebergQty, newOrderRespType, selfTradePreventionMode, pegPriceType, pegOffsetValue, pegOffsetType, recvWindow | Yes |
| `/api/v3/order` (DELETE) | Cancel order | symbol | orderId, origClientOrderId, newClientOrderId, cancelRestrictions, recvWindow | Yes |
| `/api/v3/order` (GET) | Query order | symbol | orderId, origClientOrderId, recvWindow | Yes |
| `/api/v3/order/amend/keepPriority` (PUT) | Order Amend Keep Priority | symbol, newQty | orderId, origClientOrderId, newClientOrderId, recvWindow | Yes |
| `/api/v3/order/cancelReplace` (POST) | Cancel an Existing Order and Send a New Order | symbol, side, type, cancelReplaceMode | timeInForce, quantity, quoteOrderQty, price, cancelNewClientOrderId, cancelOrigClientOrderId, cancelOrderId, newClientOrderId, strategyId, strategyType, stopPrice, trailingDelta, icebergQty, newOrderRespType, selfTradePreventionMode, cancelRestrictions, orderRateLimitExceededMode, pegPriceType, pegOffsetValue, pegOffsetType, recvWindow | Yes |
| `/api/v3/order/oco` (POST) | New OCO - Deprecated | symbol, side, quantity, price, stopPrice | listClientOrderId, limitClientOrderId, limitStrategyId, limitStrategyType, limitIcebergQty, trailingDelta, stopClientOrderId, stopStrategyId, stopStrategyType, stopLimitPrice, stopIcebergQty, stopLimitTimeInForce, newOrderRespType, selfTradePreventionMode, recvWindow | Yes |
| `/api/v3/order/test` (POST) | Test new order | symbol, side, type | computeCommissionRates, timeInForce, quantity, quoteOrderQty, price, newClientOrderId, strategyId, strategyType, stopPrice, trailingDelta, icebergQty, newOrderRespType, selfTradePreventionMode, pegPriceType, pegOffsetValue, pegOffsetType, recvWindow | Yes |
| `/api/v3/orderList` (DELETE) | Cancel Order list | symbol | orderListId, listClientOrderId, newClientOrderId, recvWindow | Yes |
| `/api/v3/orderList` (GET) | Query Order list | None | orderListId, origClientOrderId, recvWindow | Yes |
| `/api/v3/orderList/oco` (POST) | New Order list - OCO | symbol, side, quantity, aboveType, belowType | listClientOrderId, aboveClientOrderId, aboveIcebergQty, abovePrice, aboveStopPrice, aboveTrailingDelta, aboveTimeInForce, aboveStrategyId, aboveStrategyType, abovePegPriceType, abovePegOffsetType, abovePegOffsetValue, belowClientOrderId, belowIcebergQty, belowPrice, belowStopPrice, belowTrailingDelta, belowTimeInForce, belowStrategyId, belowStrategyType, belowPegPriceType, belowPegOffsetType, belowPegOffsetValue, newOrderRespType, selfTradePreventionMode, recvWindow | Yes |
| `/api/v3/orderList/opo` (POST) | New Order List - OPO | symbol, workingType, workingSide, workingPrice, workingQuantity, pendingType, pendingSide | listClientOrderId, newOrderRespType, selfTradePreventionMode, workingClientOrderId, workingIcebergQty, workingTimeInForce, workingStrategyId, workingStrategyType, workingPegPriceType, workingPegOffsetType, workingPegOffsetValue, pendingClientOrderId, pendingPrice, pendingStopPrice, pendingTrailingDelta, pendingIcebergQty, pendingTimeInForce, pendingStrategyId, pendingStrategyType, pendingPegPriceType, pendingPegOffsetType, pendingPegOffsetValue, recvWindow | Yes |
| `/api/v3/orderList/opoco` (POST) | New Order List - OPOCO | symbol, workingType, workingSide, workingPrice, workingQuantity, pendingSide, pendingAboveType | listClientOrderId, newOrderRespType, selfTradePreventionMode, workingClientOrderId, workingIcebergQty, workingTimeInForce, workingStrategyId, workingStrategyType, workingPegPriceType, workingPegOffsetType, workingPegOffsetValue, pendingAboveClientOrderId, pendingAbovePrice, pendingAboveStopPrice, pendingAboveTrailingDelta, pendingAboveIcebergQty, pendingAboveTimeInForce, pendingAboveStrategyId, pendingAboveStrategyType, pendingAbovePegPriceType, pendingAbovePegOffsetType, pendingAbovePegOffsetValue, pendingBelowType, pendingBelowClientOrderId, pendingBelowPrice, pendingBelowStopPrice, pendingBelowTrailingDelta, pendingBelowIcebergQty, pendingBelowTimeInForce, pendingBelowStrategyId, pendingBelowStrategyType, pendingBelowPegPriceType, pendingBelowPegOffsetType, pendingBelowPegOffsetValue, recvWindow | Yes |
| `/api/v3/orderList/oto` (POST) | New Order list - OTO | symbol, workingType, workingSide, workingPrice, workingQuantity, pendingType, pendingSide, pendingQuantity | listClientOrderId, newOrderRespType, selfTradePreventionMode, workingClientOrderId, workingIcebergQty, workingTimeInForce, workingStrategyId, workingStrategyType, workingPegPriceType, workingPegOffsetType, workingPegOffsetValue, pendingClientOrderId, pendingPrice, pendingStopPrice, pendingTrailingDelta, pendingIcebergQty, pendingTimeInForce, pendingStrategyId, pendingStrategyType, pendingPegPriceType, pendingPegOffsetType, pendingPegOffsetValue, recvWindow | Yes |
| `/api/v3/orderList/otoco` (POST) | New Order list - OTOCO | symbol, workingType, workingSide, workingPrice, workingQuantity, pendingSide, pendingQuantity, pendingAboveType | listClientOrderId, newOrderRespType, selfTradePreventionMode, workingClientOrderId, workingIcebergQty, workingTimeInForce, workingStrategyId, workingStrategyType, workingPegPriceType, workingPegOffsetType, workingPegOffsetValue, pendingAboveClientOrderId, pendingAbovePrice, pendingAboveStopPrice, pendingAboveTrailingDelta, pendingAboveIcebergQty, pendingAboveTimeInForce, pendingAboveStrategyId, pendingAboveStrategyType, pendingAbovePegPriceType, pendingAbovePegOffsetType, pendingAbovePegOffsetValue, pendingBelowType, pendingBelowClientOrderId, pendingBelowPrice, pendingBelowStopPrice, pendingBelowTrailingDelta, pendingBelowIcebergQty, pendingBelowTimeInForce, pendingBelowStrategyId, pendingBelowStrategyType, pendingBelowPegPriceType, pendingBelowPegOffsetType, pendingBelowPegOffsetValue, recvWindow | Yes |
| `/api/v3/sor/order` (POST) | New order using SOR | symbol, side, type, quantity | timeInForce, price, newClientOrderId, strategyId, strategyType, icebergQty, newOrderRespType, selfTradePreventionMode, recvWindow | Yes |
| `/api/v3/sor/order/test` (POST) | Test new order using SOR | symbol, side, type, quantity | computeCommissionRates, timeInForce, price, newClientOrderId, strategyId, strategyType, icebergQty, newOrderRespType, selfTradePreventionMode, recvWindow | Yes |
| `/api/v3/account` (GET) | Account information | None | omitZeroBalances, recvWindow | Yes |
| `/api/v3/account/commission` (GET) | Query Commission Rates | symbol | None | Yes |
| `/api/v3/allOrderList` (GET) | Query all Order lists | None | fromId, startTime, endTime, limit, recvWindow | Yes |
| `/api/v3/allOrders` (GET) | All orders | symbol | orderId, startTime, endTime, limit, recvWindow | Yes |
| `/api/v3/myAllocations` (GET) | Query Allocations | symbol | startTime, endTime, fromAllocationId, limit, orderId, recvWindow | Yes |
| `/api/v3/myFilters` (GET) | Query relevant filters | symbol | recvWindow | Yes |
| `/api/v3/myPreventedMatches` (GET) | Query Prevented Matches | symbol | preventedMatchId, orderId, fromPreventedMatchId, limit, recvWindow | Yes |
| `/api/v3/myTrades` (GET) | Account trade list | symbol | orderId, startTime, endTime, fromId, limit, recvWindow | Yes |
| `/api/v3/openOrderList` (GET) | Query Open Order lists | None | recvWindow | Yes |
| `/api/v3/order/amendments` (GET) | Query Order Amendments | symbol, orderId | fromExecutionId, limit, recvWindow | Yes |
| `/api/v3/rateLimit/order` (GET) | Query Unfilled Order Count | None | recvWindow | Yes |

---

## Parameters

### Common Parameters

* **symbol**: Symbol to query (e.g., BNBUSDT)
* **symbols**: List of symbols to query
* **permissions**: List of permissions to query
* **showPermissionSets**: Controls whether the content of the `permissionSets` field is populated or not. Defaults to `true` (e.g., true)
* **symbol**:  (e.g., BNBUSDT)
* **fromId**: ID to get aggregate trades from INCLUSIVE. (e.g., 1)
* **startTime**: Timestamp in ms to get aggregate trades from INCLUSIVE. (e.g., 1735693200000)
* **endTime**: Timestamp in ms to get aggregate trades until INCLUSIVE. (e.g., 1735693200000)
* **limit**: Default: 500; Maximum: 1000. (e.g., 500)
* **timeZone**: Default: 0 (UTC)
* **recvWindow**: The value cannot be greater than `60000`. Supports up to three decimal places of precision (e.g., 6000.346) so that microseconds may be specified. (e.g., 5000)
* **timestamp**:  (e.g., 1)
* **quantity**:  (e.g., 1)
* **quoteOrderQty**:  (e.g., 1)
* **price**:  (e.g., 400)
* **newClientOrderId**: A unique id among open orders. Automatically generated if not sent. Orders with the same `newClientOrderID` can be accepted only when the previous one is filled, otherwise the order will be rejected.
* **strategyId**:  (e.g., 1)
* **strategyType**: The value cannot be less than `1000000`. (e.g., 1)
* **stopPrice**: Used with `STOP_LOSS`, `STOP_LOSS_LIMIT`, `TAKE_PROFIT`, and `TAKE_PROFIT_LIMIT` orders. (e.g., 1)
* **trailingDelta**: See Trailing Stop order FAQ. (e.g., 1)
* **icebergQty**: Used with `LIMIT`, `STOP_LOSS_LIMIT`, and `TAKE_PROFIT_LIMIT` to create an iceberg order. (e.g., 1)
* **pegOffsetValue**: Priceleveltopegthepriceto(max:100). SeePeggedOrdersInfo (e.g., 1)
* **orderId**:  (e.g., 1)
* **origClientOrderId**:
* **newQty**: `newQty` must be greater than 0 and less than the order's quantity. (e.g., 1)
* **cancelNewClientOrderId**: Used to uniquely identify this cancel. Automatically generated by default.
* **cancelOrigClientOrderId**: Either `cancelOrderId` or `cancelOrigClientOrderId` must be sent.
* **cancelOrderId**: Either `cancelOrderId` or `cancelOrigClientOrderId` must be sent. (e.g., 1)
* **listClientOrderId**: A unique Id for the entire orderList
* **quantity**:  (e.g., 1)
* **limitClientOrderId**: A unique Id for the limit order
* **price**:  (e.g., 1)
* **limitStrategyId**:  (e.g., 1)
* **limitStrategyType**: The value cannot be less than `1000000`. (e.g., 1)
* **limitIcebergQty**: Used to make the `LIMIT_MAKER` leg an iceberg order. (e.g., 1)
* **stopClientOrderId**: A unique Id for the stop loss/stop loss limit leg
* **stopPrice**:  (e.g., 1)
* **stopStrategyId**:  (e.g., 1)
* **stopStrategyType**: The value cannot be less than `1000000`. (e.g., 1)
* **stopLimitPrice**: If provided, `stopLimitTimeInForce` is required. (e.g., 1)
* **stopIcebergQty**: Used with `STOP_LOSS_LIMIT` leg to make an iceberg order. (e.g., 1)
* **computeCommissionRates**: Default: `false`. See Commissions FAQ to learn more.
* **orderListId**: Either `orderListId` or `listClientOrderId` must be provided (e.g., 1)
* **aboveClientOrderId**: Arbitrary unique ID among open orders for the above order. Automatically generated if not sent.
* **aboveIcebergQty**: Note that this can only be used if `aboveTimeInForce` is `GTC`. (e.g., 1)
* **abovePrice**: Can be used if `aboveType` is `STOP_LOSS_LIMIT`, `LIMIT_MAKER`, or `TAKE_PROFIT_LIMIT` to specify the limit price. (e.g., 1)
* **aboveStopPrice**: Can be used if `aboveType` is `STOP_LOSS`, `STOP_LOSS_LIMIT`, `TAKE_PROFIT`, `TAKE_PROFIT_LIMIT`. (e.g., 1)
* **aboveTrailingDelta**: See Trailing Stop order FAQ. (e.g., 1)
* **aboveStrategyId**: Arbitrary numeric value identifying the above order within an order strategy. (e.g., 1)
* **aboveStrategyType**: Arbitrary numeric value identifying the above order strategy. Values smaller than 1000000 are reserved and cannot be used. (e.g., 1)
* **abovePegOffsetValue**:  (e.g., 1)
* **belowClientOrderId**: Arbitrary unique ID among open orders for the below order. Automatically generated if not sent.
* **belowIcebergQty**: Note that this can only be used if `belowTimeInForce` is `GTC`. (e.g., 1)
* **belowPrice**: Can be used if `belowType` is `STOP_LOSS_LIMIT`, `LIMIT_MAKER`, or `TAKE_PROFIT_LIMIT` to specify the limit price. (e.g., 1)
* **belowStopPrice**: Can be used if `belowType` is `STOP_LOSS`, `STOP_LOSS_LIMIT`, `TAKE_PROFIT`, or `TAKE_PROFIT_LIMIT`. (e.g., 1)
* **belowTrailingDelta**: See Trailing Stop order FAQ. (e.g., 1)
* **belowStrategyId**: Arbitrary numeric value identifying the below order within an order strategy. (e.g., 1)
* **belowStrategyType**: Arbitrary numeric value identifying the below order strategy. Values smaller than 1000000 are reserved and cannot be used. (e.g., 1)
* **belowPegOffsetValue**:  (e.g., 1)
* **workingClientOrderId**: Arbitrary unique ID among open orders for the working order. Automatically generated if not sent.
* **workingPrice**:  (e.g., 1)
* **workingQuantity**: Sets the quantity for the working order. (e.g., 1)
* **workingIcebergQty**: This can only be used if `workingTimeInForce` is `GTC`, or if `workingType` is `LIMIT_MAKER`. (e.g., 1)
* **workingStrategyId**: Arbitrary numeric value identifying the working order within an order strategy. (e.g., 1)
* **workingStrategyType**: Arbitrary numeric value identifying the working order strategy. Values smaller than 1000000 are reserved and cannot be used. (e.g., 1)
* **workingPegOffsetValue**:  (e.g., 1)
* **pendingClientOrderId**: Arbitrary unique ID among open orders for the pending order. Automatically generated if not sent.
* **pendingPrice**:  (e.g., 1)
* **pendingStopPrice**:  (e.g., 1)
* **pendingTrailingDelta**:  (e.g., 1)
* **pendingIcebergQty**: This can only be used if `pendingTimeInForce` is `GTC` or if `pendingType` is `LIMIT_MAKER`. (e.g., 1)
* **pendingStrategyId**: Arbitrary numeric value identifying the pending order within an order strategy. (e.g., 1)
* **pendingStrategyType**: Arbitrary numeric value identifying the pending order strategy. Values smaller than 1000000 are reserved and cannot be used. (e.g., 1)
* **pendingPegOffsetValue**:  (e.g., 1)
* **pendingAboveClientOrderId**: Arbitrary unique ID among open orders for the pending above order. Automatically generated if not sent.
* **pendingAbovePrice**: Can be used if `pendingAboveType` is `STOP_LOSS_LIMIT`, `LIMIT_MAKER`, or `TAKE_PROFIT_LIMIT` to specify the limit price. (e.g., 1)
* **pendingAboveStopPrice**: Can be used if `pendingAboveType` is `STOP_LOSS`, `STOP_LOSS_LIMIT`, `TAKE_PROFIT`, `TAKE_PROFIT_LIMIT` (e.g., 1)
* **pendingAboveTrailingDelta**: See Trailing Stop FAQ (e.g., 1)
* **pendingAboveIcebergQty**: This can only be used if `pendingAboveTimeInForce` is `GTC` or if `pendingAboveType` is `LIMIT_MAKER`. (e.g., 1)
* **pendingAboveStrategyId**: Arbitrary numeric value identifying the pending above order within an order strategy. (e.g., 1)
* **pendingAboveStrategyType**: Arbitrary numeric value identifying the pending above order strategy. Values smaller than 1000000 are reserved and cannot be used. (e.g., 1)
* **pendingAbovePegOffsetValue**:  (e.g., 1)
* **pendingBelowClientOrderId**: Arbitrary unique ID among open orders for the pending below order. Automatically generated if not sent.
* **pendingBelowPrice**: Can be used if `pendingBelowType` is `STOP_LOSS_LIMIT` or `TAKE_PROFIT_LIMIT` to specify limit price (e.g., 1)
* **pendingBelowStopPrice**: Can be used if `pendingBelowType` is `STOP_LOSS`, `STOP_LOSS_LIMIT`, `TAKE_PROFIT`, or `TAKE_PROFIT_LIMIT`. (e.g., 1)
* **pendingBelowTrailingDelta**:  (e.g., 1)
* **pendingBelowIcebergQty**: This can only be used if `pendingBelowTimeInForce` is `GTC`, or if `pendingBelowType` is `LIMIT_MAKER`. (e.g., 1)
* **pendingBelowStrategyId**: Arbitrary numeric value identifying the pending below order within an order strategy. (e.g., 1)
* **pendingBelowStrategyType**: Arbitrary numeric value identifying the pending below order strategy. Values smaller than 1000000 are reserved and cannot be used. (e.g., 1)
* **pendingBelowPegOffsetValue**:  (e.g., 1)
* **pendingQuantity**: Sets the quantity for the pending order. (e.g., 1)
* **omitZeroBalances**: When set to `true`, emits only the non-zero balances of an account. Default value: `false`
* **fromAllocationId**:  (e.g., 1)
* **timestamp**:  (e.g., 1)
* **preventedMatchId**:  (e.g., 1)
* **fromPreventedMatchId**:  (e.g., 1)
* **orderId**:  (e.g., 1)
* **fromExecutionId**:  (e.g., 1)
* **limit**: Default:500; Maximum: 1000 (e.g., 500)

### Enums

* **interval**: 1s | 1m | 3m | 5m | 15m | 30m | 1h | 2h | 4h | 6h | 8h | 12h | 1d | 3d | 1w | 1M
* **windowSize**: 1m ... 6d
* **type**: FULL | MINI
* **type**: MARKET | LIMIT | STOP_LOSS | STOP_LOSS_LIMIT | TAKE_PROFIT | TAKE_PROFIT_LIMIT | LIMIT_MAKER | NON_REPRESENTABLE
* **selfTradePreventionMode**: NONE | EXPIRE_TAKER | EXPIRE_MAKER | EXPIRE_BOTH | DECREMENT | NON_REPRESENTABLE
* **symbolStatus**: TRADING | END_OF_DAY | HALT | BREAK | NON_REPRESENTABLE
* **timeInForce**: GTC | IOC | FOK | NON_REPRESENTABLE
* **pegPriceType**: PRIMARY_PEG | MARKET_PEG | NON_REPRESENTABLE
* **pegOffsetType**: PRICE_LEVEL | NON_REPRESENTABLE
* **newOrderRespType**: ACK | RESULT | FULL | MARKET | LIMIT
* **cancelRestrictions**: ONLY_NEW | NEW | ONLY_PARTIALLY_FILLED | PARTIALLY_FILLED
* **cancelReplaceMode**: STOP_ON_FAILURE | ALLOW_FAILURE
* **orderRateLimitExceededMode**: DO_NOTHING | CANCEL_ONLY
* **stopLimitTimeInForce**: GTC | IOC | FOK
* **side**: BUY | SELL
* **workingSide**: BUY | SELL

## Authentication

For endpoints that require authentication, you will need to provide Binance API credentials.
Required credentials:

* apiKey: Your Binance API key (for header)
* secretKey: Your Binance API secret (for signing)

Base URLs:
* Mainnet: https://api.binance.com
* Testnet: https://testnet.binance.vision
* Demo: https://demo-api.binance.com

## Security

### Share Credentials

Users can provide Binance API credentials by sending a file where the content is in the following format:

```bash
abc123...xyz
secret123...key
```

### Never Display Full Secrets

When showing credentials to users:
- **API Key:** Show first 5 + last 4 characters: `su1Qc...8akf`
- **Secret Key:** Always mask, show only last 5: `***...aws1`

Example response when asked for credentials:
Account: main
API Key: su1Qc...8akf
Secret: ***...aws1
Environment: Mainnet

### Listing Accounts

When listing accounts, show names and environment only - never keys:
Binance Accounts:
* main (Mainnet/Testnet)
* testnet-dev (Testnet)
* futures-keys (Mainnet)

### Transactions in Mainnet

When performing transactions in mainnet, always confirm with the user before proceeding by asking them to write "CONFIRM" to proceed.

## Agent Behavior

1. Credentials requested: Mask secrets (show last 5 chars only)
2. Listing accounts: Show names and environment, never keys
3. Account selection: Ask if ambiguous, default to main
4. When doing a transaction in mainnet, confirm with user before by asking to write "CONFIRM" to proceed
5. If credentials are missing, ask the user to provide them in the current chat/session.

## Signing Requests

All trading endpoints require HMAC SHA256 signature:

1. Build query string with all params + timestamp (Unix ms)
2. Sign query string with secretKey using HMAC SHA256, RSA, or Ed25519 (depending on account config)
3. Append signature to query string
4. Include `X-MBX-APIKEY` header

## User Agent Header

Include `User-Agent` header with the following string: `binance-spot/1.0.1 (Skill)`

See [`references/authentication.md`](./references/authentication.md) for implementation details.
