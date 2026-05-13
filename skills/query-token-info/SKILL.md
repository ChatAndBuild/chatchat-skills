---
id: query-token-info
name: Query Token Info
description: Use this skill when searching or researching tokens by keyword, contract address, or chain, including metadata, social links, real-time market data, holder/liquidity signals, and K-line candlestick data.
category: Blockchain
author: binance-web3-team
version: 1.0.0
---

# Query Token Info Skill

## Overview

| API | Function | Use Case |
|-----|----------|----------|
| Token Search | Search tokens | Find tokens by name, symbol, or contract address |
| Token Metadata | Static info | Get token details, name, symbol, logo, social links, creator address |
| Token Dynamic Data | Real-time market data | Price, volume, holders, liquidity, market cap |
| Token K-Line | Candlestick charts | OHLCV data for technical analysis |

## Use Cases

1. **Search Tokens**: Find tokens by name, symbol, or contract address across chains
2. **Project Research**: Get token metadata, social links, and creator info
3. **Market Analysis**: Real-time price, volume, holder distribution, and liquidity data
4. **Chart Analysis**: K-Line candlestick data for technical analysis

## Supported Chains

| Chain Name | chainId |
|------------|---------|
| BSC | 56 |
| Base | 8453 |
| Solana | CT_501 |

---

## API 1: Token Search

### Method: GET

**URL**:
`https://web3.binance.com/bapi/defi/v5/public/wallet-direct/buw/wallet/market/token/search`

**Request Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| keyword | string | Yes | Search keyword (name/symbol/contract address) |
| chainIds | string | No | Chain ID list, comma-separated, e.g., `56,8453,CT_501` |
| orderBy | string | No | Sort field, e.g., `volume24h` |

**Request Headers**:
```text
Accept-Encoding: identity
```

**Example Request**:
```bash
curl --location 'https://web3.binance.com/bapi/defi/v5/public/wallet-direct/buw/wallet/market/token/search?keyword=xxx&chainIds=56,8453,CT_501&orderBy=volume24h' \
--header 'Accept-Encoding: identity'
```

**Response Example**:
```json
{
  "code": "000000",
  "data": [
    {
      "chainId": "56",
      "contractAddress": "0x1234...",
      "tokenId": "CC1F457...",
      "name": "Token",
      "symbol": "symbol of token",
      "icon": "/images/web3-data/public/token/logos/xxx.png",
      "price": "47.98771375939603199404",
      "percentChange24h": "-0.01",
      "volume24h": "53687246.955803546359104902201",
      "marketCap": "162198400",
      "liquidity": "13388877.147327333572157",
      "tokenAddresses": [],
      "tagsInfo": {
        "AI Analysis": [{"tagName": "AI Widget", "languageKey": "wmp-label-title-ai-widget"}],
        "Community Recognition Level": [{"tagName": "Alpha", "languageKey": "wmp-label-title-alpha"}]
      },
      "links": [
        {"label": "website", "link": "https://www.web.site/"},
        {"label": "x", "link": "https://twitter.com/..."}
      ],
      "createTime": 1600611727000,
      "holdersTop10Percent": "93.267178480644823",
      "riskLevel": null
    }
  ],
  "success": true
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| chainId | string | Chain ID |
| contractAddress | string | Contract address |
| tokenId | string | Token unique ID |
| name | string | Token name |
| symbol | string | Token symbol |
| icon | string | Icon URL path |
| price | string | Current price (USD) |
| percentChange24h | string | 24-hour price change (%) |
| volume24h | string | 24-hour trading volume (USD) |
| marketCap | string | Market cap (USD) |
| liquidity | string | Liquidity (USD) |
| tagsInfo | object | Tag information |
| links | array | Social links list |
| createTime | number | Creation timestamp (ms) |
| holdersTop10Percent | string | Top 10 holders percentage (%) |

---

## API 2: Token Metadata

### Method: GET

**URL**:
`https://web3.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/dex/market/token/meta/info`

**Request Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| chainId | string | Yes | Chain ID |
| contractAddress | string | Yes | Token contract address |

**Request Headers**:
```text
Accept-Encoding: identity
```

**Example Request**:
```bash
curl --location 'https://web3.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/dex/market/token/meta/info?chainId=56&contractAddress=0x55d398326f99059ff775485246999027b3197955' \
--header 'Accept-Encoding: identity'
```

**Response Example**:
```json
{
  "code": "000000",
  "data": {
    "tokenId": "CC1F457B",
    "name": "name of Token",
    "symbol": "symbol of token",
    "chainId": "56",
    "chainIconUrl": "https://bin.bnbstatic.com/image/admin_mgs_image_upload/20250228/d0216ce4-a3e9-4bda-8937-4a6aa943ccf2.png",
    "chainName": "BSC",
    "contractAddress": "0x55d398326f99059ff775485246999027b3197955",
    "decimals": 18,
    "icon": "/images/web3-data/public/token/logos/xxx.png",
    "nativeAddressFlag": false,
    "aiNarrativeFlag": 1,
    "links": [
      {"label": "website", "link": "https://www.web.site/"},
      {"label": "whitepaper", "link": "https://drive.google.com/file/d/..."},
      {"label": "x", "link": "https://twitter.com/..."}
    ],
    "previewLink": {
      "website": ["https://www.web.site/"],
      "x": ["https://twitter.com/..."],
      "tg": []
    },
    "createTime": 1600611727000,
    "creatorAddress": "0x1234...",
    "auditInfo": {
      "isBlacklist": false,
      "isWhitelist": true
    },
    "description": "this is a good token..."
  },
  "success": true
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| tokenId | string | Token unique ID |
| name | string | Token name |
| symbol | string | Token symbol |
| chainId | string | Chain ID |
| chainName | string | Chain name |
| contractAddress | string | Contract address |
| decimals | number | Token decimals |
| icon | string | Icon URL path |
| links | array | Social links list |
| createTime | number | Creation timestamp (ms) |
| creatorAddress | string | Creator address |
| description | string | Token description |

---

## API 3: Token Dynamic Data

### Method: GET

**URL**:
`https://web3.binance.com/bapi/defi/v4/public/wallet-direct/buw/wallet/market/token/dynamic/info`

**Request Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| chainId | string | Yes | Chain ID |
| contractAddress | string | Yes | Token contract address |

**Request Headers**:
```text
Accept-Encoding: identity
```

**Example Request**:
```bash
curl --location 'https://web3.binance.com/bapi/defi/v4/public/wallet-direct/buw/wallet/market/token/dynamic/info?chainId=56&contractAddress=0x55d398326f99059ff775485246999027b3197955' \
--header 'Accept-Encoding: identity'
```

**Response Fields**:

### Price Related
| Field | Type | Description |
|-------|------|-------------|
| price | string | Current price (USD) |
| nativeTokenPrice | string | Native token price |
| priceHigh24h | string | 24-hour high price |
| priceLow24h | string | 24-hour low price |

### Price Change
| Field | Type | Description |
|-------|------|-------------|
| percentChange5m | string | 5-minute price change (%) |
| percentChange1h | string | 1-hour price change (%) |
| percentChange4h | string | 4-hour price change (%) |
| percentChange24h | string | 24-hour price change (%) |

### Volume
| Field | Type | Description |
|-------|------|-------------|
| volume24h | string | 24-hour total volume (USD) |
| volume24hBuy | string | 24-hour buy volume |
| volume24hSell | string | 24-hour sell volume |
| volume4h | string | 4-hour volume |
| volume1h | string | 1-hour volume |
| volume5m | string | 5-minute volume |

### Transaction Count
| Field | Type | Description |
|-------|------|-------------|
| count24h | string | 24-hour transaction count |
| count24hBuy | string | 24-hour buy count |
| count24hSell | string | 24-hour sell count |

### Market Data
| Field | Type | Description |
|-------|------|-------------|
| marketCap | string | Market cap (USD) |
| fdv | string | Fully diluted valuation |
| totalSupply | string | Total supply |
| circulatingSupply | string | Circulating supply |
| liquidity | string | Liquidity (USD) |

### Holder Data
| Field | Type | Description |
|-------|------|-------------|
| holders | string | Total holder count |
| top10HoldersPercentage | string | Top 10 holders percentage (%) |
| kycHolderCount | string | KYC holder count |
| kolHolders | string | KOL holder count |
| kolHoldingPercent | string | KOL holding percentage |
| devHoldingPercent | string | Dev holding percentage |
| proHoldingPercent | string | Professional investor holding percentage |
| smartMoneyHoldingPercent | string | Smart money holding percentage |

---

## API 4: Token K-Line (Candlestick)

### Method: GET

**URL**:
`https://dquery.sintral.io/u-kline/v1/k-line/candles`

**Request Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| address | string | Yes | Token contract address |
| platform | string | Yes | Chain platform: `eth`, `bsc`, `solana`, `base` |
| interval | string | Yes | Kline interval (see Interval Reference below) |
| limit | number | No | Number of candles to return (has higher priority than `from`) |
| from | number | No | Start timestamp in milliseconds |
| to | number | No | End timestamp in milliseconds |
| pm | string | No | Kline type: `p` for price, `m` for market cap (default: `p`) |

**Interval Reference**:

| Interval | Description |
|----------|-------------|
| 1s | 1 second |
| 1min | 1 minute |
| 3min | 3 minutes |
| 5min | 5 minutes |
| 15min | 15 minutes |
| 30min | 30 minutes |
| 1h | 1 hour |
| 2h | 2 hours |
| 4h | 4 hours |
| 6h | 6 hours |
| 8h | 8 hours |
| 12h | 12 hours |
| 1d | 1 day |
| 3d | 3 days |
| 1w | 1 week |
| 1m | 1 month |

**Platform Mapping**:

| Chain | platform value |
|-------|---------------|
| Ethereum | eth |
| BSC | bsc |
| Solana | solana |
| Base | base |

**Request Headers**:
```text
Accept-Encoding: identity
```

**Example Request**:
```bash
curl --location 'https://dquery.sintral.io/u-kline/v1/k-line/candles?address=0x55d398326f99059ff775485246999027b3197955&interval=1min&limit=500&platform=bsc&to=1772126280000' \
--header 'Accept-Encoding: identity'
```

**Response Fields**:

Each candle is an array with 7 elements in order:

| Index | Field | Type | Description |
|-------|-------|------|-------------|
| 0 | open | number | Open price |
| 1 | high | number | High price |
| 2 | low | number | Low price |
| 3 | close | number | Close price |
| 4 | volume | number | Trading volume |
| 5 | timestamp | number | Candle timestamp (ms) |
| 6 | count | number | Transaction count |

---

## Notes

1. Icon URL requires full domain prefix: `https://bin.bnbstatic.com` + icon path
2. Numeric fields are often strings, convert when needed
3. Dynamic data updates in real time, suitable for market display
4. K-Line API uses `platform` (`eth`/`bsc`/`solana`/`base`) instead of `chainId`, and `limit` takes priority over `from` when both are provided
5. K-Line response is a 2D array (not JSON objects): `[open, high, low, close, volume, timestamp, count]`
