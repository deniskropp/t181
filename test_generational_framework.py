
import unittest
import sys
import os
# Force local import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "klipper_sdk/src")))

import shutil
import json
import tempfile
from pathlib import Path
from klipper_sdk.generational import (
    GenerationTracker,
    GenerationalBlueprintManager,
    GenerationalImprovementLoop,
    GenerationPhase,
    ComponentStatus,
    GenerationMetric
)

class TestGenerationalFramework(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.tracker = GenerationTracker("TestComponent")
        self.bp_manager = GenerationalBlueprintManager(os.path.join(self.test_dir, "blueprints"))
        self.loop = GenerationalImprovementLoop(self.tracker, self.bp_manager)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_tracker_lifecycle(self):
        """Test the basic lifecycle of the GenerationTracker."""
        self.assertEqual(self.tracker.current_generation, 0)
        
        # Start Gen 1
        gen_id = self.tracker.start_next_generation()
        self.assertEqual(gen_id, 1)
        
        # Log metrics
        self.tracker.log_metric("cpu_usage", 45.5)
        self.tracker.log_metric("memory_mb", 1024)
        
        # Register artifact
        dummy_artifact = os.path.join(self.test_dir, "build.log")
        with open(dummy_artifact, "w") as f:
            f.write("Build success")
        self.tracker.register_artifact("build_log", dummy_artifact)
        
        # Finalize
        snapshot = self.tracker.finalize_generation(notes=["Initial release"])
        
        self.assertEqual(len(self.tracker.history), 1)
        self.assertEqual(snapshot.gen_id, 1)
        self.assertEqual(snapshot.metrics[0].name, "cpu_usage")
        self.assertEqual(snapshot.status, ComponentStatus.STABLE)
        self.assertIn("build_log", snapshot.artifacts)

    def test_blueprint_metrics(self):
        """Test blueprint saving, loading, and diffing."""
        content_v1 = "step: 1\naction: run"
        content_v2 = "step: 1\naction: walk"
        
        self.bp_manager.save_blueprint("plan", content_v1, "v1")
        self.bp_manager.save_blueprint("plan", content_v2, "v2")
        
        loaded = self.bp_manager.load_blueprint("plan", "v1")
        self.assertEqual(loaded, content_v1)
        
        diff = self.bp_manager.diff_blueprints("plan", "v1", "v2")
        # Diff format is unified diff, so check for signs of it
        self.assertTrue(any("-action: run" in line for line in diff))
        self.assertTrue(any("+action: walk" in line for line in diff))

    def test_improvement_loop_flow(self):
        """Test that the improvement loop transitions through phases correctly."""
        # Mock the methods to avoid complex logic in unit test
        original_test = self.loop.phase_test
        original_apply = self.loop.phase_apply
        
        self.loop.phase_test = lambda ctx: {"success": True, "coverage": 100}
        self.loop.phase_apply = lambda analysis, ctx: {"changes": ["mock_change"]}
        
        # Run cycle
        result = self.loop.run_full_cycle({})
        
        self.assertTrue(result['test']['success'])
        self.assertEqual(result['apply']['changes'], ["mock_change"])
        self.assertEqual(self.loop.current_phase, GenerationPhase.VALIDATE)
        
        # Check that generation advanced
        self.assertEqual(self.tracker.current_generation, 1)
        self.assertEqual(self.tracker.history[0].changelog, ["mock_change"])

    def test_persistence_callback(self):
        """Test that the persistence callback is triggered."""
        saved_data = []
        def persist(data):
            saved_data.append(data)
            
        tracker = GenerationTracker("CallbackTest", persistence_callback=persist)
        tracker.start_next_generation()
        tracker.finalize_generation()
        
        self.assertEqual(len(saved_data), 1)
        self.assertEqual(saved_data[0]['component_name'], "CallbackTest")

if __name__ == '__main__':
    unittest.main()
