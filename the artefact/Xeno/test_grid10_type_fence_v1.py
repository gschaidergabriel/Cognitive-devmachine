from __future__ import annotations

import unittest

from entry_fabric_v1 import IngressSource, Modality, ResourceBudget, XenoIngressDraft, admit_ingress
from grid10_scheduler_v1 import FunctionRequest, ScheduleError, SchedulerConfig, XenoMode, compile_grid_plan

GENERATION = 17


def packet():
    draft = XenoIngressDraft(
        causal_id="causal:type-fence:1",
        generation=GENERATION,
        source=IngressSource.HUMAN,
        provenance=("source:test",),
        modality=Modality.TEXT,
        observed_at="2026-08-23T16:00:00Z",
        received_at="2026-08-23T16:00:01Z",
        isolation_domain="session:type-fence",
        permissions=("context.read",),
        capability_scope=(),
        resource_budget=ResourceBudget(10, 4, 2400, 8000, 0),
        payload_ref="sha256:" + "a" * 64,
    )
    return admit_ingress(draft, current_generation=GENERATION)


class Grid10TypeFenceTests(unittest.TestCase):
    def test_function_request_scalar_coercions_fail_closed(self):
        admitted = packet()
        invalid = (
            FunctionRequest("float-priority", 1.5),
            FunctionRequest("numeric-string-priority", "90"),
            FunctionRequest("string-bool", 90, inference_required="false"),
            FunctionRequest("bool-token", 90, estimated_tokens=True),
            FunctionRequest(123, 90),
        )
        for request in invalid:
            with self.subTest(request=request), self.assertRaises(ScheduleError):
                compile_grid_plan(
                    admitted,
                    (request,),
                    mode=XenoMode.XENO_GRID10,
                    current_generation=GENERATION,
                )

    def test_scheduler_config_coercions_fail_closed(self):
        admitted = packet()
        request = (FunctionRequest("hypothesis", 90, estimated_tokens=100),)
        invalid_configs = (
            SchedulerConfig(max_logical_cells=True),
            SchedulerConfig(max_logical_cells=10.0),
            SchedulerConfig(shared_workers=(123,)),
            SchedulerConfig(shared_workers=["xcu:worker-0"]),
        )
        for config in invalid_configs:
            with self.subTest(config=config), self.assertRaises(ScheduleError):
                compile_grid_plan(
                    admitted,
                    request,
                    mode=XenoMode.XENO_GRID10,
                    current_generation=GENERATION,
                    config=config,
                )

    def test_generation_and_function_container_types_fail_closed(self):
        admitted = packet()
        request = FunctionRequest("critic", 80, estimated_tokens=100)
        for generation in (True, 17.0, "17"):
            with self.subTest(generation=generation), self.assertRaises(ScheduleError):
                compile_grid_plan(
                    admitted,
                    (request,),
                    mode=XenoMode.XENO_GRID10,
                    current_generation=generation,
                )
        with self.assertRaises(ScheduleError):
            compile_grid_plan(
                admitted,
                [request],
                mode=XenoMode.XENO_GRID10,
                current_generation=GENERATION,
            )

    def test_valid_typed_plan_remains_deterministic(self):
        admitted = packet()
        requests = (
            FunctionRequest("hypothesis", 90, estimated_tokens=100),
            FunctionRequest("critic", 80, inference_required=False, estimated_tokens=0),
        )
        a = compile_grid_plan(
            admitted,
            requests,
            mode=XenoMode.XENO_GRID10,
            current_generation=GENERATION,
            config=SchedulerConfig(max_logical_cells=10, shared_workers=("xcu:worker-0",)),
        )
        b = compile_grid_plan(
            admitted,
            requests,
            mode=XenoMode.XENO_GRID10,
            current_generation=GENERATION,
            config=SchedulerConfig(max_logical_cells=10, shared_workers=("xcu:worker-0",)),
        )
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
