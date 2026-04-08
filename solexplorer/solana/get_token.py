import logging

import httpx
from fastapi import HTTPException
from solders.pubkey import Pubkey

from solexplorer.config.app import get_settings
from solexplorer.schemas.token import (
    DexPair,
    DexScreenerResponse,
    TokenOverview,
)

logger = logging.getLogger(__name__)


def validate_solana_address(address: str) -> str:
    """Validate that *address* is a legal Solana base-58 public key.

    Args:
        address: Raw string from the user.

    Returns:
        The canonical string representation of the address.

    Raises:
        HTTPException: 400 if the address is malformed.
    """
    try:
        pubkey = Pubkey.from_string(address)
        return str(pubkey)
    except (ValueError, Exception) as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid Solana address: {exc}",
        ) from exc


async def fetch_token_pairs(address: str) -> DexScreenerResponse:
    """Fetch all trading pairs for a token from DexScreener.

    Args:
        address: Validated Solana mint address.

    Returns:
        Parsed DexScreener API response.

    Raises:
        HTTPException: 503 when the external API is unreachable.
    """
    settings = get_settings()
    url = f"{settings.dexscreener_base_url}/latest/dex/tokens/{address}"

    try:
        async with httpx.AsyncClient(timeout=settings.http_timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            return DexScreenerResponse.model_validate(response.json())
    except httpx.TimeoutException as exc:
        logger.error("DexScreener timeout for %s: %s", address, exc)
        raise HTTPException(
            status_code=503,
            detail="External API unavailable (timeout)",
        ) from exc
    except httpx.HTTPStatusError as exc:
        logger.error("DexScreener HTTP error for %s: %s", address, exc)
        raise HTTPException(
            status_code=503,
            detail=f"External API returned {exc.response.status_code}",
        ) from exc
    except httpx.HTTPError as exc:
        logger.error("DexScreener request failed for %s: %s", address, exc)
        raise HTTPException(
            status_code=503,
            detail="External API unavailable",
        ) from exc


def _filter_solana_pairs(pairs: list[DexPair]) -> list[DexPair]:
    """Keep only pairs that belong to the Solana chain."""
    return [p for p in pairs if p.chainId == "solana"]


async def get_token_overview(address: str) -> TokenOverview:
    """Fetch token data and build an aggregated overview.

    Args:
        address: Raw token address (will be validated).

    Returns:
        Aggregated TokenOverview with all Solana pairs.

    Raises:
        HTTPException: 400/404/503 depending on failure mode.
    """
    validated = validate_solana_address(address)
    data = await fetch_token_pairs(validated)

    if not data.pairs:
        raise HTTPException(
            status_code=404,
            detail="Token not found or has no liquidity pools",
        )

    solana_pairs = _filter_solana_pairs(data.pairs)
    if not solana_pairs:
        raise HTTPException(
            status_code=404,
            detail="Token not found or has no liquidity pools on Solana",
        )

    first = solana_pairs[0]
    base_is_target = first.baseToken.address == validated
    token_info = first.baseToken if base_is_target else first.quoteToken

    total_liquidity = sum(p.liquidity.usd for p in solana_pairs)
    total_volume_24h = sum(p.volume.h24 for p in solana_pairs)
    dex_names = sorted({p.dexId for p in solana_pairs})

    try:
        price_usd = float(first.priceUsd)
    except (ValueError, TypeError):
        price_usd = 0.0

    fdv_values = [p.fdv for p in solana_pairs if p.fdv is not None]
    mc_values = [p.marketCap for p in solana_pairs if p.marketCap is not None]
    image_url = first.info.imageUrl if first.info else None

    return TokenOverview(
        address=token_info.address,
        name=token_info.name,
        symbol=token_info.symbol,
        price_usd=price_usd,
        total_liquidity_usd=total_liquidity,
        total_volume_24h=total_volume_24h,
        num_pools=len(solana_pairs),
        dex_names=dex_names,
        fdv=fdv_values[0] if fdv_values else None,
        market_cap=mc_values[0] if mc_values else None,
        image_url=image_url,
        pairs=solana_pairs,
    )
