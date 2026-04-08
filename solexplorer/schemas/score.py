from __future__ import annotations

from pydantic import BaseModel

from solexplorer.schemas.token import TokenOverview


class ScoreBreakdownItem(BaseModel):
    """One line in the scoring breakdown table."""

    criterion: str
    points: int
    max_points: int
    reason: str


class TokenScore(BaseModel):
    """Aggregated scoring result for a token."""

    total_score: int
    status_emoji: str
    breakdown: list[ScoreBreakdownItem]


class TokenAnalysisResponse(BaseModel):
    """Full API response combining token overview with its score."""

    overview: TokenOverview
    score: TokenScore
