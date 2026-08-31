import unittest
import sys
import os

# Add root directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.agentic_workflow.agent_router import (
    ProjectState,
    FileCategory,
    detect_file_category,
    route_to_specialist,
    route_after_pm,
    MultiAgentFeedbackEngine
)


class TestAgentRouter(unittest.TestCase):

    def test_file_category_detection(self):
        self.assertEqual(detect_file_category("src/frontend/index.html"), FileCategory.FRONTEND)
        self.assertEqual(detect_file_category("src/backend/api/auth.py"), FileCategory.BACKEND)
        self.assertEqual(detect_file_category("tests/test_backend_core.py"), FileCategory.QA_TEST)
        self.assertEqual(detect_file_category("docker-compose.yml"), FileCategory.DEVOPS)
        self.assertEqual(detect_file_category("src/backend/core/nav_engine.py"), FileCategory.DATA_MATH)
        self.assertEqual(detect_file_category("docs/README.md"), FileCategory.GENERAL_DOCS)

    def test_contextual_specialist_routing(self):
        state_frontend = ProjectState(task="Build bet slip", file_path="src/frontend/app.tsx")
        self.assertEqual(route_to_specialist(state_frontend), "ui_ux_node")

        state_backend = ProjectState(task="Add JWT auth", file_path="src/backend/api/auth.py")
        self.assertEqual(route_to_specialist(state_backend), "security_node")

        state_qa = ProjectState(task="Add boundary test", file_path="tests/test_math.py")
        self.assertEqual(route_to_specialist(state_qa), "qa_node")

        state_devops = ProjectState(task="Setup docker", file_path="Dockerfile")
        self.assertEqual(route_to_specialist(state_devops), "devops_node")

        state_math = ProjectState(task="Calculate Kelly stake", file_path="src/backend/core/kelly.py")
        self.assertEqual(route_to_specialist(state_math), "data_math_node")

        state_docs = ProjectState(task="Update GDD", file_path="docs/gdd.md")
        self.assertEqual(route_to_specialist(state_docs), "pm_node")

    def test_successful_feedback_loop_pass(self):
        engine = MultiAgentFeedbackEngine()
        state = ProjectState(task="Create NAV chart", file_path="src/frontend/index.html")
        result = engine.run(state)
        self.assertTrue(result.is_completed)
        self.assertEqual(result.pm_status, "PASS")
        self.assertEqual(result.specialist_name, "Senior UI/UX Designer Agent")
        self.assertFalse(result.requires_human_intervention)

    def test_revision_and_recovery_loop(self):
        iteration = 0

        def custom_security(state: ProjectState) -> ProjectState:
            nonlocal iteration
            if iteration == 0:
                state.specialist_feedback = "[REVISE] SQL Injection vector detected in raw query."
            else:
                state.specialist_feedback = "[SECURE] Parameterized query implemented correctly."
            iteration += 1
            return state

        engine = MultiAgentFeedbackEngine(security_fn=custom_security)
        state = ProjectState(task="Write login query", file_path="src/backend/api/auth.py")
        result = engine.run(state)

        self.assertTrue(result.is_completed)
        self.assertEqual(result.pm_status, "PASS")
        self.assertEqual(result.revision_count, 1)

    def test_deadlock_breaker_human_fallback(self):
        # Simulates stubborn specialist that never passes
        def stubborn_qa(state: ProjectState) -> ProjectState:
            state.specialist_feedback = "[BLOCK] Test coverage remains below required threshold."
            return state

        engine = MultiAgentFeedbackEngine(qa_fn=stubborn_qa)
        state = ProjectState(task="Implement simulator math", file_path="tests/test_math.py")
        result = engine.run(state)

        self.assertFalse(result.is_completed)
        self.assertTrue(result.requires_human_intervention)
        self.assertEqual(result.revision_count, 3)
        self.assertEqual(route_after_pm(result), "human_fallback_node")


if __name__ == "__main__":
    unittest.main()
