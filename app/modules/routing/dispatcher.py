from typing import Tuple
from app.models.issue import IssueCategory, PriorityLevel

class DepartmentDispatcher:
    """
    Automated department routing and actionable recommendation advisory.
    Determines responsible civic agency and operational SLAs based on category and priority.
    """

    DEPARTMENT_MAP = {
        IssueCategory.ROAD_DAMAGE: "Roads & Traffic Infrastructure Dept (MCGM)",
        IssueCategory.SANITATION: "Solid Waste Management (SWM Dept)",
        IssueCategory.WATER_SUPPLY: "Hydraulic Engineering Department (HED)",
        IssueCategory.ELECTRICAL: "BEST Undertaking / Street Lighting Wing",
        IssueCategory.TRAFFIC_SAFETY: "Traffic Police & Urban Transit Cell",
        IssueCategory.UNSPECIFIED: "Ward Citizen Grievance Cell"
    }

    ACTION_MAP = {
        IssueCategory.ROAD_DAMAGE: {
            PriorityLevel.CRITICAL: ("Deploy emergency cold-mix quick repair gang within 12 hours; place reflective barriers.", 12),
            PriorityLevel.HIGH: ("Schedule asphalt resurfacing patch work within 24 hours.", 24),
            PriorityLevel.MEDIUM: ("Add to weekly ward road maintenance roster.", 48),
            PriorityLevel.LOW: ("Monitor during bi-weekly route inspection.", 72)
        },
        IssueCategory.SANITATION: {
            PriorityLevel.CRITICAL: ("Emergency bulk compactor dispatch and immediate disinfectant spraying.", 12),
            PriorityLevel.HIGH: ("Deploy collection truck on primary route shift.", 24),
            PriorityLevel.MEDIUM: ("Clear community collection point by end of day.", 36),
            PriorityLevel.LOW: ("Routine morning waste pickup.", 48)
        },
        IssueCategory.WATER_SUPPLY: {
            PriorityLevel.CRITICAL: ("Immediate water valve isolation; deploy main conduit repair crew.", 6),
            PriorityLevel.HIGH: ("Pipeline leak inspection and pressure equalization repair.", 18),
            PriorityLevel.MEDIUM: ("Schedule valve seal replacement.", 36),
            PriorityLevel.LOW: ("Inspect meter leakage.", 72)
        }
    }

    DEFAULT_ACTIONS = {
        PriorityLevel.CRITICAL: ("High-priority dispatch to field supervisor.", 12),
        PriorityLevel.HIGH: ("Assign field engineer inspection.", 24),
        PriorityLevel.MEDIUM: ("Schedule standard ward response.", 48),
        PriorityLevel.LOW: ("Standard triage review.", 72)
    }

    def route_issue(self, category: IssueCategory, priority: PriorityLevel) -> Tuple[str, str, int]:
        dept = self.DEPARTMENT_MAP.get(category, "Municipal Administration")
        actions_for_cat = self.ACTION_MAP.get(category, self.DEFAULT_ACTIONS)
        action, sla = actions_for_cat.get(priority, self.DEFAULT_ACTIONS[priority])
        return dept, action, sla

department_dispatcher = DepartmentDispatcher()
