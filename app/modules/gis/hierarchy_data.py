"""
Official Municipal Administrative Hierarchy & Geographic Boundary Dataset
for CIVILENS (Mumbai — BMC and Navi Mumbai — NMMC).

Contains:
1. Municipal Authorities (BMC, NMMC)
2. Administrative Zones
3. Administrative Wards (24 official BMC wards, 8 official NMMC wards)
4. CIVILENS Operational Sub-Wards (explicitly flagged as non-official operational units)
5. Localities / Operational Service Beats
"""
from typing import Dict, Any, List

# -----------------------------------------------------------------------------
# 1. MUNICIPAL AUTHORITIES
# -----------------------------------------------------------------------------
MUNICIPAL_AUTHORITIES: List[Dict[str, Any]] = [
    {
        "id": "AUTH-BMC",
        "code": "BMC",
        "name": "Brihanmumbai Municipal Corporation",
        "short_name": "BMC (MCGM)",
        "city": "Mumbai",
        "headquarters": "Mahapalika Marg, Fort, Mumbai 400001",
        "is_active": True,
        # Outer bounding polygon for Mumbai (Island City + Suburbs)
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.810, 18.890],
                [72.845, 18.905],
                [72.860, 18.960],
                [72.880, 19.010],
                [72.920, 19.040],
                [72.955, 19.070],
                [72.975, 19.120],
                [72.970, 19.190],
                [72.945, 19.260],
                [72.880, 19.285],
                [72.835, 19.255],
                [72.805, 19.170],
                [72.800, 19.100],
                [72.810, 19.030],
                [72.800, 18.950],
                [72.810, 18.890]
            ]]
        }
    },
    {
        "id": "AUTH-NMMC",
        "code": "NMMC",
        "name": "Navi Mumbai Municipal Corporation",
        "short_name": "NMMC",
        "city": "Navi Mumbai",
        "headquarters": "NMMC Headquarters, Plot No. 1, Sector 15A, CBD Belapur, Navi Mumbai 400614",
        "is_active": True,
        # Bounding polygon for Navi Mumbai Municipal jurisdiction
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.975, 19.200],
                [73.020, 19.200],
                [73.035, 19.150],
                [73.045, 19.100],
                [73.055, 19.050],
                [73.065, 19.000],
                [73.090, 18.970],
                [73.075, 18.960],
                [73.020, 18.995],
                [72.990, 19.040],
                [72.975, 19.100],
                [72.975, 19.200]
            ]]
        }
    }
]

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
# 3. ADMINISTRATIVE WARDS
# -----------------------------------------------------------------------------
ADMINISTRATIVE_WARDS: List[Dict[str, Any]] = [
    # BMC Eastern Suburbs
    {
        "id": "WARD-BMC-N",
        "authority_id": "AUTH-BMC",
        "zone_id": "ZONE-BMC-06",
        "ward_code": "N-Ward",
        "ward_name": "N-Ward (Vidyavihar / Ghatkopar)",
        "office_address": "N Ward Municipal Office, Jawahar Road, Ghatkopar East, Mumbai 400077",
        "lead_officer": "Abhinay",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.890, 19.065],
                [72.935, 19.065],
                [72.935, 19.108],
                [72.890, 19.108],
                [72.890, 19.065]
            ]]
        }
    },
    {
        "id": "WARD-BMC-L",
        "authority_id": "AUTH-BMC",
        "zone_id": "ZONE-BMC-05",
        "ward_code": "L-Ward",
        "ward_name": "L-Ward (Kurla / Sakinaka)",
        "office_address": "L Ward Office, LBS Marg, Kurla West, Mumbai 400070",
        "lead_officer": "Abhinay",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.855, 19.055],
                [72.890, 19.055],
                [72.890, 19.088],
                [72.855, 19.088],
                [72.855, 19.055]
            ]]
        }
    },
    {
        "id": "WARD-BMC-GN",
        "authority_id": "AUTH-BMC",
        "zone_id": "ZONE-BMC-02",
        "ward_code": "G/North",
        "ward_name": "G/North (Dharavi / Dadar / Mahim)",
        "office_address": "G/North Ward Office, Harishchandra Yelve Marg, Dadar West, Mumbai 400028",
        "lead_officer": "Abhinay",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.835, 19.015],
                [72.868, 19.015],
                [72.868, 19.055],
                [72.835, 19.055],
                [72.835, 19.015]
            ]]
        }
    },
    {
        "id": "WARD-BMC-HW",
        "authority_id": "AUTH-BMC",
        "zone_id": "ZONE-BMC-03",
        "ward_code": "H/West",
        "ward_name": "H/West (Bandra West / Khar)",
        "office_address": "H/West Ward Office, Saint Martin Road, Bandra West, Mumbai 400050",
        "lead_officer": "Abhinay",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.815, 19.045],
                [72.845, 19.045],
                [72.845, 19.080],
                [72.815, 19.080],
                [72.815, 19.045]
            ]]
        }
    },
    {
        "id": "WARD-BMC-KE",
        "authority_id": "AUTH-BMC",
        "zone_id": "ZONE-BMC-03",
        "ward_code": "K/East",
        "ward_name": "K/East (Andheri East / Jogeshwari East)",
        "office_address": "K/East Ward Office, Azad Road, Gundavali, Andheri East, Mumbai 400069",
        "lead_officer": "Abhinay",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.840, 19.100],
                [72.885, 19.100],
                [72.885, 19.145],
                [72.840, 19.145],
                [72.840, 19.100]
            ]]
        }
    },
    {
        "id": "WARD-BMC-KW",
        "authority_id": "AUTH-BMC",
        "zone_id": "ZONE-BMC-04",
        "ward_code": "K/West",
        "ward_name": "K/West (Andheri West / Versova)",
        "office_address": "K/West Ward Office, Paliram Road, Andheri West, Mumbai 400058",
        "lead_officer": "Abhinay",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.805, 19.105],
                [72.845, 19.105],
                [72.845, 19.155],
                [72.805, 19.155],
                [72.805, 19.105]
            ]]
        }
    },
    {
        "id": "WARD-BMC-S",
        "authority_id": "AUTH-BMC",
        "zone_id": "ZONE-BMC-06",
        "ward_code": "S-Ward",
        "ward_name": "S-Ward (Powai / Bhandup)",
        "office_address": "S Ward Office, Lal Bahadur Shastri Marg, Bhandup West, Mumbai 400078",
        "lead_officer": "Abhinay",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.885, 19.108],
                [72.945, 19.108],
                [72.945, 19.165],
                [72.885, 19.165],
                [72.885, 19.108]
            ]]
        }
    },
    {
        "id": "WARD-BMC-MW",
        "authority_id": "AUTH-BMC",
        "zone_id": "ZONE-BMC-05",
        "ward_code": "M/West",
        "ward_name": "M/West (Chembur)",
        "office_address": "M/West Ward Office, Sharadbhau Acharya Marg, Chembur, Mumbai 400071",
        "lead_officer": "Abhinay",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.885, 19.040],
                [72.918, 19.040],
                [72.918, 19.075],
                [72.885, 19.075],
                [72.885, 19.040]
            ]]
        }
    },
    {
        "id": "WARD-BMC-ME",
        "authority_id": "AUTH-BMC",
        "zone_id": "ZONE-BMC-05",
        "ward_code": "M/East",
        "ward_name": "M/East (Govandi / Mankhurd)",
        "office_address": "M/East Ward Office, Deonar Colony, Govandi, Mumbai 400043",
        "lead_officer": "Abhinay",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.918, 19.035],
                [72.955, 19.035],
                [72.955, 19.075],
                [72.918, 19.075],
                [72.918, 19.035]
            ]]
        }
    },
    {
        "id": "WARD-BMC-RC",
        "authority_id": "AUTH-BMC",
        "zone_id": "ZONE-BMC-07",
        "ward_code": "R/Central",
        "ward_name": "R/Central (Borivali)",
        "office_address": "R/Central Ward Office, Chandavarkar Road, Borivali West, Mumbai 400092",
        "lead_officer": "Abhinay",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.835, 19.215],
                [72.875, 19.215],
                [72.875, 19.250],
                [72.835, 19.250],
                [72.835, 19.215]
            ]]
        }
    },
    {
        "id": "WARD-BMC-E",
        "authority_id": "AUTH-BMC",
        "zone_id": "ZONE-BMC-01",
        "ward_code": "E-Ward",
        "ward_name": "E-Ward (Byculla)",
        "office_address": "E Ward Office, Ramchandra Bhatt Marg, Byculla, Mumbai 400008",
        "lead_officer": "Abhinay",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.815, 18.965],
                [72.845, 18.965],
                [72.845, 18.995],
                [72.815, 18.995],
                [72.815, 18.965]
            ]]
        }
    },
    {
        "id": "WARD-BMC-A",
        "authority_id": "AUTH-BMC",
        "zone_id": "ZONE-BMC-01",
        "ward_code": "A-Ward",
        "ward_name": "A-Ward (Colaba / Fort / Marine Drive)",
        "office_address": "A Ward Office, 134-E, Shahid Bhagat Singh Marg, Fort, Mumbai 400001",
        "lead_officer": "Abhinay",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.805, 18.890],
                [72.845, 18.890],
                [72.845, 18.945],
                [72.805, 18.945],
                [72.805, 18.890]
            ]]
        }
    },

    # NMMC Administrative Wards (Navi Mumbai)
    {
        "id": "WARD-NMMC-VASHI",
        "authority_id": "AUTH-NMMC",
        "zone_id": "ZONE-NMMC-01",
        "ward_code": "NMMC-Vashi",
        "ward_name": "NMMC Vashi Ward Office",
        "office_address": "Vashi Ward Office, Sector 5, Near Shabari Hotel, Vashi, Navi Mumbai 400703",
        "lead_officer": "Abhinay",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.980, 19.065],
                [73.018, 19.065],
                [73.018, 19.092],
                [72.980, 19.092],
                [72.980, 19.065]
            ]]
        }
    },
    {
        "id": "WARD-NMMC-BELAPUR",
        "authority_id": "AUTH-NMMC",
        "zone_id": "ZONE-NMMC-01",
        "ward_code": "NMMC-Belapur",
        "ward_name": "NMMC Belapur Ward Office",
        "office_address": "CBD Belapur Ward Office, Sector 11, CBD Belapur, Navi Mumbai 400614",
        "lead_officer": "Abhinay",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [73.015, 18.995],
                [73.075, 18.995],
                [73.075, 19.030],
                [73.015, 19.030],
                [73.015, 18.995]
            ]]
        }
    },
    {
        "id": "WARD-NMMC-NERUL",
        "authority_id": "AUTH-NMMC",
        "zone_id": "ZONE-NMMC-01",
        "ward_code": "NMMC-Nerul",
        "ward_name": "NMMC Nerul Ward Office",
        "office_address": "Nerul Ward Office, Sector 3, Near Nerul Gymkhana, Nerul, Navi Mumbai 400706",
        "lead_officer": "Abhinay",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [73.000, 19.020],
                [73.045, 19.020],
                [73.045, 19.055],
                [73.000, 19.055],
                [73.000, 19.020]
            ]]
        }
    },
    {
        "id": "WARD-NMMC-TURBHE",
        "authority_id": "AUTH-NMMC",
        "zone_id": "ZONE-NMMC-01",
        "ward_code": "NMMC-Turbhe",
        "ward_name": "NMMC Turbhe Ward Office",
        "office_address": "Turbhe Ward Office, Sector 20, Turbhe, Navi Mumbai 400705",
        "lead_officer": "Abhinay",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [73.000, 19.055],
                [73.045, 19.055],
                [73.045, 19.095],
                [73.000, 19.095],
                [73.000, 19.055]
            ]]
        }
    },
    {
        "id": "WARD-NMMC-KK",
        "authority_id": "AUTH-NMMC",
        "zone_id": "ZONE-NMMC-02",
        "ward_code": "NMMC-KoparKhairane",
        "ward_name": "NMMC Kopar Khairane Ward Office",
        "office_address": "Kopar Khairane Ward Office, Sector 5, Kopar Khairane, Navi Mumbai 400709",
        "lead_officer": "Abhinay",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.985, 19.092],
                [73.030, 19.092],
                [73.030, 19.125],
                [72.985, 19.125],
                [72.985, 19.092]
            ]]
        }
    },
    {
        "id": "WARD-NMMC-AIROLI",
        "authority_id": "AUTH-NMMC",
        "zone_id": "ZONE-NMMC-02",
        "ward_code": "NMMC-Airoli",
        "ward_name": "NMMC Airoli Ward Office",
        "office_address": "Airoli Ward Office, Sector 5, Airoli, Navi Mumbai 400708",
        "lead_officer": "Abhinay",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.980, 19.145],
                [73.025, 19.145],
                [73.025, 19.185],
                [72.980, 19.185],
                [72.980, 19.145]
            ]]
        }
    }
]

# -----------------------------------------------------------------------------
# 4. CIVILENS OPERATIONAL SUB-WARDS (Clearly marked as CIVILENS operational service units)
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
        "supervisor_name": "Supervisor A. Jadhav",
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
        "name": "CIVILENS Operational Sub-Ward N-02 (Ghatkopar West / LBS Marg Beat)",
        "is_official": False,
        "operational_type": "CIVILENS_OPERATIONAL_SUB_WARD",
        "supervisor_name": "Supervisor R. Mhatre",
        "default_road_team_id": "TEAM-ROAD-01",
        "default_swm_team_id": "TEAM-SWM-01",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.890, 19.082],
                [72.925, 19.082],
                [72.925, 19.108],
                [72.890, 19.108],
                [72.890, 19.082]
            ]]
        }
    },
    {
        "id": "SUB-BMC-N-03",
        "ward_id": "WARD-BMC-N",
        "authority_id": "AUTH-BMC",
        "sub_ward_code": "N-03",
        "name": "CIVILENS Operational Sub-Ward N-03 (Pant Nagar / Eastern Express Beat)",
        "is_official": False,
        "operational_type": "CIVILENS_OPERATIONAL_SUB_WARD",
        "supervisor_name": "Supervisor K. Deshmukh",
        "default_road_team_id": "TEAM-ROAD-01",
        "default_swm_team_id": "TEAM-SWM-01",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.915, 19.065],
                [72.935, 19.065],
                [72.935, 19.095],
                [72.915, 19.095],
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
        "name": "CIVILENS Operational Sub-Ward L-01 (Kurla West Station & Link Road Beat)",
        "is_official": False,
        "operational_type": "CIVILENS_OPERATIONAL_SUB_WARD",
        "supervisor_name": "Supervisor M. Ansari",
        "default_road_team_id": "TEAM-ROAD-02",
        "default_swm_team_id": "TEAM-SWM-03",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.855, 19.055],
                [72.875, 19.055],
                [72.875, 19.075],
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
        "name": "CIVILENS Operational Sub-Ward L-02 (Kurla East / Nehru Nagar Beat)",
        "is_official": False,
        "operational_type": "CIVILENS_OPERATIONAL_SUB_WARD",
        "supervisor_name": "Supervisor P. Shinde",
        "default_road_team_id": "TEAM-ROAD-02",
        "default_swm_team_id": "TEAM-SWM-03",
        "is_active": True,
        "boundary_geojson": {
            "type": "Polygon",
            "coordinates": [[
                [72.875, 19.055],
                [72.890, 19.055],
                [72.890, 19.075],
                [72.875, 19.075],
                [72.875, 19.055]
            ]]
        }
    },
    {
        "id": "SUB-BMC-L-03",
        "ward_id": "WARD-BMC-L",
        "authority_id": "AUTH-BMC",
        "sub_ward_code": "L-03",
        "name": "CIVILENS Operational Sub-Ward L-03 (Sakinaka & Asalpha Junction Beat)",
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
