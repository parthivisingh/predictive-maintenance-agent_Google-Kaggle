-- Maintenance History Database Schema
-- Predictive Maintenance Intelligence Agent
-- Date: December 1, 2025

-- Table 1: Equipment
CREATE TABLE IF NOT EXISTS equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_type VARCHAR(50) NOT NULL,
    serial_number VARCHAR(50) UNIQUE NOT NULL,
    manufacturer VARCHAR(100),
    model VARCHAR(100),
    install_date DATE NOT NULL,
    location VARCHAR(100),
    operating_hours FLOAT DEFAULT 0.0,
    last_maintenance_date DATE,
    status VARCHAR(20) DEFAULT 'active',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_equipment_type ON equipment(equipment_type);
CREATE INDEX IF NOT EXISTS idx_equipment_status ON equipment(status);
CREATE INDEX IF NOT EXISTS idx_equipment_serial ON equipment(serial_number);

-- Table 2: Maintenance Logs
CREATE TABLE IF NOT EXISTS maintenance_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL,
    maintenance_date DATE NOT NULL,
    issue_description TEXT NOT NULL,
    failure_type VARCHAR(100),
    root_cause TEXT,
    action_taken TEXT NOT NULL,
    parts_replaced TEXT,
    labor_hours FLOAT,
    parts_cost FLOAT,
    labor_cost FLOAT,
    total_cost FLOAT,
    downtime_hours FLOAT,
    downtime_cost FLOAT,
    severity VARCHAR(20),
    technician_name VARCHAR(100),
    work_order_id VARCHAR(50),
    resolution_status VARCHAR(20) DEFAULT 'completed',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_maintenance_equipment ON maintenance_logs(equipment_id);
CREATE INDEX IF NOT EXISTS idx_maintenance_date ON maintenance_logs(maintenance_date);
CREATE INDEX IF NOT EXISTS idx_maintenance_failure_type ON maintenance_logs(failure_type);
CREATE INDEX IF NOT EXISTS idx_maintenance_severity ON maintenance_logs(severity);

-- Table 3: Failure Patterns
CREATE TABLE IF NOT EXISTS failure_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    failure_type VARCHAR(100) NOT NULL,
    sensor_signature TEXT NOT NULL,
    affected_sensors TEXT,
    signature_description TEXT,
    typical_degradation_cycles INTEGER,
    warning_threshold_hours FLOAT,
    critical_threshold_hours FLOAT,
    root_cause TEXT,
    recommended_action TEXT,
    preventive_maintenance_cost FLOAT,
    failure_cost FLOAT,
    occurrence_frequency VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_failure_type ON failure_patterns(failure_type);
CREATE INDEX IF NOT EXISTS idx_occurrence_frequency ON failure_patterns(occurrence_frequency);
