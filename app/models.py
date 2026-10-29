from pydantic import BaseModel, ConfigDict, Field


class MeterSummary(BaseModel):
    """Fields observed in the portal's meter-list UI."""

    model_config = ConfigDict(extra="allow")

    meter_id: str = Field(validation_alias="meterId")
    serial_no: str | None = Field(default=None, validation_alias="serialNo")
    make: str | None = None
    phase_type: str | None = Field(default=None, validation_alias="phaseType")
    install_status: str | None = Field(default=None, validation_alias="installStatus")
    dt_code: str | None = Field(default=None, validation_alias="dtCode")


class MeterPage(BaseModel):
    data: list[MeterSummary]
    total: int
    page: int
    page_size: int = 20


class GeoCoordinates(BaseModel):
    latitude: float
    longitude: float


class EnergyReading(BaseModel):
    timestamp: str
    kwh: float
    kvah: float
    volt_r: float = Field(validation_alias="voltR")


class EnergyReadings(BaseModel):
    data: list[EnergyReading]


class HierarchyNode(BaseModel):
    name: str
    code: str


class MeterHierarchy(BaseModel):
    zone: HierarchyNode
    circle: HierarchyNode
    division: HierarchyNode
    subdivision: HierarchyNode
    substation: HierarchyNode
    feeder: HierarchyNode
    dt: HierarchyNode


class MeterRecord(MeterSummary):
    install_type: str = Field(validation_alias="installType")
    build: str
    hierarchy: MeterHierarchy
    geo: dict[str, float]


class MeterExport(BaseModel):
    data: list[MeterRecord]
    total: int

