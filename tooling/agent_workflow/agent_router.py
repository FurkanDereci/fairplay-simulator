"""
FairPlay Simulator Multi-Agent Feedback Loop & Routing Engine
Implements:
1. Contextual Activation (route_to_specialist)
2. Gatekeeper Pattern (All specialists report to PM)
3. Deadlock Breaker (Human fallback at revision_count >= 3)
"""

from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from enum import Enum


class FileCategory(str, Enum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    QA_TEST = "qa_test"
    DEVOPS = "devops"
    DATA_MATH = "data_math"
    GENERAL_DOCS = "general_docs"


@dataclass
class ProjectState:
    task: str
    file_path: str = ""
    file_type: str = "general_docs"
    code: str = ""
    specialist_name: Optional[str] = None
    specialist_feedback: Optional[str] = None
    pm_status: str = "PENDING"  # PASS | REVISE | BLOCK
    pm_feedback: str = ""
    actionable_tasks: List[str] = field(default_factory=list)
    revision_count: int = 0
    history: List[Dict[str, Any]] = field(default_factory=list)
    is_completed: bool = False
    requires_human_intervention: bool = False


def detect_file_category(file_path: str, explicit_type: Optional[str] = None) -> FileCategory:
    """Detects appropriate category for contextual specialist activation."""
    if explicit_type:
        low = explicit_type.lower()
        if low in ["frontend", "ui", "react", "nextjs", "html", "css"]:
            return FileCategory.FRONTEND
        if low in ["backend", "api", "auth", "flask", "fastapi", "security"]:
            return FileCategory.BACKEND
        if low in ["test", "verification", "qa"]:
            return FileCategory.QA_TEST
        if low in ["infrastructure", "docker", "config", "github_actions", "opentelemetry", "devops"]:
            return FileCategory.DEVOPS
        if low in ["math", "simulator", "data_pipeline", "scraping", "pandas", "data_math"]:
            return FileCategory.DATA_MATH

    fp = file_path.lower()
    if any(k in fp for k in ["frontend/", ".html", ".css", ".jsx", ".tsx", "ui/"]):
        return FileCategory.FRONTEND
    if any(k in fp for k in ["backend/api", "auth", "security", "server", "app.py"]):
        return FileCategory.BACKEND
    if any(k in fp for k in ["tests/", "verification", "test_"]):
        return FileCategory.QA_TEST
    if any(k in fp for k in ["docker", "compose", "opentelemetry", ".github", "infra"]):
        return FileCategory.DEVOPS
    if any(k in fp for k in ["core/", "data_ingestion", "math", "simulator", "nav", "portfolio"]):
        return FileCategory.DATA_MATH

    return FileCategory.GENERAL_DOCS


def route_to_specialist(state: ProjectState) -> str:
    """Determines which specialist agent to wake up based on file category."""
    category = detect_file_category(state.file_path, state.file_type)
    
    if category == FileCategory.FRONTEND:
        return "ui_ux_node"
    elif category == FileCategory.BACKEND:
        return "security_node"
    elif category == FileCategory.QA_TEST:
        return "qa_node"
    elif category == FileCategory.DEVOPS:
        return "devops_node"
    elif category == FileCategory.DATA_MATH:
        return "data_math_node"
    else:
        return "pm_node"


def route_after_pm(state: ProjectState) -> str:
    """Evaluates whether to complete, retry coder, or break out to human."""
    if state.pm_status == "PASS":
        state.is_completed = True
        return "END"
    elif state.revision_count >= 3:
        state.requires_human_intervention = True
        return "human_fallback_node"
    else:
        return "coder_node"


class MultiAgentFeedbackEngine:
    """Executes the multi-agent state machine."""

    def __init__(
        self,
        coder_fn: Optional[Callable[[ProjectState], ProjectState]] = None,
        ui_ux_fn: Optional[Callable[[ProjectState], ProjectState]] = None,
        security_fn: Optional[Callable[[ProjectState], ProjectState]] = None,
        qa_fn: Optional[Callable[[ProjectState], ProjectState]] = None,
        devops_fn: Optional[Callable[[ProjectState], ProjectState]] = None,
        data_math_fn: Optional[Callable[[ProjectState], ProjectState]] = None,
        pm_fn: Optional[Callable[[ProjectState], ProjectState]] = None,
    ):
        self.coder_fn = coder_fn or self._default_coder
        self.ui_ux_fn = ui_ux_fn or self._default_ui_ux
        self.security_fn = security_fn or self._default_security
        self.qa_fn = qa_fn or self._default_qa
        self.devops_fn = devops_fn or self._default_devops
        self.data_math_fn = data_math_fn or self._default_data_math
        self.pm_fn = pm_fn or self._default_pm

    def _default_coder(self, state: ProjectState) -> ProjectState:
        state.history.append({"agent": "Coder", "action": f"Drafted code/task revision {state.revision_count}"})
        return state

    def _default_ui_ux(self, state: ProjectState) -> ProjectState:
        state.specialist_name = "Senior UI/UX Designer Agent"
        state.specialist_feedback = "[PASS] Visual hierarchy and loading states are clear."
        state.history.append({"agent": "UI/UX", "feedback": state.specialist_feedback})
        return state

    def _default_security(self, state: ProjectState) -> ProjectState:
        state.specialist_name = "AppSec Engineer Agent"
        state.specialist_feedback = "[SECURE] No injection vectors or unauthenticated endpoints found."
        state.history.append({"agent": "Security", "feedback": state.specialist_feedback})
        return state

    def _default_qa(self, state: ProjectState) -> ProjectState:
        state.specialist_name = "Senior QA Automation Agent"
        state.specialist_feedback = "[PASS] Test coverage meets simulation bounds and TDD standards."
        state.history.append({"agent": "QA", "feedback": state.specialist_feedback})
        return state

    def _default_devops(self, state: ProjectState) -> ProjectState:
        state.specialist_name = "DevOps & Cloud Architect Agent"
        state.specialist_feedback = "[PASS] Container resource limits and telemetry compliant."
        state.history.append({"agent": "DevOps", "feedback": state.specialist_feedback})
        return state

    def _default_data_math(self, state: ProjectState) -> ProjectState:
        state.specialist_name = "Senior Data & Math Engineer Agent"
        state.specialist_feedback = "[PASS] Decimal precision maintained; NAV invariant verified."
        state.history.append({"agent": "DataMath", "feedback": state.specialist_feedback})
        return state

    def _default_pm(self, state: ProjectState) -> ProjectState:
        # Default PM validates specialist feedback and approves if PASS/SECURE
        spec_fb = state.specialist_feedback or ""
        if "REVISE" in spec_fb or "BLOCK" in spec_fb or "CRITICAL" in spec_fb:
            state.pm_status = "REVISE"
            state.pm_feedback = f"PM Gatekeeper: Action required on specialist findings: {spec_fb}"
            state.actionable_tasks = ["Fix issues identified by specialist."]
            state.revision_count += 1
        else:
            state.pm_status = "PASS"
            state.pm_feedback = "PM Gatekeeper: Approved. MVP alignment, security, and math verified."
            state.actionable_tasks = []
        state.history.append({"agent": "PM", "status": state.pm_status, "feedback": state.pm_feedback})
        return state

    def run(self, initial_state: ProjectState) -> ProjectState:
        """Runs the loop until PASS, completion, or human fallback."""
        state = initial_state
        
        while not state.is_completed and not state.requires_human_intervention:
            # 1. Coder executes
            state = self.coder_fn(state)
            
            # 2. Contextual Routing to Specialist
            specialist_node = route_to_specialist(state)
            if specialist_node == "ui_ux_node":
                state = self.ui_ux_fn(state)
            elif specialist_node == "security_node":
                state = self.security_fn(state)
            elif specialist_node == "qa_node":
                state = self.qa_fn(state)
            elif specialist_node == "devops_node":
                state = self.devops_fn(state)
            elif specialist_node == "data_math_node":
                state = self.data_math_fn(state)
            
            # 3. Gatekeeper PM evaluates
            state = self.pm_fn(state)
            
            # 4. Route decision
            next_step = route_after_pm(state)
            if next_step == "END":
                break
            elif next_step == "human_fallback_node":
                state.history.append({"agent": "System", "action": "Triggered Human-in-the-loop fallback."})
                break
            # Otherwise loops back to coder_fn
            
        return state
