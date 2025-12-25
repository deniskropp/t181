
"""
Generational Framework Demo
This script demonstrates the full capabilities of the Klipper SDK Generational Framework.
It simulates the evolution of a hypothetical 'DataProcessor' component through multiple generations.
"""

import sys
import os
# Force local import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "klipper_sdk/src")))

import shutil
import time
import json
import random
from datetime import datetime
from klipper_sdk.generational import (
    GenerationTracker, 
    GenerationalBlueprintManager, 
    GenerationalImprovementLoop,
    GenerationPhase,
    ComponentStatus
)

def setup_demo_env():
    """Cleans up and recreates the demo environment."""
    if os.path.exists("demo_data"):
        shutil.rmtree("demo_data")
    os.makedirs("demo_data/blueprints")
    os.makedirs("demo_data/artifacts")
    print("Environment setup complete.")

def create_initial_blueprint(manager):
    """Creates the V1 blueprint for our component."""
    content = """
    # DataProcessor V1 Blueprint
    name: DataProcessor
    version: 1.0.0
    
    pipeline:
      - step: ingest
        type: file_reader
      - step: process
        type: simple_transform
      - step: output
        type: console_writer
    """
    manager.save_blueprint("DataProcessor", content, "1.0")
    print("Defined DataProcessor V1 Blueprint.")

class AutoEvolvingAgent:
    """Simulates an AI agent that can 'read' analysis and 'write' code (simulated)."""
    
    def process_analysis(self, analysis_report):
        """Decides what changes to make based on analysis."""
        changes = []
        recommendations = analysis_report.get('recommendations', [])
        
        if "optimize_processing" in recommendations:
            changes.append("Refactored loop for O(n) complexity")
        if "improve_error_handling" in recommendations:
            changes.append("Added try/catch blocks to ingestion")
        
        if not changes:
            changes.append("Minor documentation updates")
            
        return changes

def run_demo():
    print("=== Starting Generational Framework Demo ===\n")
    setup_demo_env()
    
    # 1. Initialize Components
    tracker = GenerationTracker("DataProcessor")
    bp_manager = GenerationalBlueprintManager("demo_data/blueprints")
    agent = AutoEvolvingAgent()
    
    # Custom subclass for demo purposes to inject specific logic
    class DemoImprovementLoop(GenerationalImprovementLoop):
        
        def phase_test(self, context):
            self._switch_phase(GenerationPhase.TEST)
            print(f"   [TEST] Running test suite for Gen {self.tracker.current_generation}...")
            time.sleep(0.5) 
            
            # Simulate test results improving over generations
            gen = self.tracker.current_generation
            coverage = 0.70 + (gen * 0.05) if gen < 5 else 0.95
            latency = 200 - (gen * 20) if gen < 5 else 100
            
            self.tracker.log_metric("test_coverage", coverage)
            self.tracker.log_metric("avg_latency_ms", latency)
            
            success = coverage > 0.60
            return {
                "success": success, 
                "coverage": coverage, 
                "latency": latency,
                "failures": ["test_edge_case"] if gen == 1 else []
            }

        def phase_analyze(self, test_results):
            self._switch_phase(GenerationPhase.ANALYZE)
            print("   [ANALYZE] Analyzing performance metrics...")
            recs = []
            if test_results['latency'] > 150:
                recs.append("optimize_processing")
            if test_results.get('failures'):
                recs.append("improve_error_handling")
            return {"recommendations": recs}

        def phase_apply(self, analysis, context):
            self._switch_phase(GenerationPhase.APPLY)
            print("   [APPLY] Agent applying improvements...")
            changes = agent.process_analysis(analysis)
            
            # Simulate updating blueprint
            v_curr = f"{self.tracker.current_generation}.0"
            v_next = f"{self.tracker.current_generation + 1}.0"
            
            bp_content = bp_manager.load_blueprint("DataProcessor", v_curr) or "Initial Content"
            new_content = bp_content + f"\n    # Update for {v_next}: {', '.join(changes)}"
            bp_manager.save_blueprint("DataProcessor", new_content, v_next)
            
            diff = bp_manager.diff_blueprints("DataProcessor", v_curr, v_next)
            
            return {"changes": changes, "diff_summary": f"Modified {len(changes)} items", "full_diff": diff}

    # 2. Setup Loop
    loop = DemoImprovementLoop(tracker, bp_manager)
    create_initial_blueprint(bp_manager)
    
    # 3. Validating 'Before' state (Gen 0)
    print("\n--- Initial State (Gen 0) ---")
    tracker.finalize_generation(status=ComponentStatus.ALPHA, notes=["Initial setup"])
    
    # 4. Run Generations
    simulated_context = {"env": "prod-sim"}
    
    for i in range(1, 4):
        print(f"\n--- Evolving to Generation {i} ---")
        loop.run_full_cycle(simulated_context)
        
        # Check Tracker History
        latest = tracker.history[-1]
        print(f"   => Generation {latest.gen_id} Completed.")
        print(f"      Status: {latest.status.value}")
        print(f"      Metrics: {len(latest.metrics)} logged")
        print(f"      Changes: {latest.changelog}")

    # 5. Review Full History
    print("\n=== Evolution Summary ===")
    latency_trend = tracker.get_metric_trend("avg_latency_ms")
    print("Latency Trend (ms):")
    for gen, lat in latency_trend:
        print(f"  Gen {gen}: {lat}")

    print("\n=== Demo Complete ===")

if __name__ == "__main__":
    run_demo()
