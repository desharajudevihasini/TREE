"""Shared GreenTwin property / scenario contracts. GBP and annual kWh throughout."""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field


class Property(BaseModel):
    property_id: str
    name: str
    region: str = "Unknown"
    property_type: Literal["detached", "semi_detached", "terraced", "flat", "bungalow"] = "terraced"
    floor_area_m2: float = Field(gt=0)
    construction_age_band: str = "unknown"
    epc_rating: Literal["A", "B", "C", "D", "E", "F", "G"] | None = None
    heating_type: Literal["gas_boiler", "heat_pump", "electric_resistance", "district"] | None = None
    loft_insulated: bool | None = None
    wall_insulated: bool | None = None
    glazing: Literal["single", "double", "triple"] | None = None
    solar_kwp: float = Field(default=0.0, ge=0)
    smart_controls: bool | None = None
    roof_suitable: bool | None = None
    outdoor_space: bool | None = None
    annual_electricity_kwh: float | None = Field(default=None, ge=0)
    annual_gas_kwh: float | None = Field(default=None, ge=0)
    baseline_source: str = "synthetic_demo"
    property_value_gbp: float | None = Field(default=None, ge=0)
    electricity_price_gbp_kwh: float = Field(default=0.28, ge=0)
    gas_price_gbp_kwh: float = Field(default=0.07, ge=0)
    budget_gbp: float = Field(default=5000, ge=0)


class ReportRequest(BaseModel):
    property: Property
    budget_gbp: float | None = Field(default=None, ge=0)
    objective: Literal['money','energy','carbon'] = 'money'


class ScenarioRequest(BaseModel):
    property: Property
    measures: list[str] = Field(default_factory=list)
    electricity_price_gbp_kwh: float | None = Field(default=None, ge=0)
    gas_price_gbp_kwh: float | None = Field(default=None, ge=0)


class OptimizeRequest(BaseModel):
    property: Property
    budget_gbp: float = Field(default=5000, ge=0)
    objective: Literal["money", "carbon", "energy"] = "money"


class QuestionRequest(OptimizeRequest):
    asked: list[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    session_id: str | None = None
    property_id: str = "manchester"
    message: str = Field(min_length=1, max_length=3000)
    property: Property | None = None  # Optional custom home, supplied only when starting a new chat
    use_gemini: bool = False


class PropertyUpdate(BaseModel):
    changes: dict[str, object]
    source: Literal["homeowner_confirmed", "self_reported"] = "homeowner_confirmed"


class RankRequest(BaseModel):
    properties: list[Property]
