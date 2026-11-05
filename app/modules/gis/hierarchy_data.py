"""
Official Municipal Administrative Hierarchy & Geographic Boundary Dataset
for CIVILENS (Mumbai — BMC and Navi Mumbai — NMMC).

Contains:
1. Municipal Authorities (BMC, NMMC) with validated spatial boundaries
2. Administrative Zones (7 BMC zones, 2 NMMC zones)
3. Administrative Wards (24 official BMC wards, 8 official NMMC ward offices)
4. CIVILENS Operational Sub-Wards (explicitly flagged is_official=False)
5. Localities / Operational Service Beats
"""
from typing import Dict, Any, List
from scripts.import_gis_boundaries import load_authorities, load_bmc_wards, NMMC_WARDS_LIST

# -----------------------------------------------------------------------------
# 1. MUNICIPAL AUTHORITIES (Validated outer boundaries)
# -----------------------------------------------------------------------------
MUNICIPAL_AUTHORITIES: List[Dict[str, Any]] = load_authorities()

# -----------------------------------------------------------------------------
# 2. ADMINISTRATIVE ZONES
# -----------------------------------------------------------------------------
ADMINISTRATIVE_ZONES: List[Dict[str, Any]] = [
    # BMC Zones (Zone I to Zone VII)
    {
        "id": "ZONE-BMC-01",
        "authority_id": "AUTH-BMC",
        "code": "ZONE-1",
        "name": "Zone I (South Mumbai / Island City South)",
        "zonal_officer": "Zonal Dy. Commissioner Zone I",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.805, 18.890], [72.850, 18.905], [72.860, 18.975],
                [72.815, 18.980], [72.805, 18.890]
            ]]
        }
    },
    {
        "id": "ZONE-BMC-02",
        "authority_id": "AUTH-BMC",
        "code": "ZONE-2",
        "name": "Zone II (Island City North & Central)",
        "zonal_officer": "Zonal Dy. Commissioner Zone II",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.825, 18.975], [72.875, 18.975], [72.880, 19.055],
                [72.835, 19.055], [72.825, 18.975]
            ]]
        }
    },
    {
        "id": "ZONE-BMC-03",
        "authority_id": "AUTH-BMC",
        "code": "ZONE-3",
        "name": "Zone III (Western Suburbs South: Bandra to Andheri East)",
        "zonal_officer": "Zonal Dy. Commissioner Zone III",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.815, 19.045], [72.885, 19.045], [72.885, 19.140],
                [72.815, 19.140], [72.815, 19.045]
            ]]
        }
    },
    {
        "id": "ZONE-BMC-04",
        "authority_id": "AUTH-BMC",
        "code": "ZONE-4",
        "name": "Zone IV (Western Suburbs Central: Andheri West to Malad)",
        "zonal_officer": "Zonal Dy. Commissioner Zone IV",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.800, 19.105], [72.855, 19.105], [72.860, 19.215],
                [72.800, 19.215], [72.800, 19.105]
            ]]
        }
    },
    {
        "id": "ZONE-BMC-05",
        "authority_id": "AUTH-BMC",
        "code": "ZONE-5",
        "name": "Zone V (Eastern Suburbs South: Kurla, Chembur, Govandi)",
        "zonal_officer": "Zonal Dy. Commissioner Zone V",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.855, 19.035], [72.955, 19.035], [72.955, 19.085],
                [72.855, 19.085], [72.855, 19.035]
            ]]
        }
    },
    {
        "id": "ZONE-BMC-06",
        "authority_id": "AUTH-BMC",
        "code": "ZONE-6",
        "name": "Zone VI (Eastern Suburbs North: Ghatkopar, Bhandup, Mulund)",
        "zonal_officer": "Zonal Dy. Commissioner Zone VI",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.885, 19.065], [72.975, 19.065], [72.975, 19.195],
                [72.885, 19.195], [72.885, 19.065]
            ]]
        }
    },
    {
        "id": "ZONE-BMC-07",
        "authority_id": "AUTH-BMC",
        "code": "ZONE-7",
        "name": "Zone VII (Western Suburbs North: Kandivali to Dahisar)",
        "zonal_officer": "Zonal Dy. Commissioner Zone VII",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.835, 19.195], [72.895, 19.195], [72.895, 19.285],
                [72.835, 19.285], [72.835, 19.195]
            ]]
        }
    },

    # NMMC Zones (Zone I and Zone II)
    {
        "id": "ZONE-NMMC-01",
        "authority_id": "AUTH-NMMC",
        "code": "NMMC-ZONE-1",
        "name": "Zone I (South Navi Mumbai: Belapur, Nerul, Vashi, Turbhe)",
        "zonal_officer": "Dy. Municipal Commissioner Zone I",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.975, 18.960], [73.090, 18.960], [73.060, 19.095],
                [72.975, 19.095], [72.975, 18.960]
            ]]
        }
    },
    {
        "id": "ZONE-NMMC-02",
        "authority_id": "AUTH-NMMC",
        "code": "NMMC-ZONE-2",
        "name": "Zone II (North Navi Mumbai: Kopar Khairane, Ghansoli, Airoli, Digha)",
        "zonal_officer": "Dy. Municipal Commissioner Zone II",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.975, 19.095], [73.060, 19.095], [73.045, 19.200],
                [72.975, 19.200], [72.975, 19.095]
            ]]
        }
    }
]

# -----------------------------------------------------------------------------
# 3. ADMINISTRATIVE WARDS (24 BMC Administrative Wards + 8 NMMC Ward Offices)
# -----------------------------------------------------------------------------
ADMINISTRATIVE_WARDS: List[Dict[str, Any]] = load_bmc_wards() + NMMC_WARDS_LIST

# -----------------------------------------------------------------------------
# 4. CIVILENS OPERATIONAL SUB-WARDS (is_official=False)
# -----------------------------------------------------------------------------
CIVILENS_OPERATIONAL_SUB_WARDS: List[Dict[str, Any]] = [
    # N-Ward Operational Sub-Wards
    {
        "id": "SUB-BMC-N-01",
        "ward_id": "WARD-BMC-N",
        "authority_id": "AUTH-BMC",
        "sub_ward_code": "N-01",
        "name": "CIVILENS Operational Sub-Ward N-01 (Vidyavihar East Beat)",
        "is_official": False,
        "operational_type": "CIVILENS_OPERATIONAL_SUB_WARD",
        "supervisor_name": "Junior Overseer M. Patil",
        "default_road_team_id": "TEAM-ROAD-01",
        "default_swm_team_id": "TEAM-SWM-01",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.890, 19.065],
                [72.915, 19.065],
                [72.915, 19.082],
                [72.890, 19.082],
                [72.890, 19.065]
            ]]
        }
    },
    {
        "id": "SUB-BMC-N-02",
        "ward_id": "WARD-BMC-N",
        "authority_id": "AUTH-BMC",
        "sub_ward_code": "N-02",
        "name": "CIVILENS Operational Sub-Ward N-02 (Ghatkopar West LBS Commercial Corridor)",
        "is_official": False,
        "operational_type": "CIVILENS_OPERATIONAL_SUB_WARD",
        "supervisor_name": "Supervisor R. Shinde",
        "default_road_team_id": "TEAM-ROAD-01",
        "default_swm_team_id": "TEAM-SWM-01",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.905, 19.082],
                [72.935, 19.082],
                [72.935, 19.108],
                [72.905, 19.108],
                [72.905, 19.082]
            ]]
        }
    },
    {
        "id": "SUB-BMC-N-03",
        "ward_id": "WARD-BMC-N",
        "authority_id": "AUTH-BMC",
        "sub_ward_code": "N-03",
        "name": "CIVILENS Operational Sub-Ward N-03 (Pant Nagar / Eastern Express Highway)",
        "is_official": False,
        "operational_type": "CIVILENS_OPERATIONAL_SUB_WARD",
        "supervisor_name": "Supervisor P. More",
        "default_road_team_id": "TEAM-ROAD-01",
        "default_swm_team_id": "TEAM-SWM-01",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.915, 19.065],
                [72.935, 19.065],
                [72.935, 19.085],
                [72.915, 19.085],
                [72.915, 19.065]
            ]]
        }
    },

    # L-Ward Operational Sub-Wards (Kurla)
    {
        "id": "SUB-BMC-L-01",
        "ward_id": "WARD-BMC-L",
        "authority_id": "AUTH-BMC",
        "sub_ward_code": "L-01",
        "name": "CIVILENS Operational Sub-Ward L-01 (Kurla West Station & Market Beat)",
        "is_official": False,
        "operational_type": "CIVILENS_OPERATIONAL_SUB_WARD",
        "supervisor_name": "Junior Overseer A. Shaikh",
        "default_road_team_id": "TEAM-ROAD-02",
        "default_swm_team_id": "TEAM-SWM-03",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.855, 19.055],
                [72.880, 19.055],
                [72.880, 19.075],
                [72.855, 19.075],
                [72.855, 19.055]
            ]]
        }
    },
    {
        "id": "SUB-BMC-L-02",
        "ward_id": "WARD-BMC-L",
        "authority_id": "AUTH-BMC",
        "sub_ward_code": "L-02",
        "name": "CIVILENS Operational Sub-Ward L-02 (Sakinaka Junction Industrial Corridor)",
        "is_official": False,
        "operational_type": "CIVILENS_OPERATIONAL_SUB_WARD",
        "supervisor_name": "Supervisor S. Khan",
        "default_road_team_id": "TEAM-ROAD-02",
        "default_swm_team_id": "TEAM-SWM-03",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.855, 19.075],
                [72.890, 19.075],
                [72.890, 19.088],
                [72.855, 19.088],
                [72.855, 19.075]
            ]]
        }
    },

    # G/North Operational Sub-Wards (Dharavi / Dadar)
    {
        "id": "SUB-BMC-GN-01",
        "ward_id": "WARD-BMC-GN",
        "authority_id": "AUTH-BMC",
        "sub_ward_code": "GN-01",
        "name": "CIVILENS Operational Sub-Ward GN-01 (Dharavi 90ft Road Corridor)",
        "is_official": False,
        "operational_type": "CIVILENS_OPERATIONAL_SUB_WARD",
        "supervisor_name": "Foreman D. Kamble",
        "default_road_team_id": "TEAM-ROAD-02",
        "default_swm_team_id": "TEAM-SWM-02",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.845, 19.035],
                [72.868, 19.035],
                [72.868, 19.055],
                [72.845, 19.055],
                [72.845, 19.035]
            ]]
        }
    },
    {
        "id": "SUB-BMC-GN-02",
        "ward_id": "WARD-BMC-GN",
        "authority_id": "AUTH-BMC",
        "sub_ward_code": "GN-02",
        "name": "CIVILENS Operational Sub-Ward GN-02 (Dadar TT & West Beat)",
        "is_official": False,
        "operational_type": "CIVILENS_OPERATIONAL_SUB_WARD",
        "supervisor_name": "Supervisor V. Salvi",
        "default_road_team_id": "TEAM-ROAD-02",
        "default_swm_team_id": "TEAM-SWM-02",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.835, 19.015],
                [72.855, 19.015],
                [72.855, 19.035],
                [72.835, 19.035],
                [72.835, 19.015]
            ]]
        }
    },

    # H/West Operational Sub-Wards (Bandra West)
    {
        "id": "SUB-BMC-HW-01",
        "ward_id": "WARD-BMC-HW",
        "authority_id": "AUTH-BMC",
        "sub_ward_code": "HW-01",
        "name": "CIVILENS Operational Sub-Ward HW-01 (Linking Road Commercial Strip)",
        "is_official": False,
        "operational_type": "CIVILENS_OPERATIONAL_SUB_WARD",
        "supervisor_name": "Supervisor N. Pinto",
        "default_road_team_id": "TEAM-ROAD-03",
        "default_swm_team_id": "TEAM-SWM-01",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.825, 19.055],
                [72.845, 19.055],
                [72.845, 19.070],
                [72.825, 19.070],
                [72.825, 19.055]
            ]]
        }
    },

    # NMMC Vashi Operational Sub-Wards
    {
        "id": "SUB-NMMC-V-01",
        "ward_id": "WARD-NMMC-VASHI",
        "authority_id": "AUTH-NMMC",
        "sub_ward_code": "V-01",
        "name": "CIVILENS Operational Sub-Ward V-01 (Sector 17 Commercial Beat)",
        "is_official": False,
        "operational_type": "CIVILENS_OPERATIONAL_SUB_WARD",
        "supervisor_name": "Supervisor S. Sawant",
        "default_road_team_id": "TEAM-ROAD-04",
        "default_swm_team_id": "TEAM-SWM-04",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.985, 19.070],
                [73.010, 19.070],
                [73.010, 19.088],
                [72.985, 19.088],
                [72.985, 19.070]
            ]]
        }
    },
    {
        "id": "SUB-NMMC-V-02",
        "ward_id": "WARD-NMMC-VASHI",
        "authority_id": "AUTH-NMMC",
        "sub_ward_code": "V-02",
        "name": "CIVILENS Operational Sub-Ward V-02 (Sector 9 & 10 Residential Beat)",
        "is_official": False,
        "operational_type": "CIVILENS_OPERATIONAL_SUB_WARD",
        "supervisor_name": "Supervisor G. Bhoir",
        "default_road_team_id": "TEAM-ROAD-04",
        "default_swm_team_id": "TEAM-SWM-04",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.980, 19.065],
                [73.000, 19.065],
                [73.000, 19.075],
                [72.980, 19.075],
                [72.980, 19.065]
            ]]
        }
    },

    # NMMC Belapur Operational Sub-Wards
    {
        "id": "SUB-NMMC-B-01",
        "ward_id": "WARD-NMMC-BELAPUR",
        "authority_id": "AUTH-NMMC",
        "sub_ward_code": "B-01",
        "name": "CIVILENS Operational Sub-Ward B-01 (CBD Belapur Administrative Beat)",
        "is_official": False,
        "operational_type": "CIVILENS_OPERATIONAL_SUB_WARD",
        "supervisor_name": "Supervisor R. Gaikwad",
        "default_road_team_id": "TEAM-ROAD-04",
        "default_swm_team_id": "TEAM-SWM-04",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [73.020, 19.005],
                [73.055, 19.005],
                [73.055, 19.025],
                [73.020, 19.025],
                [73.020, 19.005]
            ]]
        }
    },

    # NMMC Nerul Operational Sub-Wards
    {
        "id": "SUB-NMMC-NR-01",
        "ward_id": "WARD-NMMC-NERUL",
        "authority_id": "AUTH-NMMC",
        "sub_ward_code": "NR-01",
        "name": "CIVILENS Operational Sub-Ward NR-01 (Nerul West Residential Beat)",
        "is_official": False,
        "operational_type": "CIVILENS_OPERATIONAL_SUB_WARD",
        "supervisor_name": "Supervisor V. More",
        "default_road_team_id": "TEAM-ROAD-04",
        "default_swm_team_id": "TEAM-SWM-04",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [73.005, 19.020],
                [73.030, 19.020],
                [73.030, 19.045],
                [73.005, 19.045],
                [73.005, 19.020]
            ]]
        }
    },

    # NMMC Airoli Operational Sub-Wards
    {
        "id": "SUB-NMMC-A-01",
        "ward_id": "WARD-NMMC-AIROLI",
        "authority_id": "AUTH-NMMC",
        "sub_ward_code": "A-01",
        "name": "CIVILENS Operational Sub-Ward A-01 (Airoli Knowledge Park Beat)",
        "is_official": False,
        "operational_type": "CIVILENS_OPERATIONAL_SUB_WARD",
        "supervisor_name": "Supervisor H. Thakur",
        "default_road_team_id": "TEAM-ROAD-04",
        "default_swm_team_id": "TEAM-SWM-04",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.985, 19.145],
                [73.015, 19.145],
                [73.015, 19.175],
                [72.985, 19.175],
                [72.985, 19.145]
            ]]
        }
    }
]

# -----------------------------------------------------------------------------
# 5. LOCALITIES & OPERATIONAL BEATS
# -----------------------------------------------------------------------------
LOCALITY_BEATS: List[Dict[str, Any]] = [
    # N-Ward Localities
    {
        "id": "LOC-BMC-N-01-01",
        "sub_ward_id": "SUB-BMC-N-01",
        "ward_id": "WARD-BMC-N",
        "authority_id": "AUTH-BMC",
        "name": "Somaiya Vidyavihar Campus Beat",
        "landmark": "Somaiya Vidyavihar Main Gate, Vidyavihar East",
        "latitude": 19.0728,
        "longitude": 72.8998,
        "radius_meters": 600.0,
        "is_active": True
    },
    {
        "id": "LOC-BMC-N-01-02",
        "sub_ward_id": "SUB-BMC-N-01",
        "ward_id": "WARD-BMC-N",
        "name": "Vidyavihar Station East Beat",
        "landmark": "Vidyavihar Station East",
        "latitude": 19.0731,
        "longitude": 72.9002,
        "radius_meters": 400.0,
        "is_active": True
    },
    {
        "id": "LOC-BMC-N-02-01",
        "sub_ward_id": "SUB-BMC-N-02",
        "ward_id": "WARD-BMC-N",
        "name": "LBS Marg Ghatkopar West Beat",
        "landmark": "LBS Marg, Ghatkopar West",
        "latitude": 19.0911,
        "longitude": 72.9154,
        "radius_meters": 800.0,
        "is_active": True
    },
    {
        "id": "LOC-BMC-N-02-02",
        "sub_ward_id": "SUB-BMC-N-02",
        "ward_id": "WARD-BMC-N",
        "name": "R-City Mall Service Beat",
        "landmark": "R-City Mall, Ghatkopar West",
        "latitude": 19.0990,
        "longitude": 72.9164,
        "radius_meters": 500.0,
        "is_active": True
    },
    {
        "id": "LOC-BMC-N-03-01",
        "sub_ward_id": "SUB-BMC-N-03",
        "ward_id": "WARD-BMC-N",
        "name": "Pant Nagar Eastern Express Beat",
        "landmark": "Eastern Express Highway, Ghatkopar East",
        "latitude": 19.0850,
        "longitude": 72.9150,
        "radius_meters": 700.0,
        "is_active": True
    },

    # L-Ward Localities
    {
        "id": "LOC-BMC-L-01-01",
        "sub_ward_id": "SUB-BMC-L-01",
        "ward_id": "WARD-BMC-L",
        "authority_id": "AUTH-BMC",
        "name": "Kurla West Station Road Beat",
        "landmark": "Kurla West Station Road",
        "latitude": 19.0655,
        "longitude": 72.8710,
        "radius_meters": 500.0,
        "is_active": True
    },
    {
        "id": "LOC-BMC-L-01-02",
        "sub_ward_id": "SUB-BMC-L-01",
        "ward_id": "WARD-BMC-L",
        "authority_id": "AUTH-BMC",
        "name": "Sion-Bandra Link Road Beat",
        "landmark": "Sion-Bandra Link Road, Kurla West",
        "latitude": 19.0655,
        "longitude": 72.8710,
        "radius_meters": 600.0,
        "is_active": True
    },

    # G/North Ward Localities
    {
        "id": "LOC-BMC-GN-01-01",
        "sub_ward_id": "SUB-BMC-GN-01",
        "ward_id": "WARD-BMC-GN",
        "authority_id": "AUTH-BMC",
        "name": "Dharavi 90 Feet Road Beat",
        "landmark": "90 Feet Road, Dharavi",
        "latitude": 19.0435,
        "longitude": 72.8562,
        "radius_meters": 600.0,
        "is_active": True
    },
    {
        "id": "LOC-BMC-GN-02-01",
        "sub_ward_id": "SUB-BMC-GN-02",
        "ward_id": "WARD-BMC-GN",
        "authority_id": "AUTH-BMC",
        "name": "Dadar TT Circle Beat",
        "landmark": "Dadar TT Circle",
        "latitude": 19.0178,
        "longitude": 72.8478,
        "radius_meters": 500.0,
        "is_active": True
    },

    # H/West Ward Localities
    {
        "id": "LOC-BMC-HW-01-01",
        "sub_ward_id": "SUB-BMC-HW-01",
        "ward_id": "WARD-BMC-HW",
        "authority_id": "AUTH-BMC",
        "name": "Linking Road Bandra West Beat",
        "landmark": "Linking Road, Bandra West",
        "latitude": 19.0601,
        "longitude": 72.8361,
        "radius_meters": 600.0,
        "is_active": True
    },

    # NMMC Localities
    {
        "id": "LOC-NMMC-V-01-01",
        "sub_ward_id": "SUB-NMMC-V-01",
        "ward_id": "WARD-NMMC-VASHI",
        "authority_id": "AUTH-NMMC",
        "name": "Vashi Sector 17 Commercial Beat",
        "landmark": "Sector 17, Vashi, Navi Mumbai",
        "latitude": 19.0771,
        "longitude": 72.9986,
        "radius_meters": 600.0,
        "is_active": True
    },
    {
        "id": "LOC-NMMC-B-01-01",
        "sub_ward_id": "SUB-NMMC-B-01",
        "ward_id": "WARD-NMMC-BELAPUR",
        "authority_id": "AUTH-NMMC",
        "name": "CBD Belapur Station Beat",
        "landmark": "CBD Belapur, Navi Mumbai",
        "latitude": 19.0144,
        "longitude": 73.0380,
        "radius_meters": 600.0,
        "is_active": True
    },
    {
        "id": "LOC-NMMC-NR-01-01",
        "sub_ward_id": "SUB-NMMC-NR-01",
        "ward_id": "WARD-NMMC-NERUL",
        "authority_id": "AUTH-NMMC",
        "name": "Nerul West Station Beat",
        "landmark": "Nerul West, Navi Mumbai",
        "latitude": 19.0330,
        "longitude": 73.0197,
        "radius_meters": 600.0,
        "is_active": True
    },
    {
        "id": "LOC-NMMC-A-01-01",
        "sub_ward_id": "SUB-NMMC-A-01",
        "ward_id": "WARD-NMMC-AIROLI",
        "authority_id": "AUTH-NMMC",
        "name": "Airoli Knowledge Park Beat",
        "landmark": "Airoli Knowledge Park, Navi Mumbai",
        "latitude": 19.1579,
        "longitude": 72.9935,
        "radius_meters": 600.0,
        "is_active": True
    }
]
