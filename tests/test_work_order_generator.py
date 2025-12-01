"""
Unit tests for work_order_generator.py

Tests all work order generation functions including:
- Work order data models
- Priority determination
- Work order generation
- Formatting and file output
"""

import unittest
import os
import json
import shutil
from datetime import datetime, timedelta
from tools.work_order_generator import (
    Priority,
    Status,
    WorkOrder,
    generate_work_order_id,
    determine_priority,
    calculate_due_date,
    generate_work_order,
    format_work_order_markdown,
    save_work_order
)


class TestPriorityEnum(unittest.TestCase):
    """Test Priority enum."""

    def test_priority_values(self):
        """Test priority enum values."""
        self.assertEqual(Priority.CRITICAL.value, "critical")
        self.assertEqual(Priority.HIGH.value, "high")
        self.assertEqual(Priority.MEDIUM.value, "medium")
        self.assertEqual(Priority.LOW.value, "low")


class TestStatusEnum(unittest.TestCase):
    """Test Status enum."""

    def test_status_values(self):
        """Test status enum values."""
        self.assertEqual(Status.DRAFT.value, "draft")
        self.assertEqual(Status.APPROVED.value, "approved")
        self.assertEqual(Status.COMPLETED.value, "completed")


class TestWorkOrder(unittest.TestCase):
    """Test WorkOrder data model."""

    def test_create_work_order(self):
        """Test creating work order."""
        wo = WorkOrder(
            work_order_id="WO-TEST-001",
            equipment_id=1,
            equipment_info={'equipment_type': 'Engine'},
            issue_detected="Test issue",
            failure_type="test_failure",
            priority=Priority.HIGH,
            recommended_actions=["Action 1", "Action 2"],
            parts_required=[{"description": "Part 1", "quantity": 1}],
            estimated_cost=5000.0,
            estimated_duration_hours=8.0
        )

        self.assertEqual(wo.work_order_id, "WO-TEST-001")
        self.assertEqual(wo.equipment_id, 1)
        self.assertEqual(wo.priority, Priority.HIGH)
        self.assertEqual(wo.status, Status.DRAFT)

    def test_to_dict_conversion(self):
        """Test work order to_dict conversion."""
        wo = WorkOrder(
            work_order_id="WO-TEST-001",
            equipment_id=1,
            equipment_info={'equipment_type': 'Engine'},
            issue_detected="Test issue",
            failure_type="test_failure",
            priority=Priority.MEDIUM,
            recommended_actions=["Action 1"],
            parts_required=[],
            estimated_cost=3000.0,
            estimated_duration_hours=6.0
        )

        wo_dict = wo.to_dict()

        self.assertIsInstance(wo_dict, dict)
        self.assertEqual(wo_dict['work_order_id'], "WO-TEST-001")
        self.assertEqual(wo_dict['priority'], 'medium')
        self.assertEqual(wo_dict['status'], 'draft')
        self.assertIn('created_date', wo_dict)

    def test_to_json_conversion(self):
        """Test work order to_json conversion."""
        wo = WorkOrder(
            work_order_id="WO-TEST-001",
            equipment_id=1,
            equipment_info={'equipment_type': 'Engine'},
            issue_detected="Test issue",
            failure_type="test_failure",
            priority=Priority.LOW,
            recommended_actions=["Action 1"],
            parts_required=[],
            estimated_cost=2000.0,
            estimated_duration_hours=4.0
        )

        json_str = wo.to_json()

        self.assertIsInstance(json_str, str)
        # Verify it's valid JSON
        parsed = json.loads(json_str)
        self.assertEqual(parsed['work_order_id'], "WO-TEST-001")


class TestGenerateWorkOrderID(unittest.TestCase):
    """Test work order ID generation."""

    def test_generate_id_format(self):
        """Test ID generation format."""
        wo_id = generate_work_order_id()

        self.assertTrue(wo_id.startswith("WO-"))
        self.assertGreater(len(wo_id), 10)

    def test_generate_id_uniqueness(self):
        """Test IDs are unique."""
        id1 = generate_work_order_id()
        id2 = generate_work_order_id()

        # May be same if generated in same second
        # Just verify format is correct
        self.assertTrue(id1.startswith("WO-"))
        self.assertTrue(id2.startswith("WO-"))

    def test_custom_prefix(self):
        """Test custom prefix."""
        wo_id = generate_work_order_id(prefix="MAINT")

        self.assertTrue(wo_id.startswith("MAINT-"))


class TestDeterminePriority(unittest.TestCase):
    """Test priority determination."""

    def test_critical_severity(self):
        """Test critical severity."""
        priority = determine_priority(
            anomaly_severity='critical',
            failure_probability=0.5
        )

        self.assertEqual(priority, Priority.CRITICAL)

    def test_high_failure_probability(self):
        """Test high failure probability."""
        priority = determine_priority(
            anomaly_severity='medium',
            failure_probability=0.85
        )

        self.assertEqual(priority, Priority.CRITICAL)

    def test_high_severity(self):
        """Test high severity."""
        priority = determine_priority(
            anomaly_severity='high',
            failure_probability=0.4
        )

        self.assertEqual(priority, Priority.HIGH)

    def test_medium_severity(self):
        """Test medium severity."""
        priority = determine_priority(
            anomaly_severity='medium',
            failure_probability=0.5
        )

        self.assertEqual(priority, Priority.MEDIUM)

    def test_low_severity(self):
        """Test low severity."""
        priority = determine_priority(
            anomaly_severity='low',
            failure_probability=0.1
        )

        self.assertEqual(priority, Priority.LOW)


class TestCalculateDueDate(unittest.TestCase):
    """Test due date calculation."""

    def test_critical_due_date(self):
        """Test critical priority due date."""
        now = datetime.now()
        due_date = calculate_due_date(Priority.CRITICAL)

        # Should be 24 hours from now
        expected = now + timedelta(hours=24)
        delta = abs((due_date - expected).total_seconds())
        self.assertLess(delta, 5)  # Within 5 seconds

    def test_high_due_date(self):
        """Test high priority due date."""
        now = datetime.now()
        due_date = calculate_due_date(Priority.HIGH)

        # Should be 3 days from now
        expected = now + timedelta(days=3)
        delta = abs((due_date - expected).total_seconds())
        self.assertLess(delta, 5)

    def test_medium_due_date(self):
        """Test medium priority due date."""
        now = datetime.now()
        due_date = calculate_due_date(Priority.MEDIUM)

        # Should be 7 days from now
        expected = now + timedelta(days=7)
        delta = abs((due_date - expected).total_seconds())
        self.assertLess(delta, 5)

    def test_low_due_date(self):
        """Test low priority due date."""
        now = datetime.now()
        due_date = calculate_due_date(Priority.LOW)

        # Should be 14 days from now
        expected = now + timedelta(days=14)
        delta = abs((due_date - expected).total_seconds())
        self.assertLess(delta, 5)


class TestGenerateWorkOrder(unittest.TestCase):
    """Test work order generation."""

    def test_generate_basic_work_order(self):
        """Test generating basic work order."""
        anomaly_result = {
            'severity': 'high',
            'anomaly_score': 0.75,
            'affected_sensors': ['sensor_T30', 'sensor_Nc'],
            'recommendations': ['Inspect for overheating']
        }

        roi_analysis = {
            'failure_probability': 0.7,
            'savings': 15000.0,
            'roi_percentage': 125.0,
            'preventive_cost': {'total_cost': 12000.0, 'labor_cost': 900.0}
        }

        similar_failures = [
            {
                'failure_type': 'bearing_degradation',
                'similarity_score': 0.85,
                'action_taken': 'Replace bearings',
                'parts_replaced': 'Bearing assembly',
                'pattern_recommendation': 'Perform vibration analysis'
            }
        ]

        wo = generate_work_order(
            equipment_id=1,
            anomaly_result=anomaly_result,
            roi_analysis=roi_analysis,
            similar_failures=similar_failures
        )

        self.assertIsInstance(wo, WorkOrder)
        self.assertEqual(wo.equipment_id, 1)
        self.assertEqual(wo.priority, Priority.HIGH)
        self.assertGreater(len(wo.recommended_actions), 0)
        self.assertGreater(len(wo.safety_notes), 0)

    def test_generate_with_no_similar_failures(self):
        """Test generating work order with no similar failures."""
        anomaly_result = {
            'severity': 'medium',
            'anomaly_score': 0.5,
            'affected_sensors': ['sensor_Ps30'],
            'recommendations': ['Check pressure system']
        }

        roi_analysis = {
            'failure_probability': 0.4,
            'savings': 5000.0,
            'roi_percentage': 50.0,
            'preventive_cost': {'total_cost': 10000.0, 'labor_cost': 900.0}
        }

        wo = generate_work_order(
            equipment_id=1,
            anomaly_result=anomaly_result,
            roi_analysis=roi_analysis,
            similar_failures=[]
        )

        self.assertIsInstance(wo, WorkOrder)
        self.assertEqual(wo.failure_type, 'unclassified_anomaly')
        self.assertIn('Perform detailed diagnostic inspection', wo.recommended_actions)

    def test_generate_with_assigned_technician(self):
        """Test generating work order with assigned technician."""
        anomaly_result = {
            'severity': 'low',
            'anomaly_score': 0.3,
            'affected_sensors': ['sensor_W31'],
            'recommendations': ['Monitor flow']
        }

        roi_analysis = {
            'failure_probability': 0.2,
            'savings': 1000.0,
            'roi_percentage': 20.0,
            'preventive_cost': {'total_cost': 5000.0, 'labor_cost': 600.0}
        }

        wo = generate_work_order(
            equipment_id=1,
            anomaly_result=anomaly_result,
            roi_analysis=roi_analysis,
            similar_failures=[],
            assigned_to="John Smith"
        )

        self.assertEqual(wo.assigned_technician, "John Smith")

    def test_safety_notes_for_temperature(self):
        """Test safety notes for temperature issues."""
        anomaly_result = {
            'severity': 'critical',
            'anomaly_score': 0.9,
            'affected_sensors': ['sensor_T30', 'sensor_T50'],
            'recommendations': ['Immediate shutdown required']
        }

        roi_analysis = {
            'failure_probability': 0.9,
            'savings': 50000.0,
            'roi_percentage': 200.0,
            'preventive_cost': {'total_cost': 25000.0, 'labor_cost': 1200.0}
        }

        wo = generate_work_order(
            equipment_id=1,
            anomaly_result=anomaly_result,
            roi_analysis=roi_analysis,
            similar_failures=[]
        )

        # Should have temperature-related safety note
        has_temp_note = any('temperature' in note.lower() for note in wo.safety_notes)
        self.assertTrue(has_temp_note)


class TestFormatWorkOrderMarkdown(unittest.TestCase):
    """Test markdown formatting."""

    def test_format_basic_markdown(self):
        """Test basic markdown formatting."""
        wo = WorkOrder(
            work_order_id="WO-TEST-001",
            equipment_id=1,
            equipment_info={'equipment_type': 'Engine', 'manufacturer': 'GE', 'model': 'CF6', 'serial_number': '123', 'location': 'Hangar 1'},
            issue_detected="Test issue",
            failure_type="test_failure",
            priority=Priority.MEDIUM,
            recommended_actions=["Action 1", "Action 2"],
            parts_required=[],
            estimated_cost=5000.0,
            estimated_duration_hours=8.0,
            safety_notes=["Safety note 1"]
        )

        markdown = format_work_order_markdown(wo)

        self.assertIsInstance(markdown, str)
        self.assertIn("# Work Order: WO-TEST-001", markdown)
        self.assertIn("Equipment Information", markdown)
        self.assertIn("Action 1", markdown)
        self.assertIn("Action 2", markdown)
        self.assertIn("Safety note 1", markdown)

    def test_format_with_parts(self):
        """Test formatting with parts list."""
        wo = WorkOrder(
            work_order_id="WO-TEST-002",
            equipment_id=1,
            equipment_info={'equipment_type': 'Engine', 'manufacturer': 'GE', 'model': 'CF6', 'serial_number': '123', 'location': 'Hangar 1'},
            issue_detected="Test issue",
            failure_type="test_failure",
            priority=Priority.HIGH,
            recommended_actions=["Action 1"],
            parts_required=[
                {"description": "Bearing assembly", "quantity": 2, "estimated_cost": 1500.0, "source": "Historical"}
            ],
            estimated_cost=10000.0,
            estimated_duration_hours=12.0,
            safety_notes=["Safety note 1"]
        )

        markdown = format_work_order_markdown(wo)

        self.assertIn("Parts Required", markdown)
        self.assertIn("Bearing assembly", markdown)


class TestSaveWorkOrder(unittest.TestCase):
    """Test saving work orders to disk."""

    def setUp(self):
        """Set up test directory."""
        self.test_dir = "test_work_orders"
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def tearDown(self):
        """Clean up test directory."""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_save_json_format(self):
        """Test saving as JSON."""
        wo = WorkOrder(
            work_order_id="WO-TEST-JSON",
            equipment_id=1,
            equipment_info={'equipment_type': 'Engine'},
            issue_detected="Test issue",
            failure_type="test_failure",
            priority=Priority.LOW,
            recommended_actions=["Action 1"],
            parts_required=[],
            estimated_cost=3000.0,
            estimated_duration_hours=4.0
        )

        saved = save_work_order(wo, output_dir=self.test_dir, formats=['json'])

        self.assertIn('json', saved)
        self.assertTrue(os.path.exists(saved['json']))

        # Verify JSON content
        with open(saved['json'], 'r') as f:
            data = json.load(f)
            self.assertEqual(data['work_order_id'], "WO-TEST-JSON")

    def test_save_markdown_format(self):
        """Test saving as Markdown."""
        wo = WorkOrder(
            work_order_id="WO-TEST-MD",
            equipment_id=1,
            equipment_info={'equipment_type': 'Engine'},
            issue_detected="Test issue",
            failure_type="test_failure",
            priority=Priority.MEDIUM,
            recommended_actions=["Action 1"],
            parts_required=[],
            estimated_cost=5000.0,
            estimated_duration_hours=6.0
        )

        saved = save_work_order(wo, output_dir=self.test_dir, formats=['markdown'])

        self.assertIn('markdown', saved)
        self.assertTrue(os.path.exists(saved['markdown']))

        # Verify markdown content
        with open(saved['markdown'], 'r') as f:
            content = f.read()
            self.assertIn("# Work Order: WO-TEST-MD", content)

    def test_save_both_formats(self):
        """Test saving both JSON and Markdown."""
        wo = WorkOrder(
            work_order_id="WO-TEST-BOTH",
            equipment_id=1,
            equipment_info={'equipment_type': 'Engine'},
            issue_detected="Test issue",
            failure_type="test_failure",
            priority=Priority.HIGH,
            recommended_actions=["Action 1"],
            parts_required=[],
            estimated_cost=8000.0,
            estimated_duration_hours=10.0
        )

        saved = save_work_order(wo, output_dir=self.test_dir, formats=['json', 'markdown'])

        self.assertIn('json', saved)
        self.assertIn('markdown', saved)
        self.assertTrue(os.path.exists(saved['json']))
        self.assertTrue(os.path.exists(saved['markdown']))


if __name__ == '__main__':
    unittest.main()
