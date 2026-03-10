#!/usr/bin/env python3
import contextlib
import io
import json
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
STATECTL_PATH = ROOT / "java-migration" / "scripts" / "state"
import sys

if str(STATECTL_PATH) not in sys.path:
    sys.path.insert(0, str(STATECTL_PATH))

from statectl import main as statectl_main
from state_helpers import load_json


class StateCtlContractTest(unittest.TestCase):
    def test_state_machine_contract_preserves_phase_and_mode_invariants(self) -> None:
        contract = load_json(ROOT / "java-migration" / "references" / "contracts" / "state-machine.json")
        phase_defaults = contract["phase_defaults"]
        transitions = contract["transitions"]

        self.assertEqual(
            list(phase_defaults),
            [
                "bootstrap_governance",
                "structured_discovery",
                "migration_planning",
                "automated_execution",
                "last_mile_stabilization",
                "controlled_fallback",
            ],
        )
        self.assertNotIn("resume", phase_defaults)
        self.assertEqual({cfg["next_skill"] for cfg in phase_defaults.values()}, {"java-migration"})
        self.assertEqual(
            {cfg["operating_mode"] for cfg in phase_defaults.values()},
            {"bootstrap", "discover", "plan", "execute", "stabilize", "fallback"},
        )
        self.assertIn("openrewrite_fallback", transitions)
        self.assertEqual(transitions["openrewrite_fallback"]["to_phase"], "controlled_fallback")
        self.assertFalse(transitions["openrewrite_fallback"]["clear_exception"])

    def run_statectl(self, argv: list[str]) -> tuple[int, str]:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = statectl_main(argv)
        return code, stdout.getvalue().strip()

    def test_contract_flow_bootstrap_to_fallback_to_last_mile(self) -> None:
        with tempfile.TemporaryDirectory(prefix="java-migration-statectl-") as tmp:
            repo = pathlib.Path(tmp)
            (repo / "pom.xml").write_text("<project />\n", encoding="utf-8")

            subprocess.run(
                ["bash", "java-migration/scripts/bootstrap/init-migration-kit.sh", str(repo)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

            migration_dir = repo / "docs" / "java-migration"
            state_dir = migration_dir / "state"
            project_state_path = state_dir / "project.state.json"
            milestone_state_path = state_dir / "active-milestone.json"
            scopes_csv = migration_dir / "discovery-protocol" / "manifests" / "scopes.csv"
            runs_dir = migration_dir / "discovery-protocol" / "runs"

            scopes_csv.write_text(
                "scope_id,scope_type,scope_path,scope_name,inventory_mode,status,notes\n"
                "scope-a,module,service-a,Service A,auto,pending,\n",
                encoding="utf-8",
            )
            (runs_dir / "scope-a").mkdir(parents=True, exist_ok=True)

            code, _ = self.run_statectl(
                [
                    "sync-next-scopes",
                    str(project_state_path),
                    str(milestone_state_path),
                    str(scopes_csv),
                    str(runs_dir),
                ]
            )
            self.assertEqual(code, 0)

            project_state = load_json(project_state_path)
            self.assertEqual(project_state["current_phase"], "structured_discovery")
            self.assertEqual(project_state["operating_mode"], "discover")

            (runs_dir / "scope-a" / "summary.state").write_text(
                "STATUS\tcompleted\nAUTOMATION_ELIGIBILITY\topenrewrite_ready\n",
                encoding="utf-8",
            )

            code, _ = self.run_statectl(
                [
                    "plan-wave",
                    str(project_state_path),
                    str(milestone_state_path),
                    str(scopes_csv),
                    str(runs_dir),
                ]
            )
            self.assertEqual(code, 0)

            project_state = load_json(project_state_path)
            milestone_state = load_json(milestone_state_path)
            self.assertEqual(project_state["current_phase"], "automated_execution")
            self.assertEqual(project_state["operating_mode"], "execute")
            self.assertEqual(milestone_state["milestone_type"], "execution")

            summary_path = repo / "openrewrite-summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "run_id": "or-001",
                        "status": "rewrite_failed",
                        "scopes": ["scope-a"],
                        "recipes": ["org.openrewrite.java.migrate.jakarta.JavaxMigrationToJakarta"],
                        "validation_status": "failed",
                    }
                ),
                encoding="utf-8",
            )

            code, _ = self.run_statectl(
                [
                    "register-openrewrite",
                    str(project_state_path),
                    str(milestone_state_path),
                    str(summary_path),
                ]
            )
            self.assertEqual(code, 0)

            route_code, route_output = self.run_statectl(
                ["route", str(project_state_path), str(milestone_state_path)]
            )
            self.assertEqual(route_code, 0, route_output)

            project_state = load_json(project_state_path)
            milestone_state = load_json(milestone_state_path)
            self.assertEqual(project_state["current_phase"], "controlled_fallback")
            self.assertEqual(project_state["operating_mode"], "fallback")
            self.assertEqual(project_state["exception_state"]["exception_type"], "transformer_exception")
            self.assertEqual(milestone_state["milestone_type"], "fallback")

            code, _ = self.run_statectl(
                [
                    "register-fallback",
                    str(project_state_path),
                    str(milestone_state_path),
                    "--scope",
                    "scope-a",
                    "--phase-status",
                    "completed",
                    "--exception-status",
                    "resolved",
                    "--exception-type",
                    "transformer_exception",
                    "--summary",
                    "Transformer exception resolved through minimal manual fallback",
                    "--entry-criteria",
                    "OpenRewrite failed for the selected artifact set",
                    "--exit-condition",
                    "Proceed to last-mile stabilization and verify the residual state",
                    "--transition-reason",
                    "Controlled fallback completed for the failed execution wave",
                ]
            )
            self.assertEqual(code, 0)

            project_state = load_json(project_state_path)
            self.assertEqual(project_state["current_phase"], "controlled_fallback")
            self.assertEqual(project_state["phase_status"], "completed")
            self.assertIsNone(project_state["exception_state"])

            code, _ = self.run_statectl(
                [
                    "register-last-mile",
                    str(project_state_path),
                    str(milestone_state_path),
                    "--scope",
                    "scope-a",
                    "--status",
                    "completed",
                    "--validation-status",
                    "passed",
                ]
            )
            self.assertEqual(code, 0)

            route_code, route_output = self.run_statectl(
                ["route", str(project_state_path), str(milestone_state_path)]
            )
            self.assertEqual(route_code, 0, route_output)

            project_state = load_json(project_state_path)
            milestone_state = load_json(milestone_state_path)
            self.assertEqual(project_state["current_phase"], "last_mile_stabilization")
            self.assertEqual(project_state["operating_mode"], "stabilize")
            self.assertEqual(project_state["phase_status"], "completed")
            self.assertEqual(milestone_state["milestone_type"], "stabilization")
            self.assertEqual(milestone_state["selected_scope_ids"], [])
            self.assertEqual(milestone_state["next_scope_ids"], [])
            self.assertEqual(milestone_state["stabilized_scope_ids"], ["scope-a"])

    def test_invalid_transition_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="java-migration-statectl-invalid-") as tmp:
            repo = pathlib.Path(tmp)
            (repo / "pom.xml").write_text("<project />\n", encoding="utf-8")

            subprocess.run(
                ["bash", "java-migration/scripts/bootstrap/init-migration-kit.sh", str(repo)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

            state_dir = repo / "docs" / "java-migration" / "state"
            project_state_path = state_dir / "project.state.json"
            milestone_state_path = state_dir / "active-milestone.json"

            with self.assertRaisesRegex(
                ValueError,
                "event last_mile_completed is not allowed from current_phase=bootstrap_governance",
            ):
                self.run_statectl(
                    [
                        "register-last-mile",
                        str(project_state_path),
                        str(milestone_state_path),
                        "--status",
                        "completed",
                        "--validation-status",
                        "passed",
                    ]
                )

    def test_plan_wave_can_resume_after_last_mile_completion(self) -> None:
        with tempfile.TemporaryDirectory(prefix="java-migration-statectl-resume-wave-") as tmp:
            repo = pathlib.Path(tmp)
            (repo / "pom.xml").write_text("<project />\n", encoding="utf-8")

            subprocess.run(
                ["bash", "java-migration/scripts/bootstrap/init-migration-kit.sh", str(repo)],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

            migration_dir = repo / "docs" / "java-migration"
            state_dir = migration_dir / "state"
            project_state_path = state_dir / "project.state.json"
            milestone_state_path = state_dir / "active-milestone.json"
            scopes_csv = migration_dir / "discovery-protocol" / "manifests" / "scopes.csv"
            runs_dir = migration_dir / "discovery-protocol" / "runs"

            scopes_csv.write_text(
                "scope_id,scope_type,scope_path,scope_name,inventory_mode,status,notes\n"
                "scope-a,module,service-a,Service A,auto,pending,\n"
                "scope-b,module,service-b,Service B,auto,pending,\n",
                encoding="utf-8",
            )
            (runs_dir / "scope-a").mkdir(parents=True, exist_ok=True)
            (runs_dir / "scope-b").mkdir(parents=True, exist_ok=True)

            code, _ = self.run_statectl(
                [
                    "sync-next-scopes",
                    str(project_state_path),
                    str(milestone_state_path),
                    str(scopes_csv),
                    str(runs_dir),
                ]
            )
            self.assertEqual(code, 0)

            (runs_dir / "scope-a" / "summary.state").write_text(
                "STATUS\tcompleted\nAUTOMATION_ELIGIBILITY\topenrewrite_ready\n",
                encoding="utf-8",
            )
            (runs_dir / "scope-b" / "summary.state").write_text(
                "STATUS\tcompleted\nAUTOMATION_ELIGIBILITY\topenrewrite_ready\n",
                encoding="utf-8",
            )

            code, _ = self.run_statectl(
                [
                    "plan-wave",
                    str(project_state_path),
                    str(milestone_state_path),
                    str(scopes_csv),
                    str(runs_dir),
                ]
            )
            self.assertEqual(code, 0)

            summary_path = repo / "openrewrite-summary.json"
            summary_path.write_text(
                json.dumps(
                    {
                        "run_id": "or-001",
                        "status": "rewrite_applied_validation_passed",
                        "scopes": ["scope-a"],
                        "recipes": ["org.openrewrite.java.migrate.jakarta.JavaxMigrationToJakarta"],
                        "validation_status": "passed",
                    }
                ),
                encoding="utf-8",
            )

            code, _ = self.run_statectl(
                [
                    "register-openrewrite",
                    str(project_state_path),
                    str(milestone_state_path),
                    str(summary_path),
                ]
            )
            self.assertEqual(code, 0)

            code, _ = self.run_statectl(
                [
                    "register-last-mile",
                    str(project_state_path),
                    str(milestone_state_path),
                    "--scope",
                    "scope-a",
                    "--status",
                    "completed",
                    "--validation-status",
                    "passed",
                ]
            )
            self.assertEqual(code, 0)

            project_state = load_json(project_state_path)
            self.assertEqual(project_state["current_phase"], "last_mile_stabilization")
            self.assertEqual(project_state["phase_status"], "completed")
            milestone_state = load_json(milestone_state_path)
            self.assertEqual(milestone_state["selected_scope_ids"], [])
            self.assertEqual(milestone_state["next_scope_ids"], [])
            self.assertEqual(milestone_state["stabilized_scope_ids"], ["scope-a"])

            code, selected = self.run_statectl(
                [
                    "plan-wave",
                    str(project_state_path),
                    str(milestone_state_path),
                    str(scopes_csv),
                    str(runs_dir),
                ]
            )
            self.assertEqual(code, 0)
            self.assertEqual(selected, "scope-b")

            route_code, route_output = self.run_statectl(
                ["route", str(project_state_path), str(milestone_state_path)]
            )
            self.assertEqual(route_code, 0, route_output)

            project_state = load_json(project_state_path)
            milestone_state = load_json(milestone_state_path)
            self.assertEqual(project_state["current_phase"], "automated_execution")
            self.assertEqual(project_state["operating_mode"], "execute")
            self.assertEqual(project_state["phase_status"], "in_progress")
            self.assertEqual(milestone_state["milestone_type"], "execution")
            self.assertEqual(milestone_state["selected_scope_ids"], ["scope-b"])
            self.assertEqual(milestone_state["stabilized_scope_ids"], ["scope-a"])


if __name__ == "__main__":
    unittest.main()
