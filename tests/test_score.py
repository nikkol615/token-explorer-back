"""Phase 2 tests — scoring logic with real API data and synthetic edge cases."""

import asyncio
import json
import time

from solexplorer.analyse.get_score import calculate_score
from solexplorer.schemas.token import (
    DexLiquidity,
    DexPair,
    DexTokenInfo,
    DexVolume,
)
from solexplorer.solana.get_token import get_token_overview

SOL_MINT = "So11111111111111111111111111111111111111112"

_DUMMY_TOKEN = DexTokenInfo(address="Abc111", name="Test", symbol="TST")
_DUMMY_QUOTE = DexTokenInfo(address="Xyz999", name="USDC", symbol="USDC")
_MS_IN_HOUR = 3_600_000


def _make_pair(
    dex_id: str = "raydium",
    liquidity_usd: float = 100_000,
    volume_h24: float = 50_000,
    created_hours_ago: float = 48,
) -> DexPair:
    """Helper: build a minimal DexPair for unit-style tests."""
    now_ms = int(time.time() * 1000)
    return DexPair(
        chainId="solana",
        dexId=dex_id,
        url="https://dexscreener.com/solana/test",
        pairAddress="TestPair123",
        baseToken=_DUMMY_TOKEN,
        quoteToken=_DUMMY_QUOTE,
        liquidity=DexLiquidity(usd=liquidity_usd, base=0, quote=0),
        volume=DexVolume(h24=volume_h24, h6=0, h1=0, m5=0),
        pairCreatedAt=int(now_ms - created_hours_ago * _MS_IN_HOUR),
    )


def _print_score(label: str, score) -> None:  # noqa: ANN001
    print(f"\n--- {label} ---")
    print(json.dumps(score.model_dump(), indent=2, ensure_ascii=False))


async def test_real_data_score() -> None:
    """Score SOL using live DexScreener data."""
    overview = await get_token_overview(SOL_MINT)
    score = calculate_score(overview.pairs)
    _print_score(f"Real data: {overview.symbol} ({overview.num_pools} pools)", score)
    assert score.total_score > 0, "SOL should score > 0"
    assert score.status_emoji == "\U0001f7e2", "SOL should be green"
    print(f"[PASS] {overview.symbol} scored {score.total_score}/100 {score.status_emoji}")


def test_single_dex_low_liq() -> None:
    """1 DEX, $5k liquidity, new pool (<1h) -> low score."""
    pairs = [_make_pair(liquidity_usd=5000, volume_h24=100, created_hours_ago=0.5)]
    score = calculate_score(pairs)
    _print_score("Edge: 1 DEX, $5k liq, 30min old", score)
    assert score.total_score < 40, f"Expected red, got {score.total_score}"
    assert score.status_emoji == "\U0001f534"
    print(f"[PASS] Low score {score.total_score}/100 {score.status_emoji}")


def test_multi_dex_healthy() -> None:
    """3 DEXes, $300k liquidity, healthy volume, old pools -> high score."""
    pairs = [
        _make_pair("raydium", 150_000, 200_000, 720),
        _make_pair("orca", 100_000, 150_000, 480),
        _make_pair("meteora", 50_000, 80_000, 240),
    ]
    score = calculate_score(pairs)
    _print_score("Edge: 3 DEX, $300k liq, healthy", score)
    assert score.total_score > 70, f"Expected green, got {score.total_score}"
    assert score.status_emoji == "\U0001f7e2"
    print(f"[PASS] High score {score.total_score}/100 {score.status_emoji}")


def test_wash_trading_signal() -> None:
    """Volume >> liquidity (ratio > 5) should penalise."""
    pairs = [_make_pair(liquidity_usd=10_000, volume_h24=500_000, created_hours_ago=48)]
    score = calculate_score(pairs)
    _print_score("Edge: wash-trading ratio", score)
    vol_liq_item = next(i for i in score.breakdown if i.criterion == "Volume/Liquidity")
    assert vol_liq_item.points < 20, "Should penalise wash trading"
    print(f"[PASS] Vol/Liq points={vol_liq_item.points} (penalised)")


def test_concentrated_liquidity() -> None:
    """One dominant pool (>95%) should score low on concentration."""
    pairs = [
        _make_pair("raydium", 980_000, 100_000, 48),
        _make_pair("orca", 20_000, 5_000, 48),
    ]
    score = calculate_score(pairs)
    _print_score("Edge: concentrated liquidity", score)
    conc_item = next(i for i in score.breakdown if i.criterion == "Liquidity Concentration")
    assert conc_item.points == 5, f"Expected 5 pts for >95%, got {conc_item.points}"
    print(f"[PASS] Concentration points={conc_item.points}")


async def main() -> None:
    print("=" * 60)
    print("Phase 2 Tests: Token Scoring Module")
    print("=" * 60)

    await test_real_data_score()

    test_single_dex_low_liq()
    test_multi_dex_healthy()
    test_wash_trading_signal()
    test_concentrated_liquidity()

    print("\n" + "=" * 60)
    print("Phase 2: ALL TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
