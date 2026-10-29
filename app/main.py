from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Request

from .client import PortalError, UrjaPortalClient
from .config import get_settings
from .models import EnergyReadings, GeoCoordinates, MeterExport, MeterPage


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.portal = UrjaPortalClient(settings)
    yield
    await app.state.portal.close()


app = FastAPI(
    title="Flock Meter API",
    version="0.1.0",
    description="A read-only, documented facade over Urja Meter Ops.",
    lifespan=lifespan,
)


def portal(request: Request) -> UrjaPortalClient:
    return request.app.state.portal


Portal = Annotated[UrjaPortalClient, Depends(portal)]


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/meters", response_model=MeterPage)
async def list_meters(
    client: Portal,
    q: Annotated[str, Query(max_length=200)] = "",
    page: Annotated[int, Query(ge=1)] = 1,
) -> MeterPage:
    try:
        upstream = await client.search_meters(q, page)
        return MeterPage.model_validate({**upstream, "page": page})
    except PortalError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@app.get("/v1/meters/{meter_id}/geo", response_model=GeoCoordinates)
async def meter_geo(meter_id: str, client: Portal) -> GeoCoordinates:
    try:
        return GeoCoordinates.model_validate((await client.meter_geo(meter_id))["data"])
    except PortalError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@app.get("/v1/meters/{meter_id}/energy", response_model=EnergyReadings)
async def meter_energy(meter_id: str, client: Portal) -> EnergyReadings:
    try:
        return EnergyReadings.model_validate(await client.meter_energy(meter_id, {}))
    except PortalError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@app.get("/v1/meters/export", response_model=MeterExport)
async def export_meters(client: Portal) -> MeterExport:
    try:
        return MeterExport.model_validate(await client.export_meters())
    except PortalError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

