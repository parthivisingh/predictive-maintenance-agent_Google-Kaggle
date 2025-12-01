# Turbofan Engine Maintenance Guide

**Document ID:** DOC-TF-001
**Version:** 1.0
**Last Updated:** December 1, 2025
**Applies To:** Turbofan engines (GE Aviation, Rolls-Royce, Pratt & Whitney models)

---

## Table of Contents

1. [Introduction](#introduction)
2. [Engine Components Overview](#engine-components-overview)
3. [Scheduled Maintenance Intervals](#scheduled-maintenance-intervals)
4. [Sensor Monitoring and Normal Ranges](#sensor-monitoring-and-normal-ranges)
5. [Common Failure Modes](#common-failure-modes)
6. [Bearing Replacement Procedures](#bearing-replacement-procedures)
7. [Temperature and Pressure Monitoring](#temperature-and-pressure-monitoring)
8. [Troubleshooting Guide](#troubleshooting-guide)
9. [Parts List and Costs](#parts-list-and-costs)
10. [Safety Warnings](#safety-warnings)
11. [References](#references)

---

## 1. Introduction

This comprehensive maintenance guide covers preventive and corrective maintenance procedures for turbofan engines used in commercial and industrial applications. The guide is specifically designed to work with the NASA C-MAPSS sensor monitoring system which tracks 21 distinct sensor measurements across 3 operational settings.

### Purpose and Scope

The primary objectives of this guide are to:

- Provide clear maintenance procedures for common failure modes
- Establish sensor-based early warning criteria for degradation
- Define cost-effective maintenance intervals
- Reduce unplanned downtime through predictive monitoring
- Ensure safe and compliant maintenance operations

This guide applies to turbofan engines from major manufacturers including GE Aviation (CFM56-7B, GE90-115B, GEnx-1B), Rolls-Royce (Trent series), and Pratt & Whitney (PW4000, PW1100G series).

---

## 2. Engine Components Overview

### High Pressure Compressor (HPC)

The HPC section compresses air to high pressures before combustion. Key monitoring points include:

- **Discharge temperature** (sensor_2): Normal range 640-660 units
- **Discharge pressure** (sensor_7): Normal range 550-600 units
- **Speed** (sensor_13): Normal range 2380-2400 RPM

### Low Pressure Compressor (LPC)

The LPC provides initial compression and feeds the HPC. Monitor:

- **Inlet temperature** (sensor_1): Normal range 518-520 units
- **Pressure ratio** (sensor_15): Normal range 8.3-8.5

### High Pressure Turbine (HPT)

Drives the HPC using combustion gas energy. Critical sensors:

- **Inlet temperature** (sensor_4): Normal range 1580-1620 units
- **Coolant bleed** (sensor_20, sensor_21): Normal range 38-40 units

### Low Pressure Turbine (LPT)

Drives the fan and LPC. Monitor:

- **Outlet temperature** (sensor_3): Normal range 1400-1410 units
- **Speed** (sensor_14): Normal range 100 units (normalized)

### Bearing Assemblies

Multiple bearing locations support rotating components:

- **Forward bearing**: Monitors via sensor_3, sensor_9
- **Aft bearing**: Monitors via sensor_11, sensor_8
- Temperature increases of 10-15 units indicate degradation

---

## 3. Scheduled Maintenance Intervals

### A-Check (Every 500 Operating Hours)

**Tasks:**
- Visual inspection of external components
- Oil level and quality check
- Sensor calibration verification
- Review of recorded sensor trends
- Minor cleaning and lubrication

**Estimated Duration:** 4-6 hours
**Estimated Cost:** $800-$1,200

### B-Check (Every 2,000 Operating Hours)

**Tasks:**
- All A-check items
- Borescope inspection of turbine blades
- Bearing vibration analysis
- Fuel system cleaning
- Compressor wash (if fouling detected)
- Detailed sensor data analysis

**Estimated Duration:** 16-24 hours
**Estimated Cost:** $3,500-$5,000

### C-Check (Every 8,000 Operating Hours)

**Tasks:**
- All B-check items
- Bearing replacement (if degradation detected)
- Blade inspection with measurement
- Seal replacement
- Complete sensor recalibration
- Performance testing

**Estimated Duration:** 48-72 hours
**Estimated Cost:** $12,000-$18,000

### D-Check (Every 24,000 Operating Hours or 5 Years)

**Tasks:**
- Complete engine overhaul
- All rotating components inspected/replaced
- Combustion chamber inspection
- All seals and gaskets replaced
- Complete sensor system replacement
- Performance baseline re-establishment

**Estimated Duration:** 200-300 hours
**Estimated Cost:** $85,000-$120,000

---

## 4. Sensor Monitoring and Normal Ranges

### Critical Temperature Sensors

| Sensor | Location | Normal Range | Warning Threshold | Critical Threshold |
|--------|----------|--------------|-------------------|-------------------|
| sensor_1 | LPC inlet | 518-520 | >525 | >530 |
| sensor_2 | HPC discharge | 640-660 | >670 | >680 |
| sensor_3 | LPT outlet | 1400-1410 | >1425 | >1440 |
| sensor_4 | HPT inlet | 1580-1620 | >1635 | >1650 |

### Pressure Sensors

| Sensor | Location | Normal Range | Warning Threshold | Critical Threshold |
|--------|----------|--------------|-------------------|-------------------|
| sensor_7 | HPC discharge | 550-600 | <540 or >610 | <530 or >620 |
| sensor_11 | Bearing cavity | 14.5-14.8 | >15.2 | >15.8 |

### Speed Sensors

| Sensor | Location | Normal Range | Warning Threshold | Critical Threshold |
|--------|----------|--------------|-------------------|-------------------|
| sensor_8 | Fan speed | 2385-2390 | >2395 | >2400 |
| sensor_13 | HPC speed | 9040-9060 | >9080 | >9100 |
| sensor_14 | Core speed | 100 (normalized) | >102 | >105 |

### Fuel and Bleed Sensors

| Sensor | Location | Normal Range | Warning Threshold | Critical Threshold |
|--------|----------|--------------|-------------------|-------------------|
| sensor_12 | Fuel flow ratio | 1.28-1.32 | <1.25 or >1.35 | <1.22 or >1.38 |
| sensor_20 | Coolant bleed | 38.5-39.5 | <37.5 | <36.5 |
| sensor_21 | Coolant bleed | 23.0-23.5 | <22.0 | <21.0 |

---

## 5. Common Failure Modes

### Bearing Degradation

**Frequency:** Occasional (15-20% of failures)
**Typical Onset:** 150-200 operating cycles
**Cost Impact:** $3,500 preventive vs. $45,000 failure

**Sensor Signature:**
- sensor_3 increases 10-15 units over 50-100 cycles
- sensor_9 shows gradual upward drift (20-30 units)
- sensor_11 increases 0.5-1.0 units

**Root Cause:** Bearing race wear due to thermal cycling and contamination

**Recommended Action:** Replace bearing assembly when sensor_3 exceeds baseline by 12 units or sensor_9 shows sustained upward trend over 75 cycles.

### Overheating

**Frequency:** Common (25-30% of failures)
**Typical Onset:** 120-150 operating cycles
**Cost Impact:** $4,200 preventive vs. $52,000 failure

**Sensor Signature:**
- sensor_4 consistently exceeds baseline by 15+ units
- sensor_3 increases steadily
- sensor_12 (fuel ratio) increases

**Root Cause:** Turbine blade erosion causing reduced cooling efficiency

**Recommended Action:** Inspect turbine blades when sensor_4 exceeds 1635 for more than 10 consecutive cycles. Replace blades if erosion exceeds 0.015" tolerance.

### Fuel System Degradation

**Frequency:** Occasional (5-10% of failures)
**Typical Onset:** 180-220 operating cycles
**Cost Impact:** $2,100 preventive vs. $35,000 failure

**Sensor Signature:**
- sensor_12 shows high variance (>0.05 cycle-to-cycle)
- sensor_14 oscillates
- sensor_20 decreases gradually

**Root Cause:** Fuel nozzle clogging or fuel pump wear

**Recommended Action:** Clean or replace fuel nozzles when sensor_12 variance exceeds 0.04 for 15+ cycles. Inspect fuel pump for wear.

### Compressor Fouling

**Frequency:** Common (15-20% of failures)
**Typical Onset:** 200-250 operating cycles
**Cost Impact:** $800 preventive vs. $15,000 failure

**Sensor Signature:**
- sensor_2 gradual increase (5-10 units over 100 cycles)
- sensor_7 decreasing (5-8 units over 100 cycles)
- sensor_13 decreasing (10-20 RPM over 100 cycles)

**Root Cause:** Dirt and debris accumulation on compressor blades

**Recommended Action:** Perform compressor water wash when sensor_2 exceeds baseline by 8 units or sensor_7 drops below 545. Check air filters.

### Pressure Seal Leak

**Frequency:** Common (10-15% of failures)
**Typical Onset:** 140-180 operating cycles
**Cost Impact:** $1,500 preventive vs. $28,000 failure

**Sensor Signature:**
- sensor_7 decreasing by >2 units from baseline
- sensor_11 increasing
- sensor_15 (pressure ratio) abnormal pattern

**Root Cause:** Seal degradation allowing pressure loss

**Recommended Action:** Replace pressure seals when sensor_7 drops >3 units or sensor_11 exceeds 15.0 for 20+ consecutive cycles.

---

## 6. Bearing Replacement Procedures

### Pre-Replacement Inspection

1. **Verify Sensor Readings** (30 minutes)
   - Confirm sensor_3 elevation >12 units from baseline
   - Check sensor_9 trend over past 100 cycles
   - Verify sensor_11 is elevated >0.8 units
   - Document baseline readings for comparison

2. **Visual Inspection** (45 minutes)
   - Remove cowling and access panels
   - Inspect for oil leaks around bearing seals
   - Check for metal particles in oil sump
   - Photograph bearing housing for records

3. **Vibration Analysis** (30 minutes)
   - Attach vibration sensors to bearing housing
   - Run engine at idle, 50%, 75%, and full power
   - Record vibration spectrum
   - Compare to baseline vibration signature
   - Elevated vibration at bearing defect frequencies confirms degradation

### Bearing Removal

1. **Engine Shutdown and Lockout** (15 minutes)
   - Follow lockout/tagout procedures
   - Ensure engine is cool (< 100°F surface temp)
   - Disconnect electrical power
   - Verify zero rotation

2. **Access Bearing Assembly** (2 hours)
   - Remove engine cowling sections
   - Disconnect oil supply and return lines
   - Remove bearing housing bolts (torque: 45 ft-lbs)
   - Carefully extract bearing housing with hoist

3. **Bearing Extraction** (1 hour)
   - Use bearing puller tool (P/N PULL-12345)
   - Apply heat to bearing housing (200-250°F max)
   - Extract bearing with steady pressure
   - Inspect bearing races for wear patterns
   - Document wear measurements and photograph

### Bearing Installation

1. **Prepare New Bearing** (30 minutes)
   - Verify bearing P/N matches: 12345-B for forward, 12346-B for aft
   - Inspect new bearing for damage
   - Clean bearing housing with solvent
   - Check housing dimensions (ID, OD, width)
   - Apply high-temp bearing grease (P/N GREASE-789)

2. **Install Bearing** (1.5 hours)
   - Heat bearing housing to 225°F
   - Align bearing with housing
   - Press bearing into housing with arbor press (max 5 tons pressure)
   - Verify bearing seating with depth gauge
   - Install bearing seals (P/N 12346-S)
   - Torque seal retaining ring to 25 ft-lbs

3. **Reassembly** (2 hours)
   - Clean all mating surfaces
   - Apply gasket sealant to housing flange
   - Install bearing housing assembly
   - Torque housing bolts in star pattern to 45 ft-lbs
   - Reconnect oil lines with new crush washers
   - Reinstall cowling and access panels

### Post-Installation Testing

1. **Oil System Check** (30 minutes)
   - Fill oil system to proper level
   - Run oil pump manually
   - Check for leaks at bearing housing
   - Verify oil pressure at bearing (40-50 psi)

2. **Sensor Verification** (30 minutes)
   - Verify all sensors reconnected
   - Perform sensor calibration check
   - Confirm sensor readings at idle

3. **Engine Run-In** (2 hours)
   - Idle engine for 10 minutes, monitor sensor_3, sensor_9, sensor_11
   - Increase to 50% power for 20 minutes
   - Monitor for vibration increase
   - Run at 75% power for 30 minutes
   - Full power run for 15 minutes
   - Record final sensor baselines
   - Compare to pre-replacement values

### Expected Outcomes

After successful bearing replacement:
- sensor_3 should return to normal baseline (1400-1410 range)
- sensor_9 should stabilize with no upward trend
- sensor_11 should return to 14.5-14.8 range
- Vibration levels should decrease to baseline
- No oil leaks detected

**Total Labor:** 6-8 hours
**Parts Cost:** $2,500-$3,000
**Total Cost:** $3,500-$4,500

---

## 7. Temperature and Pressure Monitoring

### Temperature Trend Analysis

Gradual temperature increases often indicate degradation:

**Normal Degradation Rate:**
- sensor_3, sensor_4: 0.5-1.0 units per 1000 operating hours
- Exceeding 2 units per 1000 hours indicates accelerated wear

**Abnormal Patterns:**
- Sudden jumps (>5 units in single cycle): Sensor drift or physical damage
- Oscillating temperatures: Control system issues or fuel delivery problems
- Diverging temperatures between similar sensors: Sensor calibration needed

### Pressure Monitoring

Pressure changes indicate sealing and compressor efficiency:

**Compressor Efficiency:**
- sensor_7 decreasing: Compressor fouling or blade erosion
- sensor_15 (pressure ratio) decreasing: Overall efficiency loss

**Seal Integrity:**
- sensor_7 with sensor_11 increasing: Pressure seal leak

### Combined Temperature-Pressure Analysis

Most failure modes show correlated temperature and pressure changes:

**Bearing Degradation:**
- Temperature up (sensor_3, sensor_9, sensor_11)
- Pressure minimal change

**Overheating:**
- Temperature up (sensor_3, sensor_4)
- Pressure up (sensor_7) initially, then down

**Seal Leak:**
- Temperature up (sensor_11)
- Pressure down (sensor_7)

---

## 8. Troubleshooting Guide

### High Temperature Alert

**Symptom:** sensor_3 or sensor_4 >15 units above baseline

**Troubleshooting Steps:**

1. **Verify Sensor Accuracy**
   - Check sensor calibration date (should be <12 months)
   - Compare reading with redundant sensor if available
   - Look for sudden jumps indicating sensor failure vs. gradual increases

2. **Check Cooling System**
   - Verify sensor_20 and sensor_21 (coolant bleed) are in normal range
   - Inspect cooling passages for blockage
   - Check coolant valve operation

3. **Inspect for Overheating Sources**
   - Borescope turbine blades for erosion
   - Check combustion chamber for damage
   - Verify fuel flow (sensor_12) is normal

4. **Resolution:**
   - If sensor drift: Recalibrate or replace sensor ($500)
   - If coolant issue: Replace coolant valves ($3,200)
   - If blade erosion: Replace turbine blades ($5,500)

### Low Pressure Alert

**Symptom:** sensor_7 < 540 units

**Troubleshooting Steps:**

1. **Check for Leaks**
   - Inspect engine for visible leaks
   - Check sensor_11 for elevation (indicates leak)
   - Perform pressure decay test

2. **Compressor Performance**
   - Check sensor_2 for elevation (fouling)
   - Review sensor_13 speed (should be normal range)
   - Inspect air filter for restriction

3. **Resolution:**
   - If seal leak: Replace seals ($1,500)
   - If compressor fouling: Water wash ($800)
   - If blade damage: Replace blades ($5,500)

### Vibration Alert

**Symptom:** High vibration detected, sensor_8/sensor_13 high variance

**Troubleshooting Steps:**

1. **Vibration Spectrum Analysis**
   - Attach vibration sensors
   - Record frequency spectrum
   - Identify peak frequencies

2. **Bearing Frequencies**
   - Forward bearing defect frequency: 127 Hz
   - Aft bearing defect frequency: 156 Hz
   - Fan blade passing frequency: 45 Hz × blade count

3. **Diagnosis:**
   - Peak at bearing frequency: Bearing degradation
   - Peak at blade passing: Imbalance or damaged blade
   - Broadband elevation: General wear

4. **Resolution:**
   - If bearing defect: Replace bearing ($3,500)
   - If imbalance: Balance rotor ($2,800)
   - If blade damage: Replace blade ($4,200)

---

## 9. Parts List and Costs

### Bearing Components

| Part Number | Description | Cost | Lead Time |
|-------------|-------------|------|-----------|
| 12345-B | Forward bearing assembly | $1,800 | 5-7 days |
| 12346-B | Aft bearing assembly | $2,200 | 5-7 days |
| 12346-S | Bearing seal set | $450 | 2-3 days |
| GREASE-789 | High-temp bearing grease (1 lb) | $85 | Stock |

### Temperature Sensors

| Part Number | Description | Cost | Lead Time |
|-------------|-------------|------|-----------|
| TEMP-001 | Type K thermocouple (sensor_1, sensor_2) | $220 | Stock |
| TEMP-002 | High-temp thermocouple (sensor_3, sensor_4) | $380 | 3-5 days |
| TEMP-CAL | Sensor calibration kit | $650 | Stock |

### Seals and Gaskets

| Part Number | Description | Cost | Lead Time |
|-------------|-------------|------|-----------|
| 45678-PSK | Pressure seal kit (complete) | $850 | 5-7 days |
| GASKET-SET | Engine gasket set | $420 | 3-5 days |

### Turbine Components

| Part Number | Description | Cost | Lead Time |
|-------------|-------------|------|-----------|
| 23456-TB | Turbine blade set (HPT) | $12,500 | 14-21 days |
| 90123-BS | Turbine blade set (LPT) | $8,200 | 14-21 days |
| 78901-CV | Coolant valve set | $1,450 | 7-10 days |

### Fuel System

| Part Number | Description | Cost | Lead Time |
|-------------|-------------|------|-----------|
| 34567-FN | Fuel nozzle set (12) | $2,800 | 10-14 days |
| 34568-FP | Fuel pump assembly | $4,200 | 14-21 days |

### Compressor Components

| Part Number | Description | Cost | Lead Time |
|-------------|-------------|------|-----------|
| 56789-AF | Air filter set | $320 | Stock |
| WASH-KIT | Compressor wash system | $180 | Stock |

---

## 10. Safety Warnings

### Critical Safety Procedures

**DANGER - HOT SURFACES**
- Engine surfaces can remain hot (>200°F) for 4+ hours after shutdown
- Always check temperature before touching components
- Use thermal imaging camera when possible
- Wear heat-resistant gloves rated to 400°F

**DANGER - ROTATING EQUIPMENT**
- NEVER approach engine without lockout/tagout in place
- Verify zero electrical power
- Check for stored energy (compressed air, springs)
- Ensure all personnel clear before engine start

**DANGER - FUEL SYSTEM**
- Fuel system remains pressurized after shutdown
- Relieve pressure before disconnecting lines
- No open flames or sparks within 50 feet
- Use explosion-proof tools only

**DANGER - TOXIC MATERIALS**
- Engine cleaning solvents are toxic
- Wear appropriate respirator (NIOSH approved)
- Ensure adequate ventilation
- Dispose of waste per EPA regulations

### Personal Protective Equipment

Required for all maintenance operations:
- Safety glasses with side shields
- Steel-toed safety boots
- Hearing protection (>85 dB areas)
- Heat-resistant gloves (bearing work)
- Chemical-resistant gloves (cleaning operations)
- Hard hat (engine removal/installation)

---

## 11. References

### Related Documents

- **DOC-BEAR-002:** Bearing Inspection Procedures (detailed visual inspection criteria)
- **DOC-TEMP-003:** Temperature Sensor Troubleshooting Guide
- **DOC-VIB-004:** Vibration Analysis Guide
- **DOC-PM-005:** Predictive Maintenance Best Practices

### External Resources

- NASA C-MAPSS Dataset Documentation
- Manufacturer Service Bulletins (GE Aviation, Rolls-Royce, Pratt & Whitney)
- OSHA 1910.147 - Lockout/Tagout Standard
- EPA 40 CFR Part 262 - Hazardous Waste Regulations

### Training Requirements

- Engine-specific training (manufacturer certified)
- Lockout/tagout certification
- Confined space entry (if applicable)
- Hazardous materials handling
- First aid/CPR certification recommended

### Revision History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-12-01 | Initial release | Predictive Maintenance Agent |

---

**END OF DOCUMENT**

For questions or clarifications, contact the maintenance engineering department.
