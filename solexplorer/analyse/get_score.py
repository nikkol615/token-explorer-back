"""Token scoring engine (0-100 points).

Criteria and weights are defined in AGENTS.md.
"""

from __future__ import annotations

import time

from solexplorer.schemas.score import ScoreBreakdownItem, TokenScore
from solexplorer.schemas.token import DexPair

_MS_IN_HOUR = 3_600_000


def _score_dex_count(pairs: list[DexPair]) -> ScoreBreakdownItem:
    """Max 20 pts: 1 DEX -> 10, >=2 DEXes -> 20."""
    unique_dexes = {p.dexId for p in pairs}
    count = len(unique_dexes)

    if count >= 2:
        points = 20
    elif count == 1:
        points = 10
    else:
        points = 0

    return ScoreBreakdownItem(
        criterion="DEX Count",
        points=points,
        max_points=20,
        reason=f"Trading on {count} DEX(es): {', '.join(sorted(unique_dexes)) or 'none'}",
    )


def _score_total_liquidity(pairs: list[DexPair]) -> ScoreBreakdownItem:
    """Max 30 pts based on total USD liquidity across all Solana pools."""
    total = sum(p.liquidity.usd for p in pairs)

    if total > 200_000:
        points = 30
    elif total > 50_000:
        points = 20
    elif total > 10_000:
        points = 10
    else:
        points = 0

    return ScoreBreakdownItem(
        criterion="Liquidity",
        points=points,
        max_points=30,
        reason=f"Total liquidity ${total:,.0f}",
    )


def _score_volume_liquidity_ratio(pairs: list[DexPair]) -> ScoreBreakdownItem:
    """Max 20 pts: healthy ratio (0.1-5.0) scores full marks."""
    total_vol = sum(p.volume.h24 for p in pairs)
    total_liq = sum(p.liquidity.usd for p in pairs)

    if total_liq == 0:
        return ScoreBreakdownItem(
            criterion="Volume/Liquidity",
            points=0,
            max_points=20,
            reason="No liquidity — ratio undefined",
        )

    ratio = total_vol / total_liq

    if 0.1 <= ratio <= 5.0:
        points = 20
    elif ratio < 0.1:
        points = 5
        reason_hint = "very low (possibly dead)"
    elif ratio > 5.0:
        points = 5
        reason_hint = "very high (possible wash trading)"
    else:
        points = 0
        reason_hint = "extreme"

    reason = f"Vol/Liq ratio {ratio:.2f}"
    if points < 20:
        reason += f" — {reason_hint}"

    return ScoreBreakdownItem(
        criterion="Volume/Liquidity",
        points=points,
        max_points=20,
        reason=reason,
    )


def _score_liquidity_concentration(pairs: list[DexPair]) -> ScoreBreakdownItem:
    """Max 20 pts: penalise if >95% of liquidity sits in one pool."""
    total_liq = sum(p.liquidity.usd for p in pairs)

    if total_liq == 0:
        return ScoreBreakdownItem(
            criterion="Liquidity Concentration",
            points=0,
            max_points=20,
            reason="No liquidity",
        )

    top_pool_liq = max(p.liquidity.usd for p in pairs)
    top_share = top_pool_liq / total_liq

    if top_share < 0.80:
        points = 20
    elif top_share < 0.95:
        points = 10
    else:
        points = 5

    return ScoreBreakdownItem(
        criterion="Liquidity Concentration",
        points=points,
        max_points=20,
        reason=f"Top pool holds {top_share:.0%} of total liquidity",
    )


def _score_pool_age(pairs: list[DexPair]) -> ScoreBreakdownItem:
    """Max 10 pts based on the oldest pool's age."""
    now_ms = int(time.time() * 1000)
    created_times = [p.pairCreatedAt for p in pairs if p.pairCreatedAt > 0]

    if not created_times:
        return ScoreBreakdownItem(
            criterion="Pool Age",
            points=0,
            max_points=10,
            reason="No creation timestamp available",
        )

    oldest_ms = min(created_times)
    age_hours = (now_ms - oldest_ms) / _MS_IN_HOUR

    if age_hours > 24:
        points = 10
    elif age_hours >= 1:
        points = 5
    else:
        points = 0

    return ScoreBreakdownItem(
        criterion="Pool Age",
        points=points,
        max_points=10,
        reason=f"Oldest pool created {age_hours:,.0f}h ago",
    )


def calculate_score(pairs: list[DexPair]) -> TokenScore:
    """Run all scoring criteria and return the final TokenScore.

    Args:
        pairs: Solana-only DexPair objects for the token.

    Returns:
        TokenScore with total score, emoji, and per-criterion breakdown.
    """
    breakdown = [
        _score_dex_count(pairs),
        _score_total_liquidity(pairs),
        _score_volume_liquidity_ratio(pairs),
        _score_liquidity_concentration(pairs),
        _score_pool_age(pairs),
    ]

    total = sum(item.points for item in breakdown)

    if total > 70:
        emoji = "\U0001f7e2"   # green circle
    elif total >= 40:
        emoji = "\U0001f7e1"   # yellow circle
    else:
        emoji = "\U0001f534"   # red circle

    return TokenScore(
        total_score=total,
        status_emoji=emoji,
        breakdown=breakdown,
    )
