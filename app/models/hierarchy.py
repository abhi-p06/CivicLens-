"""
Hierarchical Geographical Administration & Operations Models for CIVILENS.
Covers Municipal Authorities, Zones, Administrative Wards,
CIVILENS Operational Sub-Wards, Localities/Beats, and Jurisdiction Audit Trail.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class GeoJSONGeometry(BaseModel):
    type: str = "Polygon"
    coordinates: List[Any]

class MunicipalAuthority(BaseModel):
    id: str
    code: str
    name: str
    short_name: Optional[str] = None
    city: str
    headquarters: Optional[str] = None
    is_active: bool = True
    boundary_geojson: Optional[Dict[str, Any]] = None

class AdminZone(BaseModel):
    id: str
    authority_id: str
    code: str
    name: str
    zonal_officer: Optional[str] = None
    is_active: bool = True
    boundary_geojson: Optional[Dict[str, Any]] = None

class AdminWard(BaseModel):
    id: str
    authority_id: str
    zone_id: Optional[str] = None
    ward_code: str
    ward_name: str
    office_address: Optional[str] = None
    lead_officer: str = "Abhinay"
    is_active: bool = True
    boundary_geojson: Optional[Dict[str, Any]] = None

class SubWard(BaseModel):
    id: str
    ward_id: str
    authority_id: str
    sub_ward_code: str
    name: str
    is_official: bool = False
    operational_type: str = "CIVILENS_OPERATIONAL_SUB_WARD"
    supervisor_name: Optional[str] = "Area Supervisor"
    supervisor_id: Optional[str] = None
    default_road_team_id: Optional[str] = None
    default_swm_team_id: Optional[str] = None
    is_active: bool = True
    boundary_geojson: Optional[Dict[str, Any]] = None

class SubWardCreate(BaseModel):
    ward_id: str
    sub_ward_code: str
    name: str
    supervisor_name: Optional[str] = "Area Supervisor"
    default_road_team_id: Optional[str] = None
    default_swm_team_id: Optional[str] = None
    is_active: bool = True
    boundary_geojson: Optional[Dict[str, Any]] = None

class SubWardUpdate(BaseModel):
    sub_ward_code: Optional[str] = None
    name: Optional[str] = None
    supervisor_name: Optional[str] = None
    default_road_team_id: Optional[str] = None
    default_swm_team_id: Optional[str] = None
    is_active: Optional[bool] = None
    boundary_geojson: Optional[Dict[str, Any]] = None

class LocalityBeat(BaseModel):
    id: str
    sub_ward_id: str
    ward_id: str
    authority_id: Optional[str] = None
    name: str
    landmark: Optional[str] = None
    latitude: float
    longitude: float
    radius_meters: float = 500.0
    is_active: bool = True

class LocalityBeatCreate(BaseModel):
    sub_ward_id: str
    name: str
    landmark: Optional[str] = None
    latitude: float
    longitude: float
    radius_meters: Optional[float] = 500.0
    is_active: bool = True

class LocalityBeatUpdate(BaseModel):
    name: Optional[str] = None
    landmark: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_meters: Optional[float] = None
    is_active: Optional[bool] = None

class HierarchyTreeNode(BaseModel):
    id: str
    label: str
    code: str
    type: str  # "authority" | "zone" | "ward" | "sub_ward" | "locality"
    parent_id: Optional[str] = None
    is_official: bool = True
    is_active: bool = True
    boundary_geojson: Optional[Dict[str, Any]] = None
    lead_officer: Optional[str] = None
    supervisor_name: Optional[str] = None
    assigned_crews_count: int = 0
    assigned_crews: List[str] = Field(default_factory=list)
    
    # Real-time Workload Metrics
    total_complaints: int = 0
    unassigned_complaints: int = 0
    assigned_complaints: int = 0
    in_progress_tasks: int = 0
    completed_complaints: int = 0
    
    children: List["HierarchyTreeNode"] = Field(default_factory=list)

class JurisdictionAuditLog(BaseModel):
    id: str
    issue_id: str
    previous_jurisdiction: Dict[str, Any]
    new_jurisdiction: Dict[str, Any]
    changed_by: str
    changed_by_role: str
    reason: str
    timestamp: str

class JurisdictionUpdatePayload(BaseModel):
    ward_code: str
    sub_ward_id: Optional[str] = None
    locality_id: Optional[str] = None
    reason: str = Field(..., min_length=4, description="Administrative reason for jurisdiction correction")

class LocationVerificationRequest(BaseModel):
    latitude: float
    longitude: float
    selected_ward: Optional[str] = None

class LocationVerificationResult(BaseModel):
    is_valid: bool
    error: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    authority_id: Optional[str] = None
    authority_code: Optional[str] = None
    authority_name: Optional[str] = None
    zone_id: Optional[str] = None
    zone_code: Optional[str] = None
    zone_name: Optional[str] = None
    ward_id: Optional[str] = None
    ward_code: Optional[str] = None
    ward_name: Optional[str] = None
    sub_ward_id: Optional[str] = None
    sub_ward_code: Optional[str] = None
    sub_ward_name: Optional[str] = None
    is_official_sub_ward: bool = False
    locality_id: Optional[str] = None
    locality_name: Optional[str] = None
    landmark: Optional[str] = None
    supervisor_name: Optional[str] = None
    is_ambiguous: bool = False
    requires_admin_review: bool = False
    review_reason: Optional[str] = None
    has_ward_mismatch: bool = False
    selected_ward: Optional[str] = None
    warning_message: Optional[str] = None
    # Frontend aliases and geographical routing path
    is_valid_jurisdiction: Optional[bool] = None
    is_mismatch: Optional[bool] = None
    derived_ward: Optional[str] = None
    mismatch_message: Optional[str] = None
    review_required: Optional[bool] = None
    geographic_path: Optional[str] = None
