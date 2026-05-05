"""
SAIS n-signal diagnostic and attention engine.

This module is the executable foundation for the SAIS methodology claim:
field signals should be interpreted as condition evidence, not displayed only as
isolated sensor charts.

The engine has two complementary layers:

1. Attention aggregates
   Curated combinations of signals that direct operator attention to a section
   of the farm before the system makes a strong diagnostic claim.

2. Hypothesis-driven diagnostics
   Ranked interpretations that explain what a symptom or signal pattern most
   likely means, with supporting evidence, missing signals, confidence, and a
   suggested inspection.

The design is intentionally rule-based, transparent, and operator-facing.
It does not prescribe irreversible actions. It explains why a section deserves
attention and what evidence supports each interpretation.

Core chain:

    signals -> section context -> attention aggregates -> candidate meanings
            -> evidence score -> ranked interpretations -> confidence
            -> suggested inspection
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .graph import FarmGraph


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class FarmSignal:
    """Normalized signal used by the diagnostic engine."""

    domain: str
    name: str
    value: Any
    unit: Optional[str] = None
    timestamp: Optional[str] = None
    source_id: Optional[str] = None
    confidence: str = "medium"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalRequirement:
    """Defines a signal that improves confidence for an interpretation."""

    domain: str
    name_contains: Sequence[str]
    required: bool = False


@dataclass
class AttentionAggregateRule:
    """
    A curated multi-signal combination that directs attention.

    Attention aggregates are not final diagnoses. They are the farm equivalent
    of abnormal vital-sign clusters: combinations worth looking at because they
    may reveal a condition affecting soil, water, plants, animals, infrastructure,
    or source trust.
    """

    aggregate_id: str
    domain: str
    title: str
    description: str
    section_scope: Sequence[str]
    evidence_terms: Sequence[str]
    minimum_score: float
    suggested_focus: str


@dataclass
class AttentionAggregate:
    """One attention-directing signal combination detected for a section."""

    aggregate_id: str
    domain: str
    title: str
    score: float
    priority: str
    description: str
    supporting_evidence: List[str]
    suggested_focus: str


@dataclass
class InterpretationRule:
    """Transparent rule for mapping signal combinations to farm meaning."""

    interpretation_id: str
    domain: str
    section_scope: Sequence[str]
    symptom: str
    description: str
    requirements: Sequence[SignalRequirement]
    evidence_terms: Sequence[str]
    suggested_inspection: str


@dataclass
class RankedInterpretation:
    """One possible meaning of a signal combination."""

    interpretation_id: str
    domain: str
    symptom: str
    score: float
    confidence: str
    description: str
    supporting_evidence: List[str]
    missing_signals: List[str]
    suggested_inspection: str


@dataclass
class DiagnosticReport:
    """Diagnostic and attention result for one farm section."""

    farm_id: str
    section: Dict[str, Optional[str]]
    signal_count: int
    status: str
    confidence: str
    attention_aggregates: List[AttentionAggregate]
    ranked_interpretations: List[RankedInterpretation]
    signals_used: List[FarmSignal]
    missing_signals: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "farm_id": self.farm_id,
            "section": self.section,
            "signal_count": self.signal_count,
            "status": self.status,
            "confidence": self.confidence,
            "attention_aggregates": [asdict(item) for item in self.attention_aggregates],
            "ranked_interpretations": [asdict(item) for item in self.ranked_interpretations],
            "signals_used": [asdict(item) for item in self.signals_used],
            "missing_signals": self.missing_signals,
        }


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class FarmDiagnosticEngine:
    """
    General n-signal attention and diagnostic engine for SAIS farm sections.

    Use `diagnose_section` for the normal cross-board workflow. It gathers any
    available combination of signals for the section, emits attention aggregates,
    then ranks possible interpretations.
    """

    def __init__(self, graph: FarmGraph):
        self.graph = graph
        self.rules = self.default_rules()
        self.attention_rules = self.default_attention_aggregate_rules()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def diagnose_section(
        self,
        farm_id: str,
        field_id: Optional[str] = None,
        zone_id: Optional[str] = None,
        paddock_id: Optional[str] = None,
        asset_id: Optional[str] = None,
        minimum_signals: int = 3,
        lookback_hours: int = 72,
    ) -> DiagnosticReport:
        """
        Diagnose a farm section from any available combination of recent signals.

        This is the cross-board function: water, soil, weather, plant, grazing,
        livestock, infrastructure, and source-health signals are normalized into
        one evidence set.
        """

        signals = self.collect_section_signals(
            farm_id=farm_id,
            field_id=field_id,
            zone_id=zone_id,
            paddock_id=paddock_id,
            asset_id=asset_id,
            lookback_hours=lookback_hours,
        )

        section = {
            "field_id": field_id,
            "zone_id": zone_id,
            "paddock_id": paddock_id,
            "asset_id": asset_id,
        }

        attention = self.compute_attention_aggregates(signals, section)

        if len(signals) < minimum_signals:
            return DiagnosticReport(
                farm_id=farm_id,
                section=section,
                signal_count=len(signals),
                status="insufficient_signals",
                confidence="low",
                attention_aggregates=attention,
                ranked_interpretations=[],
                signals_used=signals,
                missing_signals=[
                    f"minimum {minimum_signals} recent signals required; found {len(signals)}"
                ],
            )

        ranked = self.interpret_signals(signals, section)
        top_confidence = ranked[0].confidence if ranked else (attention[0].priority if attention else "unknown")
        status = self.status_from_attention_and_ranked(attention, ranked)
        missing = sorted({m for item in ranked[:3] for m in item.missing_signals})

        return DiagnosticReport(
            farm_id=farm_id,
            section=section,
            signal_count=len(signals),
            status=status,
            confidence=top_confidence,
            attention_aggregates=attention,
            ranked_interpretations=ranked,
            signals_used=signals,
            missing_signals=missing,
        )

    def diagnose_low_soil_moisture(
        self,
        farm_id: str,
        field_id: Optional[str] = None,
        zone_id: Optional[str] = None,
        paddock_id: Optional[str] = None,
    ) -> DiagnosticReport:
        """Convenience wrapper for the first explicit symptom family."""

        report = self.diagnose_section(
            farm_id=farm_id,
            field_id=field_id,
            zone_id=zone_id,
            paddock_id=paddock_id,
            minimum_signals=2,
        )
        report.ranked_interpretations = [
            item for item in report.ranked_interpretations
            if item.symptom in {"low_soil_moisture", "poor_water_retention", "source_fault"}
        ]
        report.attention_aggregates = [
            item for item in report.attention_aggregates
            if item.domain in {"soil_water", "soil_plant_animal", "source_health"}
        ]
        report.status = self.status_from_attention_and_ranked(
            report.attention_aggregates,
            report.ranked_interpretations,
        )
        report.confidence = self.top_confidence(report.attention_aggregates, report.ranked_interpretations)
        return report

    # ------------------------------------------------------------------
    # Attention aggregates
    # ------------------------------------------------------------------

    def compute_attention_aggregates(
        self,
        signals: Sequence[FarmSignal],
        section: Dict[str, Optional[str]],
    ) -> List[AttentionAggregate]:
        """
        Return curated multi-signal combinations that deserve attention.

        These aggregates are intentionally not unconstrained combinations.
        They are named, reviewed combinations that encode agronomic meaning.
        This avoids combinatorial noise while still letting any available set of
        signals contribute to the operating picture.
        """

        aggregates: List[AttentionAggregate] = []
        for rule in self.attention_rules:
            if not self.rule_applies_to_section_scope(rule.section_scope, section):
                continue

            score = 0.0
            evidence: List[str] = []
            for term in rule.evidence_terms:
                term_score, term_evidence = self.evaluate_term(term, signals)
                score += term_score
                evidence.extend(term_evidence)

            score = max(0.0, min(1.0, score))
            if score >= rule.minimum_score:
                aggregates.append(
                    AttentionAggregate(
                        aggregate_id=rule.aggregate_id,
                        domain=rule.domain,
                        title=rule.title,
                        score=round(score, 3),
                        priority=self.priority_from_score(score),
                        description=rule.description,
                        supporting_evidence=evidence,
                        suggested_focus=rule.suggested_focus,
                    )
                )

        aggregates.sort(key=lambda item: item.score, reverse=True)
        return aggregates[:8]

    def default_attention_aggregate_rules(self) -> List[AttentionAggregateRule]:
        return [
            AttentionAggregateRule(
                aggregate_id="attention_water_capture_gap",
                domain="soil_water",
                title="Water capture gap",
                description="Water input appears present, but the soil-water signal suggests weak capture or retention.",
                section_scope=["field", "zone", "paddock"],
                evidence_terms=["low_soil_moisture", "recent_rainfall", "runoff_context"],
                minimum_score=0.42,
                suggested_focus="Inspect infiltration, cover, crusting, compaction, and runoff pathways.",
            ),
            AttentionAggregateRule(
                aggregate_id="attention_atmospheric_drydown_pressure",
                domain="weather_soil",
                title="Atmospheric drydown pressure",
                description="Weather signals suggest the section may be losing water through heat, humidity deficit, or wind-driven drydown.",
                section_scope=["field", "zone", "paddock"],
                evidence_terms=["low_soil_moisture", "high_drydown_weather"],
                minimum_score=0.32,
                suggested_focus="Check plant stress, shade, water availability, and grazing timing.",
            ),
            AttentionAggregateRule(
                aggregate_id="attention_grazing_recovery_pressure",
                domain="soil_plant_animal",
                title="Grazing recovery pressure",
                description="Plant recovery, cover, soil moisture, and grazing signals suggest recovery may be under pressure.",
                section_scope=["paddock"],
                evidence_terms=["low_soil_moisture", "low_cover_or_recovery", "recent_grazing_pressure"],
                minimum_score=0.42,
                suggested_focus="Inspect residual cover, grazing duration, rest interval, and recovery before re-entry.",
            ),
            AttentionAggregateRule(
                aggregate_id="attention_productive_uptake_watch",
                domain="soil_plant",
                title="Productive uptake watch",
                description="Low soil moisture coincides with strong plant response, suggesting water may be moving through productive growth rather than immediate failure.",
                section_scope=["zone", "paddock"],
                evidence_terms=["low_soil_moisture", "strong_plant_response"],
                minimum_score=0.38,
                suggested_focus="Verify plant vigor and avoid overcorrecting unless stress indicators appear.",
            ),
            AttentionAggregateRule(
                aggregate_id="attention_soil_function_watch",
                domain="soil_function",
                title="Soil function watch",
                description="Infiltration or soil-function signals suggest reduced water entry or biological function.",
                section_scope=["paddock"],
                evidence_terms=["low_infiltration", "low_cover_or_recovery"],
                minimum_score=0.30,
                suggested_focus="Inspect aggregation, compaction, cover, residue, biological activity, and infiltration.",
            ),
            AttentionAggregateRule(
                aggregate_id="attention_water_asset_risk",
                domain="water_infrastructure",
                title="Water asset risk",
                description="Water level, pump, pressure, or source-health signals suggest a water asset may need inspection.",
                section_scope=["asset", "farm"],
                evidence_terms=["water_asset_low", "pump_or_pressure_fault", "source_stale_or_faulty"],
                minimum_score=0.30,
                suggested_focus="Check tank level, pump power/current, pressure, leaks, telemetry freshness, and animal access.",
            ),
            AttentionAggregateRule(
                aggregate_id="attention_source_trust_gap",
                domain="source_health",
                title="Source trust gap",
                description="Telemetry freshness, battery, or node-health signals suggest the data source may be less trustworthy.",
                section_scope=["field", "zone", "paddock", "asset", "farm"],
                evidence_terms=["source_stale_or_faulty"],
                minimum_score=0.20,
                suggested_focus="Check node battery, connectivity, last-seen time, sensor placement, and calibration.",
            ),
        ]

    # ------------------------------------------------------------------
    # Signal collection
    # ------------------------------------------------------------------

    def collect_section_signals(
        self,
        farm_id: str,
        field_id: Optional[str],
        zone_id: Optional[str],
        paddock_id: Optional[str],
        asset_id: Optional[str],
        lookback_hours: int,
    ) -> List[FarmSignal]:
        signals: List[FarmSignal] = []
        since = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)

        signals.extend(self.collect_observation_signals(farm_id, field_id, zone_id, since))
        signals.extend(self.collect_plant_signals(farm_id, paddock_id, since))
        signals.extend(self.collect_soil_test_signals(farm_id, paddock_id, since))
        signals.extend(self.collect_grazing_signals(farm_id, paddock_id, since))
        signals.extend(self.collect_infrastructure_signals(farm_id, asset_id))
        signals.extend(self.collect_source_health_signals(farm_id, field_id, zone_id, paddock_id, asset_id))
        signals.extend(self.collect_geospatial_context(farm_id))

        return signals

    def collect_observation_signals(
        self,
        farm_id: str,
        field_id: Optional[str],
        zone_id: Optional[str],
        since: datetime,
    ) -> List[FarmSignal]:
        cursor = self.graph.storage.conn.cursor()
        where = ["farm_id = ?", "timestamp > ?"]
        params: List[Any] = [farm_id, since.isoformat()]
        if field_id:
            where.append("field_id = ?")
            params.append(field_id)
        if zone_id:
            where.append("zone_id = ?")
            params.append(zone_id)

        cursor.execute(
            f"""
            SELECT node_id, timestamp, measurement_id, value, layer, payload_json
            FROM observations
            WHERE {' AND '.join(where)}
            ORDER BY timestamp DESC
            LIMIT 100
            """,
            params,
        )

        signals: List[FarmSignal] = []
        for node_id, timestamp, measurement_id, value, layer, payload_json in cursor.fetchall():
            payload = self.safe_json(payload_json)
            signals.append(
                FarmSignal(
                    domain=self.domain_from_measurement(layer, measurement_id),
                    name=measurement_id,
                    value=value,
                    unit=payload.get("unit"),
                    timestamp=timestamp,
                    source_id=node_id,
                    confidence=payload.get("confidence", "medium"),
                    metadata=payload,
                )
            )
        return signals

    def collect_plant_signals(self, farm_id: str, paddock_id: Optional[str], since: datetime) -> List[FarmSignal]:
        if not paddock_id:
            return []
        cursor = self.graph.storage.conn.cursor()
        cursor.execute(
            """
            SELECT timestamp, forage_mass, cover, height, recovery_score
            FROM plant_observations
            WHERE farm_id = ? AND paddock_id = ? AND timestamp > ?
            ORDER BY timestamp DESC LIMIT 5
            """,
            (farm_id, paddock_id, since.isoformat()),
        )
        signals: List[FarmSignal] = []
        for timestamp, forage_mass, cover, height, recovery_score in cursor.fetchall():
            values = {
                "plant.forage_mass_kg_ha": (forage_mass, "kg_dm_ha"),
                "plant.cover_percent": (cover, "%"),
                "plant.height_cm": (height, "cm"),
                "plant.recovery_score": (recovery_score, "score"),
            }
            for name, (value, unit) in values.items():
                if value is not None:
                    signals.append(FarmSignal("plant", name, value, unit, timestamp, paddock_id))
        return signals

    def collect_soil_test_signals(self, farm_id: str, paddock_id: Optional[str], since: datetime) -> List[FarmSignal]:
        if not paddock_id:
            return []
        cursor = self.graph.storage.conn.cursor()
        cursor.execute(
            """
            SELECT timestamp, infiltration_mm_hr
            FROM soil_observations
            WHERE farm_id = ? AND paddock_id = ? AND timestamp > ?
            ORDER BY timestamp DESC LIMIT 5
            """,
            (farm_id, paddock_id, since.isoformat()),
        )
        return [
            FarmSignal("soil", "soil.infiltration_mm_hr", row[1], "mm_hr", row[0], paddock_id)
            for row in cursor.fetchall()
            if row[1] is not None
        ]

    def collect_grazing_signals(self, farm_id: str, paddock_id: Optional[str], since: datetime) -> List[FarmSignal]:
        if not paddock_id:
            return []
        cursor = self.graph.storage.conn.cursor()
        cursor.execute(
            """
            SELECT started_at, ended_at, animal_count
            FROM grazing_events
            WHERE farm_id = ? AND paddock_id = ? AND started_at > ?
            ORDER BY started_at DESC LIMIT 5
            """,
            (farm_id, paddock_id, since.isoformat()),
        )
        signals: List[FarmSignal] = []
        now = datetime.now(timezone.utc)
        for started_at, ended_at, animal_count in cursor.fetchall():
            start = self.parse_time(started_at)
            days_since = (now - start).days if start else None
            active = ended_at is None
            signals.append(FarmSignal("animal", "grazing.animal_count", animal_count or 0, "count", started_at, paddock_id))
            signals.append(FarmSignal("animal", "grazing.active", 1 if active else 0, "bool", started_at, paddock_id))
            if days_since is not None:
                signals.append(FarmSignal("animal", "grazing.days_since", days_since, "days", started_at, paddock_id))
        return signals

    def collect_infrastructure_signals(self, farm_id: str, asset_id: Optional[str]) -> List[FarmSignal]:
        cursor = self.graph.storage.conn.cursor()
        if asset_id:
            cursor.execute(
                "SELECT id, asset_type, status, payload_json FROM infrastructure_assets WHERE farm_id = ? AND id = ?",
                (farm_id, asset_id),
            )
        else:
            cursor.execute(
                "SELECT id, asset_type, status, payload_json FROM infrastructure_assets WHERE farm_id = ? LIMIT 25",
                (farm_id,),
            )
        signals: List[FarmSignal] = []
        for row_id, asset_type, status, payload_json in cursor.fetchall():
            payload = self.safe_json(payload_json)
            signals.append(
                FarmSignal(
                    "infrastructure",
                    f"infrastructure.{asset_type}.status".lower(),
                    status,
                    None,
                    payload.get("timestamp"),
                    row_id,
                    payload.get("confidence", "medium"),
                    payload,
                )
            )
        return signals

    def collect_source_health_signals(
        self,
        farm_id: str,
        field_id: Optional[str],
        zone_id: Optional[str],
        paddock_id: Optional[str],
        asset_id: Optional[str],
    ) -> List[FarmSignal]:
        cursor = self.graph.storage.conn.cursor()
        where = ["status = 'accepted'"]
        params: List[Any] = []
        if farm_id:
            where.append("farm_id = ?")
            params.append(farm_id)
        if field_id:
            where.append("field_id = ?")
            params.append(field_id)
        if zone_id:
            where.append("zone_id = ?")
            params.append(zone_id)
        if paddock_id:
            where.append("paddock_id = ?")
            params.append(paddock_id)
        if asset_id:
            where.append("asset_id = ?")
            params.append(asset_id)

        cursor.execute(
            f"SELECT id, last_seen, payload_json FROM node_registry WHERE {' AND '.join(where)} LIMIT 25",
            params,
        )
        now = datetime.now(timezone.utc)
        signals: List[FarmSignal] = []
        for node_id, last_seen, payload_json in cursor.fetchall():
            seen = self.parse_time(last_seen)
            if seen:
                age_min = round((now - seen).total_seconds() / 60.0, 1)
                signals.append(FarmSignal("source_health", "source.last_seen_minutes", age_min, "min", last_seen, node_id))
            payload = self.safe_json(payload_json)
            for key in ("battery_v", "battery_voltage", "rssi", "wifi_rssi_dbm"):
                if key in payload:
                    signals.append(FarmSignal("source_health", f"source.{key}", payload[key], None, last_seen, node_id, metadata=payload))
        return signals

    def collect_geospatial_context(self, farm_id: str) -> List[FarmSignal]:
        signals: List[FarmSignal] = []
        for edge in self.graph.get_edges(source_id=farm_id, edge_type="HAS_LAYER"):
            layer_id = edge.get("target_id", "")
            lower = layer_id.lower()
            if "runoff" in lower or "slope" in lower or "flow" in lower or "soil" in lower:
                signals.append(FarmSignal("geospatial", f"layer.{layer_id}", 1, "present", None, layer_id))
        return signals

    # ------------------------------------------------------------------
    # Interpretation
    # ------------------------------------------------------------------

    def interpret_signals(self, signals: Sequence[FarmSignal], section: Dict[str, Optional[str]]) -> List[RankedInterpretation]:
        ranked: List[RankedInterpretation] = []
        for rule in self.rules:
            if not self.rule_applies_to_section_scope(rule.section_scope, section):
                continue
            score, supporting, missing = self.score_rule(rule, signals)
            if score <= 0:
                continue
            ranked.append(
                RankedInterpretation(
                    interpretation_id=rule.interpretation_id,
                    domain=rule.domain,
                    symptom=rule.symptom,
                    score=round(score, 3),
                    confidence=self.confidence_from_score(score, supporting, missing),
                    description=rule.description,
                    supporting_evidence=supporting,
                    missing_signals=missing,
                    suggested_inspection=rule.suggested_inspection,
                )
            )
        ranked.sort(key=lambda item: item.score, reverse=True)
        return ranked[:10]

    def score_rule(self, rule: InterpretationRule, signals: Sequence[FarmSignal]) -> Tuple[float, List[str], List[str]]:
        supporting: List[str] = []
        missing: List[str] = []
        score = 0.0

        for req in rule.requirements:
            matched = self.find_matching_signals(signals, req)
            label = f"{req.domain}:{'/'.join(req.name_contains)}"
            if matched:
                score += 0.15 * min(2, len(matched))
                for signal in matched[:3]:
                    supporting.append(f"{signal.name}={signal.value}{(' ' + signal.unit) if signal.unit else ''}")
            elif req.required:
                missing.append(label)
                score -= 0.15
            else:
                missing.append(label)

        for term in rule.evidence_terms:
            term_score, term_evidence = self.evaluate_term(term, signals)
            score += term_score
            supporting.extend(term_evidence)

        score = max(0.0, min(1.0, score))
        return score, supporting, missing

    def evaluate_term(self, term: str, signals: Sequence[FarmSignal]) -> Tuple[float, List[str]]:
        """Evaluate reusable diagnostic evidence terms."""

        evidence: List[str] = []

        if term == "low_soil_moisture":
            for signal in signals:
                if self.has_name(signal, ["moisture", "vwc"]):
                    value = self.float_value(signal.value)
                    if value is not None and value < 0.25:
                        return 0.25, [f"low soil moisture detected: {signal.name}={value}"]
            return 0.0, []

        if term == "recent_rainfall":
            total = sum(self.float_value(s.value) or 0.0 for s in signals if self.has_name(s, ["rain", "rainfall"]))
            if total > 1.0:
                return 0.20, [f"recent rainfall detected: {round(total, 2)}"]
            return 0.0, []

        if term == "high_drydown_weather":
            temp = self.first_float(signals, ["temperature", "air_temperature"])
            rh = self.first_float(signals, ["humidity", "relative_humidity"])
            score = 0.0
            if temp is not None and temp >= 32:
                score += 0.12
                evidence.append(f"high temperature: {temp}")
            if rh is not None and rh <= 45:
                score += 0.10
                evidence.append(f"low humidity: {rh}")
            return score, evidence

        if term == "runoff_context":
            for signal in signals:
                if signal.domain == "geospatial" and self.has_name(signal, ["runoff", "slope", "flow"]):
                    return 0.18, [f"runoff context available: {signal.name}"]
            return 0.0, []

        if term == "low_infiltration":
            value = self.first_float(signals, ["infiltration"])
            if value is not None and value < 15:
                return 0.25, [f"low infiltration: {value} mm/hr"]
            if value is not None and value < 25:
                return 0.12, [f"marginal infiltration: {value} mm/hr"]
            return 0.0, []

        if term == "low_cover_or_recovery":
            cover = self.first_float(signals, ["cover_percent", "cover"])
            recovery = self.first_float(signals, ["recovery_score"])
            score = 0.0
            if cover is not None and cover < 50:
                score += 0.18
                evidence.append(f"low cover: {cover}%")
            if recovery is not None and recovery <= 2:
                score += 0.18
                evidence.append(f"low recovery score: {recovery}")
            return score, evidence

        if term == "recent_grazing_pressure":
            days = self.first_float(signals, ["grazing.days_since"])
            active = self.first_float(signals, ["grazing.active"])
            if active == 1:
                return 0.20, ["active grazing recorded"]
            if days is not None and days < 14:
                return 0.18, [f"recent grazing: {days} days since event"]
            return 0.0, []

        if term == "strong_plant_response":
            cover = self.first_float(signals, ["cover_percent", "cover"])
            recovery = self.first_float(signals, ["recovery_score"])
            score = 0.0
            if cover is not None and cover >= 75:
                score += 0.18
                evidence.append(f"strong cover: {cover}%")
            if recovery is not None and recovery >= 4:
                score += 0.18
                evidence.append(f"strong recovery score: {recovery}")
            return score, evidence

        if term == "source_stale_or_faulty":
            age = self.first_float(signals, ["source.last_seen_minutes"])
            battery = self.first_float(signals, ["battery"])
            score = 0.0
            if age is not None and age > 240:
                score += 0.25
                evidence.append(f"source telemetry stale: {age} minutes")
            if battery is not None and battery < 3.5:
                score += 0.20
                evidence.append(f"low battery: {battery}")
            return score, evidence

        if term == "water_asset_low":
            for signal in signals:
                if self.has_name(signal, ["tank.level", "level_percent"]):
                    value = self.float_value(signal.value)
                    if value is not None and value < 30:
                        return 0.30, [f"tank level low: {value}%"]
            return 0.0, []

        if term == "pump_or_pressure_fault":
            pump = self.first_float(signals, ["pump"])
            pressure = self.first_float(signals, ["pressure"])
            score = 0.0
            if pump is not None and pump <= 0:
                score += 0.15
                evidence.append("pump signal indicates off or no current")
            if pressure is not None and pressure <= 0:
                score += 0.20
                evidence.append("water pressure is low or absent")
            return score, evidence

        return 0.0, []

    # ------------------------------------------------------------------
    # Default interpretation rules
    # ------------------------------------------------------------------

    def default_rules(self) -> List[InterpretationRule]:
        return [
            InterpretationRule(
                interpretation_id="soil_water_drought_stress",
                domain="soil_water",
                section_scope=["field", "zone", "paddock"],
                symptom="low_soil_moisture",
                description="Low soil moisture is most consistent with drought or atmospheric drydown pressure.",
                requirements=[
                    SignalRequirement("soil", ["moisture", "vwc"], required=True),
                    SignalRequirement("weather", ["temperature"]),
                    SignalRequirement("weather", ["humidity"]),
                    SignalRequirement("weather", ["rain"]),
                ],
                evidence_terms=["low_soil_moisture", "high_drydown_weather"],
                suggested_inspection="Check plant stress, water availability, shade, and grazing timing before assuming soil-function failure.",
            ),
            InterpretationRule(
                interpretation_id="soil_water_runoff_or_poor_infiltration",
                domain="soil_water",
                section_scope=["field", "zone", "paddock"],
                symptom="poor_water_retention",
                description="Moisture remains low despite water input, suggesting runoff, crusting, compaction, or poor infiltration.",
                requirements=[
                    SignalRequirement("soil", ["moisture", "vwc"], required=True),
                    SignalRequirement("water", ["rain"], required=False),
                    SignalRequirement("geospatial", ["runoff", "slope", "flow"], required=False),
                    SignalRequirement("soil", ["infiltration"], required=False),
                ],
                evidence_terms=["low_soil_moisture", "recent_rainfall", "runoff_context", "low_infiltration"],
                suggested_inspection="Inspect soil cover, crusting, compaction, slope pathways, and infiltration after rainfall.",
            ),
            InterpretationRule(
                interpretation_id="soil_plant_low_cover_or_overgrazing",
                domain="soil_plant_animal",
                section_scope=["paddock"],
                symptom="low_soil_moisture",
                description="Low moisture may be tied to grazing pressure, low cover, and poor pasture recovery.",
                requirements=[
                    SignalRequirement("soil", ["moisture", "vwc"], required=True),
                    SignalRequirement("plant", ["cover", "recovery"], required=False),
                    SignalRequirement("animal", ["grazing"], required=False),
                ],
                evidence_terms=["low_soil_moisture", "low_cover_or_recovery", "recent_grazing_pressure"],
                suggested_inspection="Check residual height, recovery score, ground cover, grazing duration, and rest interval.",
            ),
            InterpretationRule(
                interpretation_id="soil_plant_productive_water_use",
                domain="soil_plant",
                section_scope=["paddock", "zone"],
                symptom="low_soil_moisture",
                description="Low moisture may reflect productive plant uptake rather than immediate field failure.",
                requirements=[
                    SignalRequirement("soil", ["moisture", "vwc"], required=True),
                    SignalRequirement("plant", ["cover", "recovery"], required=True),
                ],
                evidence_terms=["low_soil_moisture", "strong_plant_response"],
                suggested_inspection="Verify plant vigor and canopy cover; avoid overcorrecting if growth is strong and stress indicators are low.",
            ),
            InterpretationRule(
                interpretation_id="source_sensor_fault_possible",
                domain="source_health",
                section_scope=["field", "zone", "paddock", "asset", "farm"],
                symptom="source_fault",
                description="The signal pattern may be explained by stale telemetry, low battery, or node/source failure.",
                requirements=[
                    SignalRequirement("source_health", ["last_seen"], required=False),
                    SignalRequirement("source_health", ["battery"], required=False),
                ],
                evidence_terms=["source_stale_or_faulty"],
                suggested_inspection="Check node battery, telemetry freshness, sensor placement, calibration, and nearby sensor agreement.",
            ),
            InterpretationRule(
                interpretation_id="water_asset_drawdown_or_failure",
                domain="water_infrastructure",
                section_scope=["asset", "farm"],
                symptom="water_asset_risk",
                description="Water asset risk may come from tank drawdown, pump state, pressure loss, or telemetry failure.",
                requirements=[
                    SignalRequirement("water", ["tank", "level"], required=False),
                    SignalRequirement("infrastructure", ["pump"], required=False),
                    SignalRequirement("water", ["pressure"], required=False),
                    SignalRequirement("source_health", ["last_seen"], required=False),
                ],
                evidence_terms=["water_asset_low", "pump_or_pressure_fault", "source_stale_or_faulty"],
                suggested_inspection="Check tank level, pump power/current, pressure, leaks, node telemetry, and water access points.",
            ),
        ]

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------

    def rule_applies_to_section_scope(self, section_scope: Sequence[str], section: Dict[str, Optional[str]]) -> bool:
        if "farm" in section_scope:
            return True
        if section.get("asset_id") and "asset" in section_scope:
            return True
        if section.get("paddock_id") and "paddock" in section_scope:
            return True
        if section.get("zone_id") and "zone" in section_scope:
            return True
        if section.get("field_id") and "field" in section_scope:
            return True
        return not any(section.values()) and "farm" in section_scope

    def find_matching_signals(self, signals: Sequence[FarmSignal], req: SignalRequirement) -> List[FarmSignal]:
        return [
            signal for signal in signals
            if signal.domain == req.domain and self.has_name(signal, req.name_contains)
        ]

    def has_name(self, signal: FarmSignal, parts: Iterable[str]) -> bool:
        name = signal.name.lower()
        return any(part.lower() in name for part in parts)

    def first_float(self, signals: Sequence[FarmSignal], name_parts: Iterable[str]) -> Optional[float]:
        for signal in signals:
            if self.has_name(signal, name_parts):
                value = self.float_value(signal.value)
                if value is not None:
                    return value
        return None

    def float_value(self, value: Any) -> Optional[float]:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def confidence_from_score(self, score: float, supporting: Sequence[str], missing: Sequence[str]) -> str:
        if score >= 0.75 and len(supporting) >= 4 and len(missing) <= 2:
            return "high"
        if score >= 0.45 and len(supporting) >= 2:
            return "medium"
        if score > 0:
            return "low"
        return "unknown"

    def priority_from_score(self, score: float) -> str:
        if score >= 0.75:
            return "high"
        if score >= 0.45:
            return "medium"
        return "low"

    def status_from_attention_and_ranked(
        self,
        attention: Sequence[AttentionAggregate],
        ranked: Sequence[RankedInterpretation],
    ) -> str:
        top_score = 0.0
        if attention:
            top_score = max(top_score, attention[0].score)
        if ranked:
            top_score = max(top_score, ranked[0].score)

        if top_score >= 0.75:
            return "action"
        if top_score >= 0.45:
            return "watch"
        if top_score > 0:
            return "ok_with_warning"
        return "insufficient_data"

    def top_confidence(
        self,
        attention: Sequence[AttentionAggregate],
        ranked: Sequence[RankedInterpretation],
    ) -> str:
        scored: List[Tuple[float, str]] = []
        scored.extend((item.score, item.priority) for item in attention)
        scored.extend((item.score, item.confidence) for item in ranked)
        if not scored:
            return "low"
        scored.sort(key=lambda item: item[0], reverse=True)
        return scored[0][1]

    def domain_from_measurement(self, layer: Optional[str], measurement_id: Optional[str]) -> str:
        text = f"{layer or ''} {measurement_id or ''}".lower()
        if any(term in text for term in ["soil", "vwc", "moisture", "infiltration"]):
            return "soil"
        if any(term in text for term in ["rain", "weather", "temperature", "humidity", "wind", "pressure"]):
            return "weather"
        if any(term in text for term in ["tank", "pump", "flow", "water"]):
            return "water"
        if any(term in text for term in ["plant", "forage", "cover", "height", "recovery"]):
            return "plant"
        if any(term in text for term in ["grazing", "livestock", "animal"]):
            return "animal"
        if any(term in text for term in ["battery", "rssi", "uptime", "telemetry", "fault"]):
            return "source_health"
        return layer or "unknown"

    def parse_time(self, value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return None

    def safe_json(self, payload_json: Optional[str]) -> Dict[str, Any]:
        if not payload_json:
            return {}
        try:
            return json.loads(payload_json)
        except (TypeError, json.JSONDecodeError):
            return {}
