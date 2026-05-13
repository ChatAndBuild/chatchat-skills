---
id: crypto-market-rank
name: Crypto Market Rank
description: Use this skill when retrieving or interpreting crypto market rankings and leaderboards for trending tokens, social hype, smart-money inflow, meme ranks, or top-trader PnL.
category: Blockchain
author: binance-web3-team
version: 2.0.0
---

# Crypto Market Rank Skill

## Overview

| API | Function | Use Case |
|-----|----------|----------|
| Social Hype Leaderboard | Social buzz ranking | Sentiment analysis, social summaries |
| Unified Token Rank | Multi-type token rankings | Trending, Top Search, Alpha, Stock with filters |
| Smart Money Inflow Rank | Token rank by smart money buys | Discover tokens smart money is buying most |
| Meme Rank | Top meme tokens from Pulse launchpad | Find meme tokens most likely to break out |
| Address PnL Rank | Top trader PnL leaderboard | Top PnL traders / KOL performance ranking |

## Use Cases

1. **Social Hype Analysis**: Discover tokens with highest social buzz and sentiment
2. **Trending Tokens**: View currently trending tokens (`rankType=10`)
3. **Top Searched**: See most searched tokens (`rankType=11`)
4. **Alpha Discovery**: Browse Binance Alpha picks (`rankType=20`)
5. **Stock Tokens**: View tokenized stocks (`rankType=40`)
6. **Smart Money Inflow**: Discover which tokens smart money is buying most
7. **Meme Rank**: Find top meme tokens from Pulse launchpad most likely to break out
8. **PnL Leaderboard**: View top-performing trader addresses, PnL, win rates
9. **Filtered Research**: Combine filters for targeted token or address screening

## Supported Chains

| Chain | chainId |
|-------|---------|
| BSC | 56 |
| Base | 8453 |
| Solana | CT_501 |

---

## API 1: Social Hype Leaderboard

### Method: GET

**URL**:
`https://web3.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/market/token/pulse/social/hype/rank/leaderboard`

**Request Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| chainId | string | Yes | Chain ID |
| sentiment | string | No | Filter: `All`, `Positive`, `Negative`, `Neutral` |
| targetLanguage | string | Yes | Translation target, e.g. `en`, `zh` |
| timeRange | number | Yes | Time range, `1` = 24 hours |
| socialLanguage | string | No | Content language, `ALL` for all |

**Headers**: `Accept-Encoding: identity`

---

## API 2: Unified Token Rank

### Method: POST (recommended) / GET

**URL**:
`https://web3.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/market/token/pulse/unified/rank/list`

**Headers**: `Content-Type: application/json`, `Accept-Encoding: identity`

### Rank Types

| rankType | Name | Description |
|----------|------|-------------|
| 10 | Trending | Hot trending tokens |
| 11 | Top Search | Most searched tokens |
| 20 | Alpha | Alpha tokens (Binance Alpha picks) |
| 40 | Stock | Tokenized stock tokens |

### Request Body (all fields optional)

**Core Parameters**:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| rankType | integer | 10 | Rank type: `10`=Trending, `11`=TopSearch, `20`=Alpha, `40`=Stock |
| chainId | string | - | Chain ID: `1`, `56`, `8453`, `CT_501` |
| period | integer | 50 | Time period: `10`=1m, `20`=5m, `30`=1h, `40`=4h, `50`=24h |
| sortBy | integer | 0 | Sort field (see Sort Options) |
| orderAsc | boolean | false | Ascending order if true |
| page | integer | 1 | Page number (min 1) |
| size | integer | 200 | Page size (max 200) |

**Filter Parameters (Min/Max pairs)**:

| Filter | Type | Description |
|--------|------|-------------|
| percentChangeMin/Max | decimal | Price change range (%) |
| marketCapMin/Max | decimal | Market cap range (USD) |
| volumeMin/Max | decimal | Volume range (USD) |
| liquidityMin/Max | decimal | Liquidity range (USD) |
| holdersMin/Max | long | Holder count range |
| holdersTop10PercentMin/Max | decimal | Top10 holder % range |
| kycHoldersMin/Max | long | KYC holder count (Alpha only) |
| countMin/Max | long | Transaction count range |
| uniqueTraderMin/Max | long | Unique trader count range |
| launchTimeMin/Max | long | Token launch time range (timestamp ms) |

**Advanced Filters**:

| Field | Type | Description |
|-------|------|-------------|
| keywords | string[] | Include symbols matching these keywords |
| excludes | string[] | Exclude these symbols |
| socials | integer[] | Social filter: `0`=at least one, `1`=X, `2`=Telegram, `3`=Website |
| alphaTagFilter | string[] | Alpha narrative tags |
| auditFilter | integer[] | Audit: `0`=not renounced, `1`=freezable, `2`=mintable |
| tagFilter | integer[] | Tag filter: `0`=hide alpha, `23`=dex paid, `29`=alpha points, etc. |

### Sort Options

| sortBy | Field |
|--------|-------|
| 0 | Default |
| 1 | Web default |
| 2 | Search count |
| 10 | Launch time |
| 20 | Liquidity |
| 30 | Holders |
| 40 | Market cap |
| 50 | Price change |
| 60 | Transaction count |
| 70 | Volume |
| 80 | KYC holders |
| 90 | Price |
| 100 | Unique traders |

### Example Request

```bash
curl -X POST 'https://web3.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/market/token/pulse/unified/rank/list' \
-H 'Content-Type: application/json' \
-H 'Accept-Encoding: identity' \
-d '{"rankType":10,"chainId":"1","period":50,"sortBy":70,"orderAsc":false,"page":1,"size":20}'
```

---

## API 3: Smart Money Inflow Rank

### Method: POST

**URL**:
`https://web3.binance.com/bapi/defi/v1/public/wallet-direct/tracker/wallet/token/inflow/rank/query`

**Headers**: `Content-Type: application/json`, `Accept-Encoding: identity`

**Request Body**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| chainId | string | Yes | Chain ID: `56` (BSC), `CT_501` (Solana) |
| period | string | No | Stats window: `5m`, `1h`, `4h`, `24h` |
| tagType | integer | No | Address tag type (e.g. `2`) |

### Example Request

```bash
curl -X POST 'https://web3.binance.com/bapi/defi/v1/public/wallet-direct/tracker/wallet/token/inflow/rank/query' \
-H 'Content-Type: application/json' \
-H 'Accept-Encoding: identity' \
-d '{"chainId":"56","period":"24h","tagType":2}'
```

---

## API 4: Meme Rank

### Method: GET

**URL**:
`https://web3.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/market/token/pulse/exclusive/rank/list`

**Headers**: `Accept-Encoding: identity`

**Request Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| chainId | string | Yes | Chain ID: `56` (BSC) |

Returns top 100 meme tokens launched via Pulse platform, scored and ranked by an algorithm evaluating breakout potential.

### Example Request

```bash
curl 'https://web3.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/market/token/pulse/exclusive/rank/list?chainId=56' \
-H 'Accept-Encoding: identity'
```

---

## API 5: Address PnL Rank

### Method: GET

**URL**:
`https://web3.binance.com/bapi/defi/v1/public/wallet-direct/market/leaderboard/query`

**Headers**: `Accept-Encoding: identity`

**Request Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| chainId | string | Yes | Chain ID: `56` (BSC), `CT_501` (Solana) |
| period | string | No | Time period: `7d`, `30d`, `90d` |
| tag | string | No | Address tag filter: `ALL`, `KOL` |
| sortBy | integer | No | Sort field |
| orderBy | integer | No | Order direction |
| pageNo | integer | No | Page number (min 1) |
| pageSize | integer | No | Page size (max 25) |

**Filter Parameters (Min/Max pairs)**:

| Filter | Type | Description |
|--------|------|-------------|
| PNLMin/Max | decimal | Realized PnL range (USD) |
| winRateMin/Max | decimal | Win rate range (percentage, e.g. `1` = 1%) |
| txMin/Max | long | Transaction count range |
| volumeMin/Max | decimal | Volume range (USD) |

### Example Request

```bash
curl 'https://web3.binance.com/bapi/defi/v1/public/wallet-direct/market/leaderboard/query?tag=ALL&pageNo=1&chainId=CT_501&pageSize=25&sortBy=0&orderBy=0&period=30d' \
-H 'Accept-Encoding: identity'
```

---

## Notes

1. Icon/logo URLs require prefix: `https://bin.bnbstatic.com` + path
2. Unified Token Rank supports both GET and POST; POST is recommended
3. Numeric fields in responses may be returned as strings, so parse as needed
4. Period fields use shorthand (`1m`, `5m`, `1h`, `4h`, `24h`) across multiple stats fields
