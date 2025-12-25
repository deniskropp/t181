
"""
Generational Iteration Framework for Klipper SDK.
This module provides the core classes for tracking, managing, and evolving the Klipper SDK
through its ten generations of capability.

Key Components:
1. GenerationTracker: Core tracking system with version history and metrics.
2. GenerationalImprovementLoop: Systematic evolution engine (Test -> Analyze -> Apply -> Advance -> Validate).
3. GenerationalBlueprintManager: KickLang blueprint versioning system.
"""

import time
import json
import logging
import uuid
import os
from typing import Dict, List, Optional, Any, Tuple, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from datetime import datetime
from pathlib import Path

# Configure logging
logger = logging.getLogger("klipper_sdk.generational")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

# --- Constants & Enums ---

class GenerationPhase(Enum):
    """The five phases of the Generational Improvement Loop."""
    TEST = "TEST"
    ANALYZE = "ANALYZE"
    APPLY = "APPLY"
    ADVANCE = "ADVANCE"
    VALIDATE = "VALIDATE"

class ComponentStatus(Enum):
    ALPHA = "ALPHA"
    BETA = "BETA"
    STABLE = "STABLE"
    DEPRECATED = "DEPRECATED"

# --- Data Structures ---

@dataclass
class GenerationMetric:
    """A single metric data point tracked during a generation."""
    name: str
    value: Union[int, float, str, bool]
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self):
        return asdict(self)

@dataclass
class GenerationArtifact:
    """An artifact produced during a generation (e.g., code, logs, charts)."""
    name: str
    artifact_type: str
    path: str
    hash_sum: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GenerationSnapshot:
    """A complete record of a specific generation of a component."""
    gen_id: int
    component_name: str
    timestamp: str 
    status: ComponentStatus
    metrics: List[GenerationMetric]
    artifacts: Dict[str, GenerationArtifact] = field(default_factory=dict)
    changelog: List[str] = field(default_factory=list)
    parent_gen_id: Optional[int] = None

    def to_json(self) -> str:
        data = asdict(self)
        data['status'] = self.status.value
        # Handle artifacts specifically if needed
        return json.dumps(data, default=str, indent=2)

# --- Core Components ---

class GenerationTracker:
    """
    Core tracking system that maintains the lineage of a component's evolution.
    
    Features:
    - Version history tracking
    - Metric collection per generation
    - Artifact association
    - State persistence (optional via callback)
    """
    
    def __init__(self, component_name: str, persistence_callback: Optional[Callable[[Dict], None]] = None):
        self.component_name = component_name
        self.current_generation = 0
        self.history: List[GenerationSnapshot] = []
        self._current_metrics: List[GenerationMetric] = []
        self._current_artifacts: Dict[str, GenerationArtifact] = {}
        self._persistence_callback = persistence_callback
        self.logger = logging.getLogger(f"klipper_sdk.tracker.{component_name}")

    def start_next_generation(self) -> int:
        """ Prepares the tracker for the next generation. """
        self.current_generation += 1
        self._current_metrics = []
        self._current_artifacts = {}
        self.logger.info(f"Initializing Generation {self.current_generation} for {self.component_name}")
        return self.current_generation

    def log_metric(self, name: str, value: Any, tags: Dict[str, str] = None):
        """ Records a metric for the current generation. """
        metric = GenerationMetric(name=name, value=value, tags=tags or {})
        self._current_metrics.append(metric)
        self.logger.debug(f"Metric logged: {name}={value}")

    def register_artifact(self, name: str, path: str, type_hint: str = "file"):
        """ Registers an artifact produced in this generation. """
        # In a real impl, we might calculate hash here
        import hashlib
        checksum = "unknown"
        if os.path.exists(path) and os.path.isfile(path):
            with open(path, "rb") as f:
                checksum = hashlib.md5(f.read()).hexdigest()
        
        artifact = GenerationArtifact(
            name=name,
            artifact_type=type_hint,
            path=path,
            hash_sum=checksum
        )
        self._current_artifacts[name] = artifact
        self.logger.info(f"Artifact registered: {name} ({path})")

    def finalize_generation(self, status: ComponentStatus = ComponentStatus.STABLE, notes: List[str] = None) -> GenerationSnapshot:
        """ Cements the current generation into history. """
        snapshot = GenerationSnapshot(
            gen_id=self.current_generation,
            component_name=self.component_name,
            timestamp=datetime.now().isoformat(),
            status=status,
            metrics=list(self._current_metrics),
            artifacts=dict(self._current_artifacts),
            changelog=notes or [],
            parent_gen_id=self.history[-1].gen_id if self.history else None
        )
        self.history.append(snapshot)
        
        if self._persistence_callback:
            self._persistence_callback(json.loads(snapshot.to_json()))
            
        self.logger.info(f"Finalized Generation {self.current_generation}. Total metrics: {len(snapshot.metrics)}")
        return snapshot

    def get_metric_trend(self, metric_name: str) -> List[Tuple[int, Any]]:
        """ Returns a list of (gen_id, value) for a specific metric across history. """
        trend = []
        for snap in self.history:
            for m in snap.metrics:
                if m.name == metric_name:
                    trend.append((snap.gen_id, m.value))
                    break # assume one value per gen per metric name for simplicity
        return trend


class GenerationalBlueprintManager:
    """
    Manages KickLang blueprints, supporting versioning, diffing, and rollback.
    
    Blueprints are the recipes or 'DNA' for a generation.
    """
    
    def __init__(self, storage_root: str = "./blueprints"):
        self.storage_root = Path(storage_root)
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self.blueprints: Dict[str, List[GenerationSnapshot]] = {}
        self.logger = logging.getLogger("klipper_sdk.blueprints")

    def save_blueprint(self, name: str, content: str, version_tag: str) -> str:
        """ Saves a blueprint string to disk and records it. """
        filename = f"{name}_v{version_tag}.kl"
        path = self.storage_root / filename
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        
        self.logger.info(f"Saved blueprint {name} version {version_tag} to {path}")
        return str(path)

    def load_blueprint(self, name: str, version_tag: str) -> Optional[str]:
        """ Loads a specific version of a blueprint. """
        filename = f"{name}_v{version_tag}.kl"
        path = self.storage_root / filename
        if path.exists():
            return path.read_text(encoding="utf-8")
        self.logger.warning(f"Blueprint not found: {path}")
        return None

    def diff_blueprints(self, name: str, v1: str, v2: str) -> List[str]:
        """ proper diffing of two blueprint versions. """
        b1 = self.load_blueprint(name, v1)
        b2 = self.load_blueprint(name, v2)
        
        if b1 is None or b2 is None:
            return ["Error: One or both versions not found."]
            
        import difflib
        diff = difflib.unified_diff(
            b1.splitlines(), 
            b2.splitlines(), 
            fromfile=f"{name}:{v1}", 
            tofile=f"{name}:{v2}"
        )
        return list(diff)


class GenerationalImprovementLoop:
    """
    Driver for the 5-phase systematic evolution cycle.
    
    Cycles through:
    1. TEST: Check current capabilities and establish baseline.
    2. ANALYZE: Review test results and identify gaps.
    3. APPLY: Execute changes (refactoring, new features).
    4. ADVANCE: Commit changes to a new generation.
    5. VALIDATE: Ensure the new generation meets criteria.
    """
    
    def __init__(self, 
                 tracker: GenerationTracker, 
                 blueprint_manager: GenerationalBlueprintManager,
                 executor_agent: Any = None):
        self.tracker = tracker
        self.blueprint_manager = blueprint_manager
        self.executor = executor_agent # Placeholder for an AI agent interface
        self.current_phase = GenerationPhase.TEST
        self.logger = logging.getLogger("klipper_sdk.loop")

    def run_full_cycle(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """ Runs all 5 phases in order. """
        self.logger.info("Initiating Full Generational Cycle")
        results = {}
        
        # 1. TEST
        results['test'] = self.phase_test(context)
        if not results['test'].get('success', False):
             self.logger.warning("Test phase failed, aborting cycle.")
             return results

        # 2. ANALYZE
        results['analyze'] = self.phase_analyze(results['test'])
        
        # 3. APPLY
        results['apply'] = self.phase_apply(results['analyze'], context)
        
        # 4. ADVANCE
        results['advance'] = self.phase_advance(results['apply'])
        
        # 5. VALIDATE
        results['validate'] = self.phase_validate(results['advance'])
        
        self.logger.info("Cycle Complete")
        return results

    def phase_test(self, context: Dict) -> Dict:
        self._switch_phase(GenerationPhase.TEST)
        # In a real scenario, this would trigger a test suite
        # using the context to determine target tests.
        self.tracker.log_metric("phase_test_duration_ms", 120) 
        return {"success": True, "coverage": 0.88, "failures": []}

    def phase_analyze(self, test_results: Dict) -> Dict:
        self._switch_phase(GenerationPhase.ANALYZE)
        # Analyze failures or performance bottlenecks
        recommendations = ["optimize_query_speed"] if test_results.get("coverage") < 0.9 else []
        return {"recommendations": recommendations, "priority": "HIGH"}

    def phase_apply(self, analysis: Dict, context: Dict) -> Dict:
        self._switch_phase(GenerationPhase.APPLY)
        # Apply the changes. 
        # This is where the Agent would be invoked to write code.
        changes_applied = ["Ran optimizer"]
        return {"changes": changes_applied, "diff_summary": "+5 lines, -2 lines"}

    def phase_advance(self, apply_results: Dict) -> Dict:
        self._switch_phase(GenerationPhase.ADVANCE)
        # Increment generation
        gen_id = self.tracker.start_next_generation()
        # Log everything
        for change in apply_results.get("changes", []):
            self.tracker.log_metric("applied_change", 1, tags={"desc": change})
        
        snapshot = self.tracker.finalize_generation(notes=apply_results.get("changes"))
        return {"gen_id": gen_id, "snapshot_id": str(snapshot.timestamp)}

    def phase_validate(self, advance_results: Dict) -> Dict:
        self._switch_phase(GenerationPhase.VALIDATE)
        # Regression testing
        validated = True
        self.tracker.log_metric("validation_success", 1 if validated else 0)
        return {"validated": validated, "score": 100}

    def _switch_phase(self, phase: GenerationPhase):
        self.current_phase = phase
        self.logger.info(f"Entering Phase: {phase.value}")


# --- Utility Functions ---

def create_default_pipeline(name: str, export_path: str = "./data"):
    """ Factory to create a standard loop setup. """
    tracker = GenerationTracker(name)
    bp_manager = GenerationalBlueprintManager(os.path.join(export_path, "blueprints"))
    return GenerationalImprovementLoop(tracker, bp_manager)

if __name__ == "__main__":
    # Simple self-test if run directly
    print("Initializing Generational Framework...")
    pipeline = create_default_pipeline("DemoComponent")
    result = pipeline.run_full_cycle({"target": "core_module"})
    print(f"Cycle Result: {json.dumps(result, indent=2)}")
