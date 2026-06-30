"""Query parameter definitions matching api-football.com documentation v3."""

from typing import Any

ParamSpec = dict[str, Any]


def _param(
    name: str,
    *,
    type_: str = "string",
    required: bool = False,
    description: str = "",
    example: Any = None,
) -> ParamSpec:
    schema: dict[str, Any] = {"type": type_}
    if example is not None:
        schema["example"] = example

    spec: ParamSpec = {
        "name": name,
        "in": "query",
        "required": required,
        "schema": schema,
    }
    if description:
        spec["description"] = description
    return spec


def _int(name: str, **kwargs: Any) -> ParamSpec:
    return _param(name, type_="integer", **kwargs)


def _str(name: str, **kwargs: Any) -> ParamSpec:
    return _param(name, type_="string", **kwargs)


def _page() -> ParamSpec:
    return _int("page", description="Pagination page number", example=1)


ENDPOINT_PARAMETERS: dict[str, list[ParamSpec]] = {
    "timezone": [],
    "status": [],
    "countries": [
        _str("name", description="Country name"),
        _str("code", description="Country code (2-6 chars)", example="GB-ENG"),
        _str("search", description="Search by country name (min 3 chars)"),
    ],
    "leagues": [
        _int("id", description="League ID", example=39),
        _str("name", description="League name"),
        _str("country", description="Country name", example="England"),
        _str("code", description="Country code"),
        _int("season", description="Season year", example=2025),
        _int("team", description="Team ID"),
        _str("type", description="League type: league or cup"),
        _str("current", description="Only current seasons: true or false", example="true"),
        _str("search", description="Search league or country (min 3 chars)"),
        _int("last", description="Recently added leagues (max 2 digits)"),
    ],
    "leagues/seasons": [],
    "seasons": [],
    "teams": [
        _int("id", description="Team ID", example=33),
        _str("name", description="Team name"),
        _int("league", description="League ID", example=39),
        _int("season", description="Season year", example=2025),
        _str("country", description="Country name"),
        _str("code", description="Country code"),
        _int("venue", description="Venue ID"),
        _str("search", description="Search by team name (min 3 chars)"),
    ],
    "teams/statistics": [
        _int("league", required=True, description="League ID", example=39),
        _int("season", required=True, description="Season year", example=2025),
        _int("team", required=True, description="Team ID", example=33),
        _str("date", description="Stats up to date (YYYY-MM-DD)"),
    ],
    "venues": [
        _int("id", description="Venue ID"),
        _str("name", description="Venue name"),
        _str("city", description="City name"),
        _str("country", description="Country name"),
        _str("search", description="Search venue name (min 3 chars)"),
    ],
    "fixtures": [
        _int("id", description="Fixture ID"),
        _str("ids", description="Up to 20 fixture IDs separated by -"),
        _str("live", description="Live fixtures: all or league IDs (e.g. 39-140)", example="all"),
        _str("date", description="Fixtures on date (YYYY-MM-DD)"),
        _int("league", description="League ID", example=39),
        _int("season", description="Season year", example=2025),
        _int("team", description="Team ID"),
        _int("last", description="Last N fixtures (max 2 digits)"),
        _int("next", description="Next N fixtures (max 2 digits)"),
        _str("from", description="Start date (YYYY-MM-DD)"),
        _str("to", description="End date (YYYY-MM-DD)"),
        _str("round", description="Round name from /fixtures/rounds"),
        _str("status", description="Status codes (e.g. NS, FT, 1H-HT-2H)"),
        _int("venue", description="Venue ID"),
        _str("timezone", description="Timezone from /timezone", example="Europe/London"),
    ],
    "fixtures/rounds": [
        _int("league", required=True, description="League ID", example=39),
        _int("season", required=True, description="Season year", example=2025),
        _str("current", description="Only current round: true or false"),
    ],
    "fixtures/headtohead": [
        _str("h2h", required=True, description="Two team IDs separated by -", example="33-34"),
        _str("date", description="Fixtures on date (YYYY-MM-DD)"),
        _int("league", description="League ID"),
        _int("season", description="Season year"),
        _int("last", description="Last N fixtures"),
        _int("next", description="Next N fixtures"),
        _str("from", description="Start date (YYYY-MM-DD)"),
        _str("to", description="End date (YYYY-MM-DD)"),
        _str("timezone", description="Timezone from /timezone"),
    ],
    "fixtures/statistics": [
        _int("fixture", required=True, description="Fixture ID"),
        _int("team", description="Team ID"),
        _str("type", description="Statistic type filter"),
    ],
    "fixtures/events": [
        _int("fixture", required=True, description="Fixture ID"),
        _int("team", description="Team ID"),
        _int("player", description="Player ID"),
        _str("type", description="Event type: Goal, Card, subst"),
    ],
    "fixtures/lineups": [
        _int("fixture", required=True, description="Fixture ID"),
        _int("team", description="Team ID"),
        _str("type", description="Lineup type, e.g. Starting XI"),
    ],
    "fixtures/players": [
        _int("fixture", required=True, description="Fixture ID"),
        _int("team", description="Team ID"),
    ],
    "standings": [
        _int("league", description="League ID", example=39),
        _int("season", required=True, description="Season year", example=2025),
        _int("team", description="Team ID"),
    ],
    "players": [
        _int("id", description="Player ID"),
        _int("team", description="Team ID"),
        _int("league", description="League ID", example=39),
        _int("season", description="Season year", example=2025),
        _str("search", description="Search player name (min 3 chars)"),
        _page(),
    ],
    "players/squads": [
        _int("team", required=True, description="Team ID", example=33),
    ],
    "players/teams": [
        _int("player", required=True, description="Player ID"),
    ],
    "players/topscorers": [
        _int("league", required=True, description="League ID", example=39),
        _int("season", required=True, description="Season year", example=2025),
    ],
    "players/topassists": [
        _int("league", required=True, description="League ID", example=39),
        _int("season", required=True, description="Season year", example=2025),
    ],
    "players/topyellowcards": [
        _int("league", required=True, description="League ID", example=39),
        _int("season", required=True, description="Season year", example=2025),
    ],
    "players/topredcards": [
        _int("league", required=True, description="League ID", example=39),
        _int("season", required=True, description="Season year", example=2025),
    ],
    "coachs": [
        _int("id", description="Coach ID"),
        _int("team", description="Team ID"),
        _str("search", description="Search coach name (min 3 chars)"),
    ],
    "transfers": [
        _int("player", description="Player ID"),
        _int("team", description="Team ID"),
    ],
    "trophies": [
        _int("player", description="Player ID"),
        _int("coach", description="Coach ID"),
    ],
    "injuries": [
        _int("league", description="League ID"),
        _int("season", description="Season year"),
        _int("fixture", description="Fixture ID"),
        _int("team", description="Team ID"),
        _int("player", description="Player ID"),
        _str("date", description="Date (YYYY-MM-DD)"),
        _str("timezone", description="Timezone from /timezone"),
        _str("ids", description="Fixture IDs separated by -"),
    ],
    "sidelined": [
        _int("player", description="Player ID"),
        _int("coach", description="Coach ID"),
    ],
    "predictions": [
        _int("fixture", required=True, description="Fixture ID"),
    ],
    "odds": [
        _int("fixture", description="Fixture ID"),
        _int("league", description="League ID"),
        _int("season", description="Season year"),
        _str("date", description="Date (YYYY-MM-DD)"),
        _int("bookmaker", description="Bookmaker ID from /odds/bookmakers"),
        _int("bet", description="Bet type ID from /odds/bets"),
        _page(),
        _str("timezone", description="Timezone from /timezone"),
    ],
    "odds/live": [
        _int("fixture", description="Fixture ID"),
        _int("league", description="League ID"),
        _int("bet", description="Live bet type ID from /odds/live/bets"),
    ],
    "odds/bookmakers": [
        _int("id", description="Bookmaker ID"),
        _str("search", description="Search bookmaker name"),
    ],
    "odds/bets": [
        _int("id", description="Bet type ID"),
        _str("search", description="Search bet name"),
    ],
    "odds/live/bets": [
        _int("id", description="Live bet type ID"),
        _str("search", description="Search bet name"),
    ],
}


def openapi_parameters(endpoint: str) -> list[ParamSpec]:
    return ENDPOINT_PARAMETERS.get(endpoint, [])
