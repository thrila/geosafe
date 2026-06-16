from fastapi import APIRouter, Request
from scalar_fastapi import get_scalar_api_reference
from core.config import settings

docs_route = APIRouter()

@docs_route.get("/docs", include_in_schema=False)
async def scalar_docs(request: Request):  
        return get_scalar_api_reference(
        openapi_url=request.app.openapi_url,  
        title=settings.TITLE,
        scalar_proxy_url="https://proxy.scalar.com",
    )
