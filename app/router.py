from typing import Any

from fastapi import APIRouter, Depends, Request

from app.auth import require_api_key
from app.endpoint_params import ENDPOINT_PARAMETERS, openapi_parameters
from app.service import FootballDataService, get_football_service

router = APIRouter(tags=["API-Football"], dependencies=[Depends(require_api_key)])

ENDPOINTS = list(ENDPOINT_PARAMETERS.keys())


def _query_params(request: Request) -> dict[str, Any]:
    return dict(request.query_params)


async def _proxy(
    endpoint: str,
    request: Request,
    service: FootballDataService,
) -> dict[str, Any]:
    return await service.get(endpoint, _query_params(request))


def _register_endpoint(path: str) -> None:
    params = openapi_parameters(path)
    required = [p["name"] for p in params if p.get("required")]
    summary = f"GET /{path}"
    if required:
        summary += f" — required: {', '.join(required)}"

    async def handler(
        request: Request,
        service: FootballDataService = Depends(get_football_service),
    ) -> dict[str, Any]:
        return await _proxy(path, request, service)

    handler.__name__ = path.replace("/", "_")

    route_kwargs: dict[str, Any] = {
        "methods": ["GET"],
        "name": handler.__name__,
        "summary": summary,
    }
    if params:
        route_kwargs["openapi_extra"] = {"parameters": params}

    router.add_api_route(f"/{path}", handler, **route_kwargs)


for endpoint in ENDPOINTS:
    _register_endpoint(endpoint)
