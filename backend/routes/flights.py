import logging

from fastapi import APIRouter, HTTPException

from services.flights import FlightService

logger = logging.getLogger(__name__)

flights_router = APIRouter()
_flight_service = FlightService()


@flights_router.get("/flights")
async def list_flights():
    try:
        return await _flight_service.list_flights_response()
    except Exception:
        logger.exception("Failed to list flights")
        return []


@flights_router.get("/flights/{flight_id}")
async def get_flight(flight_id: int):
    try:
        result = await _flight_service.get_flight_response(flight_id)
        if not result:
            raise HTTPException(
                status_code=404, detail=f"Flight {flight_id} not found."
            )
        return result
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to get flight %d", flight_id)
        raise HTTPException(status_code=500, detail="An internal error occurred.")
