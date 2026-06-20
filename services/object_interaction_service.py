import uuid
import json
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.models import (
    ProcessAnalysis,
    ScenarioSimulation,
    ScenarioType
)
from app.services.ocel_service import OcelGenerationService
from app.services.object_conformance_service import ObjectConformanceService
from app.services.object_carbon_service import ObjectCarbonAttributionService

class ObjectInteractionService:
    def __init__(self, db: Session):
        self.db = db

    def _calculate_bottleneck_score(self, outbound_degree: int, inbound_degree: int, downstream_objects: int) -> float:
        return (outbound_degree * 0.5) + (inbound_degree * 0.3) + (downstream_objects * 0.2)

    def _severity_to_score(self, severity: str) -> int:
        mapping = {
            "Critical": 100,
            "High": 75,
            "Medium": 50,
            "Low": 25
        }
        return mapping.get(severity, 25)

    def _calculate_risk_score(self, carbon_severity: str, conformance_severity: str) -> float:
        c_score = self._severity_to_score(carbon_severity)
        conf_score = self._severity_to_score(conformance_severity)
        return (c_score * 0.6) + (conf_score * 0.4)

    def generate_and_persist(self, analysis_id: uuid.UUID) -> Dict[str, Any]:
        analysis = self.db.query(ProcessAnalysis).filter(
            ProcessAnalysis.id == analysis_id,
            ProcessAnalysis.is_deleted == False
        ).first()
        if not analysis:
            raise ValueError("Analysis not found")

        # Load Source Snapshots
        ocel_service = OcelGenerationService(self.db)
        latest_ocel = ocel_service.get_latest(analysis_id)
        ocel_data = latest_ocel.get("ocel", {})
        source_ocel_version = latest_ocel.get("ocel_version", 1)

        conf_service = ObjectConformanceService(self.db)
        latest_conf = conf_service.get_latest(analysis_id)
        conf_objects = {o["object_id"]: o for o in latest_conf.get("objects", [])}
        source_conformance_version = latest_conf.get("object_conformance_version", 1)

        carbon_service = ObjectCarbonAttributionService(self.db)
        latest_carbon = carbon_service.get_latest(analysis_id)
        carbon_objects = {o["object_id"]: o for o in latest_carbon.get("objects", [])}
        source_object_carbon_version = latest_carbon.get("object_carbon_version", 1)

        # 1. Build Graph Nodes and Base Graph — OCEL 1.0 dict-keyed format
        nodes = []
        object_map = {}
        raw_objects = ocel_data.get("ocel:objects") or ocel_data.get("objects") or {}
        if isinstance(raw_objects, dict):
            ocel_objects_iter = [
                dict(obj, object_id=obj_id, object_type=obj.get("ocel:type", obj.get("object_type", "")))
                for obj_id, obj in raw_objects.items()
            ]
        else:
            ocel_objects_iter = list(raw_objects)

        for obj in ocel_objects_iter:
            o_id = obj["object_id"]
            o_type = obj.get("object_type") or obj.get("ocel:type", "")
            nodes.append({"object_id": o_id, "object_type": o_type})
            object_map[o_id] = {
                "object_id": o_id,
                "object_type": o_type,
                "inbound_edges": [],
                "outbound_edges": []
            }

        # Determine relationships — OCEL 1.0: relations from ocel:omap per event
        event_objects = {}
        raw_events = ocel_data.get("ocel:events") or ocel_data.get("events") or {}
        if isinstance(raw_events, dict):
            for ev_id, ev in raw_events.items():
                omap = ev.get("ocel:omap", [])
                if omap:
                    event_objects[ev_id] = omap
        else:
            for rel in ocel_data.get("relations", []):
                e_id = rel["event_id"]
                o_id = rel["object_id"]
                event_objects.setdefault(e_id, []).append(o_id)

        hierarchy = {"Supplier": 1, "PurchaseOrder": 2, "Shipment": 3, "Material": 4, "Invoice": 5, "Transport": 6}

        edges = []

        edge_set = set()
        for e_id, obj_ids in event_objects.items():
            if len(obj_ids) > 1:
                # Sort objects in this event by hierarchy to create a directed edge
                objs_with_rank = []
                for oid in obj_ids:
                    if oid in object_map:
                        otype = object_map[oid]["object_type"]
                        objs_with_rank.append((hierarchy.get(otype, 99), oid))
                objs_with_rank.sort(key=lambda x: x[0])
                
                # Create sequential edges
                for i in range(len(objs_with_rank) - 1):
                    src_id = objs_with_rank[i][1]
                    tgt_id = objs_with_rank[i+1][1]
                    
                    if src_id != tgt_id:
                        edge_key = f"{src_id}->{tgt_id}"
                        if edge_key not in edge_set:
                            edge_set.add(edge_key)
                            edges.append({
                                "source_object_id": src_id,
                                "target_object_id": tgt_id,
                                "relationship_type": "depends_on"
                            })
                            object_map[src_id]["outbound_edges"].append(tgt_id)
                            object_map[tgt_id]["inbound_edges"].append(src_id)

        # Build Bottlenecks and Risks
        bottlenecks = []
        risks = []

        # Find downstream count using simple BFS
        def get_downstream_count(start_node):
            visited = set([start_node])
            queue = [start_node]
            while queue:
                curr = queue.pop(0)
                for nxt in object_map[curr]["outbound_edges"]:
                    if nxt not in visited:
                        visited.add(nxt)
                        queue.append(nxt)
            return len(visited) - 1

        for o_id, node_info in object_map.items():
            out_deg = len(node_info["outbound_edges"])
            in_deg = len(node_info["inbound_edges"])
            downstream = get_downstream_count(o_id)
            
            b_score = self._calculate_bottleneck_score(out_deg, in_deg, downstream)
            bottlenecks.append({
                "object_id": o_id,
                "bottleneck_score": round(b_score, 2),
                "outbound_degree": out_deg
            })

            carbon_sev = carbon_objects.get(o_id, {}).get("severity", "Low")
            conf_sev = conf_objects.get(o_id, {}).get("severity", "Low")
            emissions = carbon_objects.get(o_id, {}).get("emissions", 0.0)

            r_score = self._calculate_risk_score(carbon_sev, conf_sev)
            risks.append({
                "object_id": o_id,
                "risk_score": round(r_score, 2),
                "emissions": round(emissions, 2),
                "carbon_severity": carbon_sev,
                "conformance_severity": conf_sev
            })

        # Rank Bottlenecks
        bottlenecks = sorted(bottlenecks, key=lambda x: (-x["bottleneck_score"], -x["outbound_degree"], x["object_id"]))

        # Rank Risks
        risks = sorted(risks, key=lambda x: (-x["risk_score"], -x["emissions"], x["object_id"]))

        # Build Carbon Paths
        # Find all paths up to length 5
        paths = []
        def dfs_paths(curr, path, current_emissions):
            em = carbon_objects.get(curr, {}).get("emissions", 0.0)
            total = current_emissions + em
            
            # Save the path if it has more than 1 node
            if len(path) > 1:
                paths.append({
                    "path": list(path),
                    "total_emissions_kg": round(total, 2)
                })
            
            # Stop if path is too long to prevent combinatorial explosion
            if len(path) >= 5:
                return

            for nxt in object_map[curr]["outbound_edges"]:
                if nxt not in path:
                    path.append(nxt)
                    dfs_paths(nxt, path, total)
                    path.pop()

        # Start DFS from nodes with no inbound edges (roots)
        roots = [oid for oid, info in object_map.items() if len(info["inbound_edges"]) == 0]
        # If there are cycles and no roots, just pick all nodes
        if not roots:
            roots = list(object_map.keys())

        for root in roots:
            dfs_paths(root, [root], 0.0)

        # Sort and take top 10 carbon paths
        paths = sorted(paths, key=lambda x: -x["total_emissions_kg"])[:10]

        # Prepare payload
        max_version = self.db.query(
            func.max(func.json_extract(ScenarioSimulation.simulation_metadata, '$.object_interaction_version'))
        ).filter(
            ScenarioSimulation.analysis_id == analysis_id,
            ScenarioSimulation.scenario_type == ScenarioType.PROCESS_EFFICIENCY.value,
            func.json_extract(ScenarioSimulation.simulation_metadata, '$.simulation_type') == 'object_interaction_analytics',
            ScenarioSimulation.is_deleted == False
        ).scalar()
        next_version = int(max_version) + 1 if max_version is not None else 1

        run_id = str(uuid.uuid4())
        generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Merge scores into nodes
        bottleneck_map = {b["object_id"]: b["bottleneck_score"] for b in bottlenecks}
        risk_map = {r["object_id"]: r["risk_score"] for r in risks}
        
        for n in nodes:
            n["bottleneck_score"] = bottleneck_map.get(n["object_id"], 0.0)
            n["risk_score"] = risk_map.get(n["object_id"], 0.0)

        # Summary Metrics
        high_risk_count = sum(1 for r in risks if r["risk_score"] >= 75)
        highest_risk_obj = risks[0] if risks else {}
        highest_carbon_path = paths[0] if paths else {}

        sim_meta = {
            "simulation_type": "object_interaction_analytics",
            "object_interaction_version": next_version,
            "object_interaction_run_id": run_id,
            "source_ocel_version": source_ocel_version,
            "source_conformance_version": source_conformance_version,
            "source_object_carbon_version": source_object_carbon_version,
            "nodes": nodes,
            "edges": edges,
            "bottlenecks": bottlenecks,
            "risks": risks,
            "carbon_paths": paths,
            "total_relationships": len(edges),
            "bottleneck_count": len([b for b in bottlenecks if b["bottleneck_score"] > 0]),
            "high_risk_objects": high_risk_count,
            "highest_risk_object": highest_risk_obj,
            "highest_carbon_path": highest_carbon_path
        }

        payload_str = json.dumps(sim_meta, sort_keys=True)
        sim_meta["snapshot_hash"] = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
        sim_meta["snapshot_timestamp"] = generated_at

        sim = ScenarioSimulation(
            tenant_id=analysis.tenant_id,
            workspace_id=analysis.workspace_id,
            project_id=analysis.project_id,
            analysis_id=analysis_id,
            scenario_name=f"Object Interaction Analytics v{next_version}",
            scenario_description="Generated Object Interaction Analytics.",
            input_parameters={},
            baseline_emissions=0.0,
            simulated_emissions=0.0,
            emission_reduction=0.0,
            reduction_percentage=0.0,
            scenario_type=ScenarioType.PROCESS_EFFICIENCY.value,
            simulation_confidence_score=100.0,
            simulation_metadata=sim_meta
        )
        self.db.add(sim)
        self.db.commit()

        mapped = sim_meta.copy()
        mapped["interaction_id"] = str(sim.id)
        return mapped

    def get_latest(self, analysis_id: uuid.UUID) -> Dict[str, Any]:
        max_version = self.db.query(
            func.max(func.json_extract(ScenarioSimulation.simulation_metadata, '$.object_interaction_version'))
        ).filter(
            ScenarioSimulation.analysis_id == analysis_id,
            ScenarioSimulation.scenario_type == ScenarioType.PROCESS_EFFICIENCY.value,
            func.json_extract(ScenarioSimulation.simulation_metadata, '$.simulation_type') == 'object_interaction_analytics',
            ScenarioSimulation.is_deleted == False
        ).scalar()

        if max_version is None:
            return self.generate_and_persist(analysis_id)

        sim = self.db.query(ScenarioSimulation).filter(
            ScenarioSimulation.analysis_id == analysis_id,
            ScenarioSimulation.scenario_type == ScenarioType.PROCESS_EFFICIENCY.value,
            func.json_extract(ScenarioSimulation.simulation_metadata, '$.simulation_type') == 'object_interaction_analytics',
            func.json_extract(ScenarioSimulation.simulation_metadata, '$.object_interaction_version') == max_version,
            ScenarioSimulation.is_deleted == False
        ).first()

        mapped = sim.simulation_metadata.copy()
        mapped["interaction_id"] = str(sim.id)
        return mapped

    def get_summary(self, analysis_id: uuid.UUID) -> Dict[str, Any]:
        latest = self.get_latest(analysis_id)
        return {
            "total_relationships": latest.get("total_relationships", 0),
            "bottleneck_count": latest.get("bottleneck_count", 0),
            "high_risk_objects": latest.get("high_risk_objects", 0),
            "highest_risk_object": latest.get("highest_risk_object", {}),
            "highest_carbon_path": latest.get("highest_carbon_path", {})
        }

    def get_bottlenecks(self, analysis_id: uuid.UUID) -> List[Dict[str, Any]]:
        latest = self.get_latest(analysis_id)
        return latest.get("bottlenecks", [])

    def get_risk_paths(self, analysis_id: uuid.UUID) -> List[Dict[str, Any]]:
        latest = self.get_latest(analysis_id)
        return latest.get("carbon_paths", [])

    def get_history(self, analysis_id: uuid.UUID) -> List[Dict[str, Any]]:
        sims = self.db.query(ScenarioSimulation).filter(
            ScenarioSimulation.analysis_id == analysis_id,
            ScenarioSimulation.scenario_type == ScenarioType.PROCESS_EFFICIENCY.value,
            func.json_extract(ScenarioSimulation.simulation_metadata, '$.simulation_type') == 'object_interaction_analytics',
            ScenarioSimulation.is_deleted == False
        ).order_by(
            func.json_extract(ScenarioSimulation.simulation_metadata, '$.object_interaction_version').desc()
        ).all()

        history = []
        for s in sims:
            meta = s.simulation_metadata
            # History endpoints must return metadata only per spec
            history.append({
                "object_interaction_version": meta.get("object_interaction_version"),
                "object_interaction_run_id": meta.get("object_interaction_run_id"),
                "source_ocel_version": meta.get("source_ocel_version"),
                "source_conformance_version": meta.get("source_conformance_version"),
                "source_object_carbon_version": meta.get("source_object_carbon_version"),
                "snapshot_hash": meta.get("snapshot_hash"),
                "snapshot_timestamp": meta.get("snapshot_timestamp"),
                "total_relationships": meta.get("total_relationships"),
                "high_risk_objects": meta.get("high_risk_objects")
            })
        return history

    def get_version(self, analysis_id: uuid.UUID, version: int) -> Dict[str, Any]:
        sim = self.db.query(ScenarioSimulation).filter(
            ScenarioSimulation.analysis_id == analysis_id,
            ScenarioSimulation.scenario_type == ScenarioType.PROCESS_EFFICIENCY.value,
            func.json_extract(ScenarioSimulation.simulation_metadata, '$.simulation_type') == 'object_interaction_analytics',
            func.json_extract(ScenarioSimulation.simulation_metadata, '$.object_interaction_version') == version,
            ScenarioSimulation.is_deleted == False
        ).first()

        if not sim:
            raise FileNotFoundError("Version not found")

        mapped = sim.simulation_metadata.copy()
        mapped["interaction_id"] = str(sim.id)
        return mapped
