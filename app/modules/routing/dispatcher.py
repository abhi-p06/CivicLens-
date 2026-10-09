from typing import Tuple, Dict, Any, Optional
from app.models.issue import IssueCategory, PriorityLevel

def get_default_routing_config() -> Dict[str, Dict[str, Any]]:
    return {
        IssueCategory.ROAD_DAMAGE.value: {
            "department": "Roads & Traffic Infrastructure Dept (MCGM)",
            "code": "MCGM-ROADS",
            "actions": {
                PriorityLevel.CRITICAL.value: ("Deploy emergency cold-mix quick repair crew within 12 hours; erect hazard cones.", 12),
                PriorityLevel.HIGH.value: ("Schedule asphalt patch work within 24 hours.", 24),
                PriorityLevel.MEDIUM.value: ("Add to weekly ward road maintenance roster.", 48),
                PriorityLevel.LOW.value: ("Monitor during bi-weekly route inspection.", 72)
            }
        },
        IssueCategory.SANITATION.value: {
            "department": "Solid Waste Management (SWM Dept)",
            "code": "MCGM-SWM",
            "actions": {
                PriorityLevel.CRITICAL.value: ("Emergency bulk compactor dispatch and immediate disinfectant spraying.", 12),
                PriorityLevel.HIGH.value: ("Deploy collection truck on primary route shift.", 24),
                PriorityLevel.MEDIUM.value: ("Clear community collection point by end of day.", 36),
                PriorityLevel.LOW.value: ("Routine morning waste pickup.", 48)
            }
        },
        IssueCategory.WATER_SUPPLY.value: {
            "department": "Hydraulic Engineering Department (HED)",
            "code": "MCGM-HED",
            "actions": {
                PriorityLevel.CRITICAL.value: ("Immediate water valve isolation; deploy main conduit repair crew.", 6),
                PriorityLevel.HIGH.value: ("Pipeline leak inspection and pressure equalization repair.", 18),
                PriorityLevel.MEDIUM.value: ("Schedule valve seal replacement.", 36),
                PriorityLevel.LOW.value: ("Inspect meter leakage.", 72)
            }
        },
        IssueCategory.ELECTRICAL.value: {
            "department": "BEST Undertaking / Street Lighting Wing",
            "code": "BEST-ELEC",
            "actions": {
                PriorityLevel.CRITICAL.value: ("Immediate emergency crew dispatch to secure live exposed wires.", 4),
                PriorityLevel.HIGH.value: ("Replace faulty luminaire and reset feeder breaker within 24 hours.", 24),
                PriorityLevel.MEDIUM.value: ("Inspect luminaire connection on weekly circuit check.", 48),
                PriorityLevel.LOW.value: ("Routine fixture inspection.", 72)
            }
        },
        IssueCategory.STORM_WATER.value: {
            "department": "Storm Water Drains Department (SWD)",
            "code": "MCGM-SWD",
            "actions": {
                PriorityLevel.CRITICAL.value: ("Emergency suction tanker deployment to dewater blocked junction.", 6),
                PriorityLevel.HIGH.value: ("Desilt storm water culvert within 24 hours.", 24),
                PriorityLevel.MEDIUM.value: ("Clear drain grate debris.", 48),
                PriorityLevel.LOW.value: ("Schedule for pre-monsoon desilting.", 72)
            }
        },
        IssueCategory.TRAFFIC_SAFETY.value: {
            "department": "Traffic Police & Urban Transit Cell",
            "code": "MTP-TRANSIT",
            "actions": {
                PriorityLevel.CRITICAL.value: ("Deploy traffic marshals to redirect flow; repair signal fault immediately.", 4),
                PriorityLevel.HIGH.value: ("Inspect signal timer controller and fix zebra crossing within 24 hours.", 24),
                PriorityLevel.MEDIUM.value: ("Repaint lane markers and speed breakers.", 48),
                PriorityLevel.LOW.value: ("Routine traffic flow assessment.", 72)
            }
        }
    }

DEFAULT_DEPARTMENT_ROUTING_CONFIG = get_default_routing_config()

class ConfigurableDepartmentDispatcher:
    """
    Feature 19: Department Routing & Recommended Action
    
    Decoupled from ML classification logic:
    Allows municipal administrators to adjust department mappings, SLAs,
    and action protocols via configuration without touching machine learning models.
    """

    def __init__(self, routing_config: Optional[Dict[str, Dict[str, Any]]] = None):
        import copy
        self._config = copy.deepcopy(routing_config) if routing_config is not None else get_default_routing_config()

    def reset_to_defaults(self):
        self._config = get_default_routing_config()

    def update_routing_config(self, category_key: str, dept_info: Dict[str, Any]):
        """Allows dynamic runtime configuration of department routing."""
        self._config[category_key] = dept_info

    def get_routing_config(self) -> Dict[str, Dict[str, Any]]:
        return self._config

    def route_issue(
        self,
        category: IssueCategory,
        priority: PriorityLevel
    ) -> Tuple[str, str, int, str]:
        """
        Returns (department_name, recommended_action, sla_hours, department_code)
        """
        cat_key = category.value if hasattr(category, "value") else str(category)
        pri_key = priority.value if hasattr(priority, "value") else str(priority)

        dept_record = self._config.get(cat_key)
        if not dept_record:
            # Fallback for unspecified categories
            return (
                "Ward Citizen Grievance Cell",
                "Assign field engineer inspection and initial triage.",
                48,
                "MCGM-WARD"
            )

        dept_name = dept_record["department"]
        dept_code = dept_record.get("code", "MCGM-GEN")
        actions_dict = dept_record.get("actions", {})

        action_tuple = actions_dict.get(pri_key)
        if action_tuple:
            action, sla = action_tuple
        else:
            action = f"Inspect and schedule {cat_key} resolution."
            sla = 48

        return dept_name, action, sla, dept_code

department_dispatcher = ConfigurableDepartmentDispatcher()
