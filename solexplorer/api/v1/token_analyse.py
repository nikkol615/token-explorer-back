"""Endpoint for fetching and scoring a Solana token."""

from fastapi import APIRouter

from solexplorer.analyse.get_score import calculate_score
from solexplorer.schemas.score import TokenAnalysisResponse
from solexplorer.solana.get_token import get_token_overview

router = APIRouter()


@router.get(
    "/token/{token_address}",
    response_model=TokenAnalysisResponse,
    summary="Analyse a Solana token",
    tags=["Token Analysis"],
)
async def analyse_token(token_address: str) -> TokenAnalysisResponse:
    """Validate the address, fetch DEX data, score the token and return the full analysis.

    Args:
        token_address: Solana mint address of the token.

    Returns:
        Combined overview and scoring breakdown.
    """
    overview = await get_token_overview(token_address)
    score = calculate_score(overview.pairs)
    return TokenAnalysisResponse(overview=overview, score=score)
