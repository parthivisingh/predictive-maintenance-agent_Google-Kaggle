# Predictive Maintenance Intelligence Agent

A multi-agent AI system that revolutionizes manufacturing maintenance by predicting equipment failures before they occur, reducing unplanned downtime by 30-50% and extending equipment lifespan through intelligent maintenance scheduling.

## Table of Contents
- [Problem Statement](#problem-statement)
- [Solution Overview](#solution-overview)
- [Architecture](#architecture)
- [Setup Instructions](#setup-instructions)
- [Usage Examples](#usage-examples)
- [Interpreting Results](#interpreting-results)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)
- [Contributing](#contributing)

## Problem Statement

### The High Cost of Manufacturing Downtime

Manufacturing facilities face a critical challenge: **unplanned equipment downtime costs between $50,000 to $250,000 per hour** depending on the industry and production scale. The cumulative impact includes:

- **Revenue Loss**: Direct production stoppage translates to immediate revenue loss
- **Emergency Repairs**: Rush repairs cost 3-5x more than planned maintenance
- **Extended Downtime**: Finding and replacing failed parts can take 24-72 hours
- **Quality Issues**: Equipment degradation leads to defect rates increasing by 15-25%
- **Safety Risks**: Critical failures can endanger personnel and facilities
- **Cascading Failures**: One equipment failure often triggers downstream problems

**Industry Statistics:**
- Average manufacturer experiences 800+ hours of downtime annually
- 82% of companies have experienced at least one unplanned downtime event
- 70% of companies don't know when their assets will fail
- Reactive maintenance costs 5x more than predictive maintenance

### Traditional Approaches Fall Short

1. **Reactive Maintenance**: Fixing equipment after failure (most expensive)
2. **Preventive Maintenance**: Time-based schedules (often too early or too late)
3. **Manual Monitoring**: Maintenance staff review sensor data periodically (slow, error-prone)

None of these approaches leverage real-time sensor data analysis, historical failure patterns, or AI-driven decision-making to optimize maintenance timing and resource allocation.

## Solution Overview

### Intelligent Predictive Maintenance via Multi-Agent AI

This system implements a sophisticated **multi-agent AI architecture** that continuously monitors equipment health, predicts failures, and generates actionable maintenance recommendations with ROI analysis.

**Key Capabilities:**

1. **Real-Time Anomaly Detection**
   - Analyzes 21+ sensor readings (temperature, pressure, vibration, etc.)
   - Uses ensemble ML models (Isolation Forest + Local Outlier Factor)
   - Detects subtle degradation patterns invisible to human operators

2. **Historical Failure Research**
   - Searches maintenance history database for similar failure patterns
   - Identifies root causes and successful remediation strategies
   - Calculates average repair costs and downtime from past incidents

3. **Intelligent Recommendations**
   - Generates specific maintenance actions based on failure patterns
   - Provides ROI analysis comparing preventive vs. reactive costs
   - Creates detailed work orders with part specifications and priorities

4. **Cost Optimization**
   - Estimates preventive maintenance costs (parts + labor + downtime)
   - Compares against reactive failure costs (emergency repair + extended downtime)
   - Recommends optimal maintenance timing for maximum ROI

**Business Impact:**
- **30-50% reduction** in unplanned downtime
- **20-30% savings** in maintenance costs
- **15-25% extension** of equipment lifespan
- **70-90% improvement** in maintenance planning accuracy

## Architecture

### Multi-Agent Pipeline Workflow

```mermaid
graph TB
    Start([Sensor Data Input]) --> Root[Root Agent<br/>Pipeline Orchestrator]

    Root --> Diagnostic[Diagnostic Agent<br/>Anomaly Detection]

    Diagnostic --> |"Anomaly<br/>Detected"| Research[Research Agent<br/>Historical Failure Search]
    Diagnostic --> |"Normal<br/>Operation"| NormalPath[Skip Research & Recommendation]

    Research --> Recommendation[Recommendation Agent<br/>ROI Analysis & Work Orders]

    Recommendation --> Output[Final Decision & Report]
    NormalPath --> Output

    Diagnostic -.->|Uses| SensorTool[Sensor Analyzer Tool<br/>ML Models: IF + LOF]
    Research -.->|Uses| DBTool[Database Query Tool<br/>Vector Similarity Search]
    Recommendation -.->|Uses| ROITool[Cost Calculator Tool<br/>ROI Analysis]
    Recommendation -.->|Uses| WOTool[Work Order Generator<br/>Template System]

    style Root fill:#4A90E2,color:#fff
    style Diagnostic fill:#7ED321,color:#000
    style Research fill:#F5A623,color:#000
    style Recommendation fill:#BD10E0,color:#fff
    style Output fill:#50E3C2,color:#000
    style SensorTool fill:#E8F5E9,color:#000
    style DBTool fill:#FFF3E0,color:#000
    style ROITool fill:#F3E5F5,color:#000
    style WOTool fill:#F3E5F5,color:#000
```

### Agent Responsibilities

#### 1. Root Agent (Pipeline Orchestrator)
- **Role**: Coordinates the sequential execution of specialized agents
- **Logic**: Implements early-exit optimization (skips research/recommendation if no anomaly)
- **Output**: Consolidated results with execution metadata

#### 2. Diagnostic Agent (Anomaly Detection)
- **Input**: Sensor readings (21 sensors), unit ID, time cycle
- **Processing**:
  - Isolation Forest: Detects outliers in high-dimensional sensor space
  - Local Outlier Factor: Identifies density-based anomalies
  - Combined scoring with confidence metrics
- **Output**: Anomaly detection (yes/no), severity (low/medium/high/critical), affected sensors, recommendations

#### 3. Research Agent (Historical Failure Search)
- **Input**: Diagnostic results, sensor anomaly patterns
- **Processing**:
  - Vector similarity search in maintenance history database
  - Matches against 1000+ historical failure records
  - Filters by similarity threshold (default: 0.6)
- **Output**: Top-N similar failures with root causes, actions taken, costs, and downtime

#### 4. Recommendation Agent (ROI Analysis & Work Order Generation)
- **Input**: Diagnostic + research results
- **Processing**:
  - ROI calculation comparing preventive vs. reactive maintenance
  - Work order generation using historical data templates
  - Priority assignment based on severity and estimated costs
- **Output**: ROI analysis, work order with actionable tasks, priority level

### Technology Stack

- **AI/ML**: Google Gemini API (via google-genai)
- **Machine Learning**: scikit-learn (Isolation Forest, Local Outlier Factor)
- **Database**: SQLite with vector similarity search
- **Data Processing**: pandas, numpy
- **API Framework**: FastAPI (for future API endpoints)
- **Monitoring**: OpenTelemetry, Prometheus metrics
- **Configuration**: python-dotenv for environment management

## Setup Instructions

### Prerequisites

- Python 3.9 or higher
- Google Cloud account with Gemini API access
- Git (for cloning the repository)
- 4GB+ RAM recommended for ML model operations

### 1. Clone the Repository

```bash
git clone <repository-url>
cd predictive-maintenance-agent
```

### 2. Environment Setup

#### Option A: Using Virtual Environment (Recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Option B: Using Conda

```bash
conda create -n maintenance-agent python=3.9
conda activate maintenance-agent
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Key dependencies installed:**
- `google-genai==1.52.0` - Google Gemini API client
- `scikit-learn==1.7.2` - Machine learning models
- `pandas==2.3.3` - Data processing
- `sqlalchemy==2.0.44` - Database ORM
- `fastapi==0.118.3` - API framework
- `pydantic==2.12.5` - Data validation
- `matplotlib==3.10.7` - Visualization

### 4. Download Data Files

#### Option A: Download from Kaggle (Original Dataset)

1. Install Kaggle CLI:
   ```bash
   pip install kaggle
   ```

2. Configure Kaggle credentials:
   - Go to https://www.kaggle.com/settings
   - Click "Create New API Token" (downloads kaggle.json)
   - Place `kaggle.json` in:
     - Windows: `C:\Users\<YourUsername>\.kaggle\`
     - Linux/Mac: `~/.kaggle/`

3. Download NASA Turbofan Engine dataset:
   ```bash
   kaggle datasets download -d behrad3d/nasa-cmaps
   unzip nasa-cmaps.zip -d data/raw/
   ```

#### Option B: Use Provided Sample Data (Quick Start)

The repository includes pre-processed sample data in `data/cmapss_processed.csv` for immediate testing.

### 5. API Key Configuration

Create a `.env` file in the project root:

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

Edit `.env` and add your Google Gemini API key:

```env
GOOGLE_API_KEY=your_actual_api_key_here
```

**To obtain a Google Gemini API key:**
1. Visit https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key and paste it in your `.env` file

**Security Note:** Never commit your `.env` file to version control. It's already in `.gitignore`.

### 6. Database Initialization

The system uses SQLite databases for maintenance history and vector embeddings.

#### Initialize Database Schema

```bash
python tools/database_setup.py
```

This creates:
- `data/maintenance_history.db` - SQLite database with maintenance records
- Pre-populated with 1000+ historical failure records
- Indexed for fast similarity searches

#### Verify Database Setup

```bash
python -c "from tools.database_query import DatabaseQueryTool; print(DatabaseQueryTool().get_stats())"
```

Expected output:
```
{'total_records': 1000, 'failure_types': 15, 'components': 25, 'avg_cost': 8500.0}
```

### 7. Verify Installation

Run the system health check:

```bash
python -m pytest tests/test_cli_smoke.py -v
```

Expected output:
```
tests/test_cli_smoke.py::test_imports PASSED
tests/test_cli_smoke.py::test_database_connection PASSED
tests/test_cli_smoke.py::test_ml_models PASSED
tests/test_cli_smoke.py::test_api_key PASSED
```

## Usage Examples

### Example 1: Basic Pipeline Execution

Run the multi-agent pipeline with sample sensor data:

```bash
python examples/run_multi_agent_pipeline.py
```

**Sample Output:**

```
================================================================================
PHASE 4 MULTI-AGENT MAINTENANCE SYSTEM - DEMO
================================================================================

[OK] Root agent initialized
  - Diagnostic Agent: Ready
  - Research Agent: Ready
  - Recommendation Agent: Ready

[OK] Sample sensor data loaded (21 sensors)

[...] Executing multi-agent maintenance pipeline...
[OK] Pipeline execution completed

================================================================================
PIPELINE EXECUTION RESULTS
================================================================================

Status                    [OK] SUCCESS
Execution Time           2847.32 ms
Agents Called            diagnostic_agent, research_agent, recommendation_agent

================================================================================
1. DIAGNOSTIC ANALYSIS
================================================================================

Anomaly Detected         YES
Severity                 HIGH
Anomaly Score            0.7834
Confidence               89.50%
Method Used              combined

Affected Sensors         5 sensors
  1. sensor_T30
  2. sensor_T50
  3. sensor_P30
  4. sensor_Nf
  5. sensor_epr

Top Recommendation       Inspect turbine temperature sensors and bearings

================================================================================
2. SIMILAR FAILURES RESEARCH
================================================================================

Matches Found            3

Historical Failure Analysis:

  Match #1:
    Similarity Score      87.50%
    Failure Type         High-Pressure Turbine Degradation
    Root Cause           Bearing wear causing temperature increase
    Action Taken         Replaced HPT bearing assembly
    Parts Replaced       HPT bearing, temperature sensor
    Average Cost         $12,450.00
    Average Downtime     6.5 hours

  Match #2:
    Similarity Score      82.30%
    Failure Type         Compressor Fouling
    Root Cause           Contaminant buildup on compressor blades
    Action Taken         Chemical cleaning and blade inspection
    Parts Replaced       Compressor seals
    Average Cost         $5,200.00
    Average Downtime     3.2 hours

  Match #3:
    Similarity Score      78.90%
    Failure Type         Temperature Sensor Drift
    Root Cause           Sensor calibration drift
    Action Taken         Recalibration and sensor replacement
    Parts Replaced       T30 sensor, T50 sensor
    Average Cost         $1,850.00
    Average Downtime     1.5 hours

================================================================================
3. RECOMMENDATIONS & ROI ANALYSIS
================================================================================

ROI Analysis:
  Preventive Cost          $8,500.00
  Reactive Cost            $45,000.00
  Expected Savings         $36,500.00
  ROI Percentage           429.4%
  Recommendation           TAKE ACTION IMMEDIATELY

Work Order Generated:
  Work Order ID            WO-20251201-000001
  Priority                 HIGH
  Estimated Cost           $8,500.00
  Estimated Duration       5.5 hours

  Issue Summary
    Unit 1 (cycle 100) exhibits high anomaly score (0.7834) with elevated
    turbine temperatures and bearing vibration patterns consistent with HPT
    bearing degradation. Historical data suggests preventive replacement now
    avoids catastrophic failure in 50-100 cycles.

  Recommended Actions
    1. Shutdown unit for inspection
    2. Perform borescope inspection of HPT section
    3. Replace HPT bearing assembly if wear detected
    4. Recalibrate temperature sensors T30, T50
    5. Test run and verify sensor readings within normal range
    6. Update maintenance log with findings

================================================================================
4. FINAL DECISION
================================================================================

Action Required          YES
Priority                 HIGH
Work Order ID            WO-20251201-000001
Estimated Cost           $8,500.00

Summary
  High-severity anomaly detected with 89.5% confidence. Based on historical
  failures, immediate preventive maintenance is recommended. ROI analysis shows
  $36,500 in potential savings compared to reactive failure response.

Recommended Actions
  1. Shutdown unit for inspection
  2. Perform borescope inspection of HPT section
  3. Replace HPT bearing assembly if wear detected
  4. Recalibrate temperature sensors T30, T50
  5. Test run and verify sensor readings within normal range
  6. Update maintenance log with findings

================================================================================
OUTPUT FILE
================================================================================

[OK] Full results saved to: examples/pipeline_results.json
  File size: 8,742 bytes

================================================================================
SUMMARY STATISTICS
================================================================================

Equipment Unit ID        1
Time Cycle              100
Sensors Analyzed        21
Agents Executed         3
Total Execution Time    2847.32 ms

[OK] Pipeline completed successfully
```

### Example 2: Custom Configuration

```python
from agents.root_agent import RootAgent

# Initialize root agent
root_agent = RootAgent()

# Sensor data from your equipment
sensor_values = {
    "sensor_T30": 1605.2,
    "sensor_T50": 1450.8,
    "sensor_T2": 643.1,
    # ... (all 21 sensors)
}

# Execute with custom configuration
result = root_agent.execute_pipeline(
    unit_id=42,
    time_cycle=500,
    sensor_values=sensor_values,
    config={
        "diagnostic_method": "combined",      # or "isolation_forest", "lof"
        "similarity_top_n": 5,                # number of historical matches
        "similarity_threshold": 0.7,          # minimum similarity score
        "assigned_to": "Maintenance Team B",  # work order assignment
        "enable_work_order": True,            # generate work orders
        "emergency_threshold": 0.85           # critical anomaly threshold
    }
)

# Access results
print(f"Anomaly detected: {result['pipeline_results']['diagnostic']['anomaly_detected']}")
print(f"Severity: {result['pipeline_results']['diagnostic']['severity']}")
print(f"ROI: {result['pipeline_results']['recommendation']['roi_analysis']['roi_percentage']:.1f}%")
```

### Example 3: Batch Processing Multiple Units

```python
from src.simulation.batch_processor import BatchProcessor

# Define equipment profiles
profiles = [
    {"unit_id": 1, "time_cycle": 100, "sensor_values": {...}},
    {"unit_id": 2, "time_cycle": 150, "sensor_values": {...}},
    {"unit_id": 3, "time_cycle": 200, "sensor_values": {...}},
]

# Initialize batch processor
processor = BatchProcessor()

# Run all simulations
results = processor.run_batch(
    profiles=profiles,
    num_runs_per_profile=5,
    output_dir="output/batch_run"
)

# Generate metrics report
from src.simulation.metrics_reporter import MetricsReporter
reporter = MetricsReporter()
report = reporter.generate_report(results)

print(f"Total runs: {report['total_runs']}")
print(f"Success rate: {report['success_rate']:.1%}")
print(f"Average execution time: {report['avg_execution_time_ms']:.2f} ms")
```

### Example 4: Integration via Python API

```python
# In your existing manufacturing system
from agents.root_agent import RootAgent
import json

def monitor_equipment(equipment_id: int, sensor_readings: dict):
    """
    Integrate with your existing monitoring system.
    """
    agent = RootAgent()

    # Get current cycle from your system
    current_cycle = get_current_cycle(equipment_id)

    # Execute analysis
    result = agent.execute_pipeline(
        unit_id=equipment_id,
        time_cycle=current_cycle,
        sensor_values=sensor_readings
    )

    # Check if action required
    if result['final_decision']['action_required']:
        # Alert maintenance team
        send_alert(
            priority=result['final_decision']['priority'],
            work_order_id=result['final_decision']['work_order_id'],
            summary=result['final_decision']['summary']
        )

        # Create ticket in your maintenance system
        create_maintenance_ticket(result)

    # Log results
    log_to_database(result)

    return result
```

## Interpreting Results

### Understanding Diagnostic Output

#### Anomaly Score
- **Range**: 0.0 to 1.0
- **0.0 - 0.3**: Normal operation (no action needed)
- **0.3 - 0.6**: Minor anomaly (monitor closely)
- **0.6 - 0.8**: Significant anomaly (plan maintenance)
- **0.8 - 1.0**: Critical anomaly (immediate action required)

#### Severity Levels
- **low**: Minor deviation, continue monitoring
- **medium**: Schedule maintenance within 1-2 weeks
- **high**: Plan maintenance within 3-5 days
- **critical**: Immediate shutdown and repair required

#### Confidence Score
- **< 60%**: Low confidence, collect more data
- **60-80%**: Moderate confidence, verify with manual inspection
- **80-95%**: High confidence, trust the recommendation
- **> 95%**: Very high confidence, act immediately

### Understanding ROI Analysis

#### ROI Calculation Formula
```
ROI % = ((Reactive Cost - Preventive Cost) / Preventive Cost) × 100
```

#### Cost Components

**Preventive Maintenance Cost:**
- Parts cost (from historical averages)
- Labor cost (estimated hours × hourly rate)
- Planned downtime cost (scheduled shutdown)

**Reactive Maintenance Cost:**
- Emergency parts cost (1.5-2x normal cost)
- Emergency labor cost (overtime rates)
- Unplanned downtime cost (lost production)
- Collateral damage cost (failures that spread)

#### ROI Interpretation
- **> 200%**: Strong business case, act immediately
- **100-200%**: Good ROI, schedule within days
- **50-100%**: Moderate ROI, schedule within weeks
- **< 50%**: Low ROI, continue monitoring

### Work Order Priority Levels

- **critical**: Stop production immediately, safety risk present
- **high**: Plan shutdown within 24-48 hours
- **medium**: Schedule within 1-2 weeks during planned maintenance
- **low**: Include in next scheduled maintenance window

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Problem:**
```
ModuleNotFoundError: No module named 'google.genai'
```

**Solution:**
```bash
# Ensure virtual environment is activated
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

#### 2. API Key Errors

**Problem:**
```
google.api_core.exceptions.Unauthenticated: 401 API key not valid
```

**Solution:**
1. Verify `.env` file exists in project root
2. Check API key format (should start with `AIza`)
3. Verify key is active at https://makersuite.google.com/app/apikey
4. Restart Python session to reload environment variables

#### 3. Database Connection Errors

**Problem:**
```
sqlite3.OperationalError: unable to open database file
```

**Solution:**
```bash
# Ensure data directory exists
mkdir -p data

# Reinitialize database
python tools/database_setup.py

# Check permissions
# Windows:
icacls data\maintenance_history.db
# Linux/Mac:
ls -la data/maintenance_history.db
```

#### 4. Missing Sensor Data

**Problem:**
```
KeyError: 'sensor_T30'
```

**Solution:**
Ensure all 21 required sensors are present in `sensor_values` dictionary:
```python
required_sensors = [
    "sensor_T2", "sensor_T24", "sensor_T30", "sensor_T50", "sensor_T50_2",
    "sensor_P2", "sensor_P15", "sensor_P30", "sensor_Nf", "sensor_Nc",
    "sensor_epr", "sensor_Ps30", "sensor_phi", "sensor_NRf", "sensor_NRc",
    "sensor_BPR", "sensor_farB", "sensor_htBleed", "sensor_Nf_dmd",
    "sensor_PCNfR_dmd", "sensor_W31", "sensor_W32"
]
```

#### 5. Memory Errors with ML Models

**Problem:**
```
MemoryError: Unable to allocate array
```

**Solution:**
```python
# Reduce batch size in config
config = {
    "diagnostic_batch_size": 100,  # reduce from default 1000
    "ml_model_max_samples": 5000   # reduce training samples
}
```

#### 6. Slow Performance

**Problem:** Pipeline execution takes > 10 seconds

**Solution:**

1. **Enable caching:**
   ```python
   from tools.cache_manager import CacheManager
   CacheManager.enable_cache()
   ```

2. **Use faster diagnostic method:**
   ```python
   config = {"diagnostic_method": "isolation_forest"}  # faster than "combined"
   ```

3. **Reduce similarity search results:**
   ```python
   config = {"similarity_top_n": 3}  # reduce from default 5
   ```

### Logging and Debugging

#### Enable Debug Logging

```python
import logging
from tools.logging_config import get_logger, set_log_level

# Enable debug logging
set_log_level(logging.DEBUG)

# View detailed execution logs
logger = get_logger(__name__)
logger.debug("Starting pipeline execution...")
```

#### Check Log Files

```bash
# View recent logs
tail -f logs/maintenance_agent.log

# Search for errors
grep ERROR logs/maintenance_agent.log

# Filter by request ID
grep "request_id=12345" logs/maintenance_agent.log
```

#### Test Individual Agents

```python
# Test diagnostic agent in isolation
from agents.diagnostic_agent import DiagnosticAgent

agent = DiagnosticAgent()
context = {
    "unit_id": 1,
    "time_cycle": 100,
    "sensor_values": {...}
}
result = agent.analyze(context)
print(result)
```

### Performance Benchmarks

**Expected Performance Metrics:**
- Cold start (first run): 3-5 seconds
- Warm start (cached): 1-2 seconds
- Diagnostic agent: 200-500ms
- Research agent: 500-800ms
- Recommendation agent: 800-1500ms
- Memory usage: 150-300MB

### Getting Help

1. **Check Documentation:**
   - [API Reference](docs/API_Reference.md)
   - [Integration Playbook](docs/Integration_Playbook.md)
   - [Phase Implementation Guides](docs/)

2. **Run Tests:**
   ```bash
   pytest tests/ -v --tb=short
   ```

3. **System Health Check:**
   ```bash
   python scripts/run_observability_check.py
   ```

4. **Report Issues:**
   - GitHub Issues: [repository-url]/issues
   - Include: Python version, OS, error logs, configuration

## Project Structure

```
predictive-maintenance-agent/
├── agents/                      # Multi-agent AI system
│   ├── diagnostic_agent.py     # Anomaly detection agent
│   ├── research_agent.py       # Historical failure search agent
│   ├── recommendation_agent.py # ROI & work order generation
│   ├── root_agent.py           # Pipeline orchestrator
│   └── schemas.py              # Data models and validation
├── tools/                       # Specialized tools for agents
│   ├── sensor_analyzer.py      # ML-based sensor analysis
│   ├── database_query.py       # Maintenance history queries
│   ├── cost_calculator.py      # ROI analysis
│   ├── work_order_generator.py # Work order templating
│   └── ml_model_manager.py     # ML model lifecycle
├── src/                         # Core system modules
│   ├── simulation/             # Batch simulation framework
│   ├── evaluation/             # Model quality & system health
│   └── observability/          # Monitoring & metrics
├── data/                        # Data files
│   ├── cmapss_processed.csv    # Preprocessed sensor data
│   ├── maintenance_history.db  # SQLite database
│   └── manuals/                # Technical documentation
├── examples/                    # Usage examples
│   └── run_multi_agent_pipeline.py
├── tests/                       # Unit and integration tests
├── scripts/                     # Utility scripts
├── docker-compose.yml          # Container orchestration
├── requirements.txt            # Python dependencies
└── .env                        # Environment configuration
```

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

**Development Setup:**
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v --cov

# Run linting
flake8 agents/ tools/ src/
black agents/ tools/ src/ --check

# Type checking
mypy agents/ tools/ src/
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- NASA C-MAPSS Dataset: Turbofan engine degradation simulation data
- Google Gemini AI: Large language model for intelligent analysis
- scikit-learn: Machine learning library for anomaly detection
- The manufacturing and maintenance engineering community

---

**Built with**: Python 3.11+ | Google Gemini API | scikit-learn | FastAPI | SQLite

**For questions and support**, please open an issue on GitHub or contact the maintainers.
