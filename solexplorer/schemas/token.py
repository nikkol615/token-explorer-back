from __future__ import annotations

from pydantic import BaseModel, Field


class DexTokenInfo(BaseModel):
    """Base / quote token descriptor returned by DexScreener."""

    address: str
    name: str
    symbol: str


class DexTxnCounts(BaseModel):
    """Buy/sell transaction counts for a single time window."""

    buys: int = 0
    sells: int = 0


class DexTransactions(BaseModel):
    """Transaction counts across time windows."""

    m5: DexTxnCounts = Field(default_factory=DexTxnCounts)
    h1: DexTxnCounts = Field(default_factory=DexTxnCounts)
    h6: DexTxnCounts = Field(default_factory=DexTxnCounts)
    h24: DexTxnCounts = Field(default_factory=DexTxnCounts)


class DexVolume(BaseModel):
    """Trading volume in USD across time windows."""

    h24: float = 0.0
    h6: float = 0.0
    h1: float = 0.0
    m5: float = 0.0


class DexPriceChange(BaseModel):
    """Price change percentages (may be absent for some windows)."""

    m5: float | None = None
    h1: float | None = None
    h6: float | None = None
    h24: float | None = None


class DexLiquidity(BaseModel):
    """Liquidity data for a pair."""

    usd: float = 0.0
    base: float = 0.0
    quote: float = 0.0


class DexPairInfo(BaseModel):
    """Optional metadata attached to a pair (images, links)."""

    imageUrl: str | None = None
    header: str | None = None
    openGraph: str | None = None
    websites: list[dict[str, str]] = Field(default_factory=list)
    socials: list[dict[str, str]] = Field(default_factory=list)


class DexPair(BaseModel):
    """A single DEX trading pair from the DexScreener response."""

    chainId: str
    dexId: str
    url: str
    pairAddress: str
    labels: list[str] = Field(default_factory=list)
    baseToken: DexTokenInfo
    quoteToken: DexTokenInfo
    priceNative: str = "0"
    priceUsd: str = "0"
    txns: DexTransactions = Field(default_factory=DexTransactions)
    volume: DexVolume = Field(default_factory=DexVolume)
    priceChange: DexPriceChange = Field(default_factory=DexPriceChange)
    liquidity: DexLiquidity = Field(default_factory=DexLiquidity)
    fdv: float | None = None
    marketCap: float | None = None
    pairCreatedAt: int = 0
    info: DexPairInfo | None = None


class DexScreenerResponse(BaseModel):
    """Top-level response from GET /latest/dex/tokens/{address}."""

    schemaVersion: str = ""
    pairs: list[DexPair] | None = None


class TokenOverview(BaseModel):
    """Aggregated token summary built from the list of DexScreener pairs."""

    address: str
    name: str
    symbol: str
    price_usd: float
    total_liquidity_usd: float
    total_volume_24h: float
    num_pools: int
    dex_names: list[str]
    fdv: float | None = None
    market_cap: float | None = None
    image_url: str | None = None
    pairs: list[DexPair]
