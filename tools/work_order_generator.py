"""
Work Order Generator Tool
==========================

Generate structured maintenance work orders with complete details.

USAGE FOR PHASE 4 AGENTS:
-------------------------

Basic usage (generate work order):
>>> from tools.work_order_generator import generate_work_order
>>>
>>> anomaly_result = {
>>>     'severity': 'high',
>>>     'anomaly_score': 0.75,
>>>     'affected_sensors': ['sensor_T30', 'sensor_Nc'],
>>>     'recommendations': ['Inspect for overheating', 'Check mechanical issues']
>>> }
>>>
>>> roi_analysis = {
>>>     'failure_probability': 0.7,
>>>     'savings': 15000.0,
>>>     'roi_percentage': 125.0,
>>>     'preventive_cost': {'total_cost': 12000.0, 'labor_cost': 900.0}
>>> }
>>>
>>> similar_failures = [
>>>     {
>>>         'failure_type': 'bearing_degradation',
>>>         'similarity_score': 0.85,
>>>         'action_taken': 'Replace bearings and lubricate',
>>>         'parts_replaced': 'Bearing assembly, Seal kit',
>>>         'pattern_recommendation': 'Perform vibration analysis'
>>>     }
>>> ]
>>>
>>> work_order = generate_work_order(
>>>     equipment_id=1,
>>>     anomaly_result=anomaly_result,
>>>     roi_analysis=roi_analysis,
>>>     similar_failures=similar_failures
>>> )
>>> print(work_order.work_order_id)
>>> print(work_order.priority.value)

Save work order:
>>> from tools.work_order_generator import save_work_order
>>>
>>> saved_files = save_work_order(
>>>     work_order,
>>>     output_dir='work_orders',
>>>     formats=['json', 'markdown']
>>> )
>>> print(f"Saved to: {saved_files}")

INTEGRATION WITH GOOGLE ADK:
-----------------------------
To use as an ADK tool in Phase 4:

from google.adk import Tool
from tools.work_order_generator import generate_work_order

work_order_tool = Tool(
    name="generate_work_order",
    description="Creates structured maintenance work order",
    func=generate_work_order
)
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
from enum import Enum


class Priority(Enum):
    """Work order priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Status(Enum):
    """Work order status."""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class WorkOrder:
    """
    Structured maintenance work order.

    Attributes:
    -----------
    work_order_id : str
        Unique work order identifier
    equipment_id : int
        Target equipment ID
    equipment_info : Dict
        Equipment details (type, serial, location)
    issue_detected : str
        Description of detected issue
    failure_type : str
        Categorized failure type
    priority : Priority
        Urgency level
    recommended_actions : List[str]
        Step-by-step actions to perform
    parts_required : List[Dict]
        Parts list with part numbers and quantities
    estimated_cost : float
        Estimated total cost
    estimated_duration_hours : float
        Estimated time to complete
    safety_notes : List[str]
        Safety warnings and procedures
    created_date : datetime
        When work order was created
    due_date : Optional[datetime]
        Target completion date
    assigned_technician : Optional[str]
        Assigned technician name
    status : Status
        Current status
    notes : Optional[str]
        Additional notes
    """
    work_order_id: str
    equipment_id: int
    equipment_info: Dict
    issue_detected: str
    failure_type: str
    priority: Priority
    recommended_actions: List[str]
    parts_required: List[Dict]
    estimated_cost: float
    estimated_duration_hours: float
    safety_notes: List[str] = field(default_factory=list)
    created_date: datetime = field(default_factory=datetime.now)
    due_date: Optional[datetime] = None
    assigned_technician: Optional[str] = None
    status: Status = Status.DRAFT
    notes: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'work_order_id': self.work_order_id,
            'equipment_id': self.equipment_id,
            'equipment_info': self.equipment_info,
            'issue_detected': self.issue_detected,
            'failure_type': self.failure_type,
            'priority': self.priority.value,
            'recommended_actions': self.recommended_actions,
            'parts_required': self.parts_required,
            'estimated_cost': round(self.estimated_cost, 2),
            'estimated_duration_hours': round(self.estimated_duration_hours, 1),
            'safety_notes': self.safety_notes,
            'created_date': self.created_date.isoformat(),
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'assigned_technician': self.assigned_technician,
            'status': self.status.value,
            'notes': self.notes
        }

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


def generate_work_order_id(prefix: str = "WO") -> str:
    """Generate unique work order ID."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{prefix}-{timestamp}"


def determine_priority(
    anomaly_severity: str,
    failure_probability: float,
    estimated_rul: Optional[int] = None
) -> Priority:
    """
    Determine work order priority.

    Parameters:
    -----------
    anomaly_severity : str
        'critical', 'high', 'medium', 'low', 'none'
    failure_probability : float
        Probability of failure (0-1)
    estimated_rul : int, optional
        Estimated remaining useful life (cycles)

    Returns:
    --------
    Priority
        Work order priority level
    """
    if anomaly_severity == 'critical' or failure_probability > 0.8:
        return Priority.CRITICAL
    elif anomaly_severity == 'high' or failure_probability > 0.6:
        return Priority.HIGH
    elif anomaly_severity == 'medium' or failure_probability > 0.4:
        return Priority.MEDIUM
    else:
        return Priority.LOW


def calculate_due_date(priority: Priority) -> datetime:
    """Calculate due date based on priority."""
    now = datetime.now()

    if priority == Priority.CRITICAL:
        return now + timedelta(hours=24)
    elif priority == Priority.HIGH:
        return now + timedelta(days=3)
    elif priority == Priority.MEDIUM:
        return now + timedelta(days=7)
    else:
        return now + timedelta(days=14)


def generate_work_order(
    equipment_id: int,
    anomaly_result: Dict,
    roi_analysis: Dict,
    similar_failures: List[Dict],
    assigned_to: Optional[str] = None
) -> WorkOrder:
    """
    Generate structured maintenance work order.

    Parameters:
    -----------
    equipment_id : int
        Equipment ID from database
    anomaly_result : Dict
        Results from sensor_analyzer.analyze_sensor_data()
    roi_analysis : Dict
        Results from cost_calculator.calculate_maintenance_roi()
    similar_failures : List[Dict]
        Results from database_query.search_similar_failures()
    assigned_to : str, optional
        Technician name

    Returns:
    --------
    WorkOrder
        Complete work order ready for execution
    """
    from tools.database_query import get_db_connection, DEFAULT_DB_PATH

    # Get equipment info
    with get_db_connection(DEFAULT_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM equipment WHERE id = ?",
            (equipment_id,)
        )
        equipment = cursor.fetchone()

        if not equipment:
            raise ValueError(f"Equipment ID {equipment_id} not found")

        equipment_info = {
            'equipment_type': equipment['equipment_type'],
            'serial_number': equipment['serial_number'],
            'manufacturer': equipment['manufacturer'],
            'model': equipment['model'],
            'location': equipment['location']
        }

    # Determine priority
    priority = determine_priority(
        anomaly_result.get('severity', 'medium'),
        roi_analysis.get('failure_probability', 0.5)
    )

    # Generate issue description
    affected = ', '.join(anomaly_result.get('affected_sensors', []))
    issue_description = (
        f"Anomaly detected in {len(anomaly_result.get('affected_sensors', []))} sensor(s): {affected}. "
        f"Severity: {anomaly_result.get('severity', 'unknown')}. "
        f"Anomaly score: {anomaly_result.get('anomaly_score', 0):.2f}."
    )

    # Extract recommended actions from similar failures
    recommended_actions = anomaly_result.get('recommendations', []).copy()

    if similar_failures:
        top_match = similar_failures[0]
        failure_type = top_match.get('failure_type', 'unknown')

        # Add actions from historical cases
        if top_match.get('action_taken'):
            recommended_actions.append(f"Based on similar case: {top_match['action_taken']}")

        if top_match.get('pattern_recommendation'):
            recommended_actions.append(f"Pattern recommendation: {top_match['pattern_recommendation']}")
    else:
        failure_type = 'unclassified_anomaly'
        recommended_actions.append("Perform detailed diagnostic inspection")

    # Extract parts from similar failures
    parts_required = []
    if similar_failures:
        for failure in similar_failures[:2]:
            if failure.get('parts_replaced'):
                parts_text = failure['parts_replaced']
                # Simple parsing (in production, use proper parts catalog)
                parts_list = [p.strip() for p in parts_text.split(',')]
                for part in parts_list[:3]:  # Top 3 parts
                    parts_required.append({
                        'description': part,
                        'quantity': 1,
                        'estimated_cost': None,
                        'source': f"Historical case (similarity: {failure['similarity_score']:.2f})"
                    })

    # Safety notes based on failure type
    safety_notes = [
        "Lock out and tag all energy sources before beginning work",
        "Allow equipment to cool down completely (minimum 4 hours)",
        "Wear appropriate PPE: safety glasses, gloves, hearing protection"
    ]

    if 'temperature' in issue_description.lower() or 'T30' in affected or 'T50' in affected:
        safety_notes.append("CAUTION: High temperature components - verify cool-down complete")

    if 'pressure' in failure_type.lower():
        safety_notes.append("WARNING: Pressurized system - verify pressure release before opening")

    # Calculate due date
    due_date = calculate_due_date(priority)

    # Create work order
    work_order = WorkOrder(
        work_order_id=generate_work_order_id(),
        equipment_id=equipment_id,
        equipment_info=equipment_info,
        issue_detected=issue_description,
        failure_type=failure_type,
        priority=priority,
        recommended_actions=recommended_actions,
        parts_required=parts_required,
        estimated_cost=roi_analysis.get('preventive_cost', {}).get('total_cost', 0),
        estimated_duration_hours=roi_analysis.get('preventive_cost', {}).get('labor_cost', 900) / 150,  # Estimate hours
        safety_notes=safety_notes,
        due_date=due_date,
        assigned_technician=assigned_to,
        status=Status.DRAFT,
        notes=f"Generated automatically based on anomaly detection. "
              f"Estimated ROI: ${roi_analysis.get('savings', 0):.2f} savings "
              f"({roi_analysis.get('roi_percentage', 0):.1f}% ROI)"
    )

    return work_order


def format_work_order_markdown(work_order: WorkOrder) -> str:
    """
    Format work order as Markdown.

    Parameters:
    -----------
    work_order : WorkOrder
        Work order to format

    Returns:
    --------
    str
        Markdown-formatted work order
    """
    md = f"""# Work Order: {work_order.work_order_id}

## Equipment Information

- **Equipment ID:** {work_order.equipment_id}
- **Type:** {work_order.equipment_info.get('equipment_type', 'N/A')}
- **Manufacturer:** {work_order.equipment_info.get('manufacturer', 'N/A')}
- **Model:** {work_order.equipment_info.get('model', 'N/A')}
- **Serial Number:** {work_order.equipment_info.get('serial_number', 'N/A')}
- **Location:** {work_order.equipment_info.get('location', 'N/A')}

## Work Order Details

- **Priority:** {work_order.priority.value.upper()}
- **Status:** {work_order.status.value}
- **Created:** {work_order.created_date.strftime('%Y-%m-%d %H:%M')}
- **Due Date:** {work_order.due_date.strftime('%Y-%m-%d %H:%M') if work_order.due_date else 'Not set'}
- **Assigned To:** {work_order.assigned_technician or 'Unassigned'}
- **Estimated Duration:** {work_order.estimated_duration_hours:.1f} hours
- **Estimated Cost:** ${work_order.estimated_cost:,.2f}

## Issue Description

{work_order.issue_detected}

**Failure Type:** {work_order.failure_type}

## Recommended Actions

"""

    for i, action in enumerate(work_order.recommended_actions, 1):
        md += f"{i}. {action}\n"

    if work_order.parts_required:
        md += "\n## Parts Required\n\n"
        md += "| Part Description | Quantity | Estimated Cost | Source |\n"
        md += "|------------------|----------|----------------|--------|\n"

        for part in work_order.parts_required:
            cost_str = f"${part['estimated_cost']:.2f}" if part.get('estimated_cost') else "TBD"
            md += f"| {part['description']} | {part['quantity']} | {cost_str} | {part.get('source', 'N/A')} |\n"

    md += "\n## Safety Notes\n\n"
    for safety in work_order.safety_notes:
        md += f"- {safety}\n"

    if work_order.notes:
        md += f"\n## Additional Notes\n\n{work_order.notes}\n"

    md += "\n---\n\n"
    md += "*This work order was generated automatically by the Predictive Maintenance Intelligence Agent.*\n"

    return md


def save_work_order(
    work_order: WorkOrder,
    output_dir: str = "work_orders",
    formats: List[str] = ['json', 'markdown']
) -> Dict[str, str]:
    """
    Save work order to disk in multiple formats.

    Parameters:
    -----------
    work_order : WorkOrder
        Work order to save
    output_dir : str
        Directory to save files
    formats : List[str]
        Output formats ('json', 'markdown')

    Returns:
    --------
    Dict[str, str]
        Mapping of format -> file path
    """
    import os

    # Create directory if needed
    os.makedirs(output_dir, exist_ok=True)

    saved_files = {}

    # Save JSON
    if 'json' in formats:
        json_path = os.path.join(output_dir, f"{work_order.work_order_id}.json")
        with open(json_path, 'w') as f:
            f.write(work_order.to_json())
        saved_files['json'] = json_path

    # Save Markdown
    if 'markdown' in formats:
        md_path = os.path.join(output_dir, f"{work_order.work_order_id}.md")
        with open(md_path, 'w') as f:
            f.write(format_work_order_markdown(work_order))
        saved_files['markdown'] = md_path

    return saved_files
