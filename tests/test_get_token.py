"""Phase 1 tests — token data fetching from DexScreener."""

import asyncio
import json

from solexplorer.solana.get_token import (
    fetch_token_pairs,
    get_token_overview,
    validate_solana_address,
)

SOL_MINT = "So11111111111111111111111111111111111111112"
INVALID_ADDRESS = "not-a-real-address-123"


def test_validate_address_ok() -> None:
    result = validate_solana_address(SOL_MINT)
    assert result == SOL_MINT
    print(f"[PASS] validate_solana_address('{SOL_MINT}') -> '{result}'")


def test_validate_address_bad() -> None:
    try:
        validate_solana_address(INVALID_ADDRESS)
        print("[FAIL] Expected HTTPException for invalid address")
    except Exception as exc:
        print(f"[PASS] Invalid address rejected: {exc}")


async def test_fetch_token_pairs() -> None:
    data = await fetch_token_pairs(SOL_MINT)
    assert data.pairs is not None, "pairs should not be None"
    print(f"[PASS] fetch_token_pairs returned {len(data.pairs)} pairs")
    print(f"       First pair DEX: {data.pairs[0].dexId}, chain: {data.pairs[0].chainId}")


async def test_get_token_overview() -> None:
    overview = await get_token_overview(SOL_MINT)
    print(f"[PASS] get_token_overview:")
    print(json.dumps(
        overview.model_dump(exclude={"pairs"}),
        indent=2,
        ensure_ascii=False,
    ))
    assert overview.num_pools > 0
    assert overview.total_liquidity_usd > 0
    assert len(overview.dex_names) >= 1
    print(f"       Pools: {overview.num_pools}, DEXes: {overview.dex_names}")


async def test_nonexistent_token() -> None:
    fake_address = "11111111111111111111111111111111"
    try:
        await get_token_overview(fake_address)
        print("[FAIL] Expected HTTPException for non-existent token")
    except Exception as exc:
        print(f"[PASS] Non-existent token rejected: {exc}")


async def main() -> None:
    print("=" * 60)
    print("Phase 1 Tests: Token Data Module")
    print("=" * 60)

    print("\n--- Address Validation ---")
    test_validate_address_ok()
    test_validate_address_bad()

    print("\n--- Fetch Token Pairs ---")
    await test_fetch_token_pairs()

    print("\n--- Token Overview ---")
    await test_get_token_overview()

    print("\n--- Non-existent Token ---")
    await test_nonexistent_token()

    print("\n" + "=" * 60)
    print("Phase 1: ALL TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
