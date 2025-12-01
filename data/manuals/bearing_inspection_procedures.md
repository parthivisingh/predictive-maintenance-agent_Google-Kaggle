# Bearing Inspection Procedures

**Document ID:** DOC-BEAR-002
**Version:** 1.0
**Last Updated:** December 1, 2025
**Applies To:** Turbofan engine bearing assemblies

---

## Table of Contents

1. [Introduction](#introduction)
2. [Visual Inspection Criteria](#visual-inspection-criteria)
3. [Measurement Procedures](#measurement-procedures)
4. [Wear Tolerance Limits](#wear-tolerance-limits)
5. [Failure Indicators](#failure-indicators)
6. [Sensor Correlation Analysis](#sensor-correlation-analysis)
7. [Replacement Decision Matrix](#replacement-decision-matrix)
8. [Inspection Equipment](#inspection-equipment)
9. [Safety Requirements](#safety-requirements)

---

## 1. Introduction

Bearing assemblies are critical components in turbofan engines, supporting high-speed rotating shafts under extreme temperatures and loads. Regular inspection prevents catastrophic failures and reduces maintenance costs.

### Purpose

This procedure provides standardized methods for:
- Visual bearing inspection and defect identification
- Dimensional measurement and wear quantification
- Correlation of physical wear with sensor readings
- Go/no-go decisions for bearing replacement

### Applicable Bearings

This procedure covers:
- Forward bearing assemblies (P/N 12345-B)
- Aft bearing assemblies (P/N 12346-B)
- Intermediate bearing assemblies (P/N 12347-B)

### Inspection Frequency

Perform bearing inspections:
- Every B-check (2,000 operating hours)
- When sensor data indicates degradation (sensor_3, sensor_9, sensor_11 elevated)
- After any vibration event
- Following any bearing-related maintenance

---

## 2. Visual Inspection Criteria

### Pre-Inspection Preparation

1. **Clean the Bearing**
   - Remove all oil, grease, and debris
   - Use clean solvent (P/N SOLV-100)
   - Dry with compressed air (< 30 psi, filtered)
   - Handle with lint-free gloves only

2. **Lighting Setup**
   - Use high-intensity LED inspection light (>1000 lumens)
   - Position light at 30-45 degree angle
   - Use magnifying glass (5x-10x) for detail inspection

### Normal Bearing Condition

A bearing in good condition exhibits:

**Inner and Outer Races:**
- Smooth, mirror-like finish
- Uniform color (typically silver-gray)
- No discoloration patterns
- Rolling element paths show polishing only

**Rolling Elements (Balls or Rollers):**
- Perfectly spherical or cylindrical shape
- Uniform size across all elements
- No surface marks or scratches
- Consistent surface finish

**Cage:**
- No deformation or cracks
- Pockets show minimal wear
- Rivets tight and intact
- Uniform spacing maintained

### Degraded Bearing Indicators

**Minor Degradation (Monitor, No Replacement):**
- Light polishing on races (normal wear)
- Very minor surface scratches (<0.001" deep)
- Slight discoloration in non-critical areas
- Cage shows minor polishing

**Moderate Degradation (Plan Replacement):**
- Visible wear paths on races
- Surface roughness detectable by fingernail
- Discoloration patterns indicating heat
- Cage shows measurable wear in pockets

**Severe Degradation (Immediate Replacement):**
- Pitting on race surfaces
- Spalling (material flaking off)
- Deep grooves or scratches
- Cracks visible in races or cage
- Severe discoloration (blue, brown, black)
- Rolling elements not uniform in size
- Cage deformed or cracked

### Specific Defect Identification

**Pitting**
- Small craters on race surface
- Typically 0.005-0.020" diameter
- Indicates fatigue failure beginning
- **Action:** Replace bearing

**Spalling**
- Larger areas where material has flaked away
- Typically >0.050" area
- Leaves sharp edges
- **Action:** Replace immediately, inspect mating surfaces

**Fretting**
- Fine rust-like powder in race contact area
- Indicates micro-movement between parts
- Common at bearing seat interfaces
- **Action:** Replace bearing, inspect housing for proper fit

**False Brinelling**
- Wear marks at ball positions
- Occurs during transport/storage vibration
- Appears as evenly-spaced depressions
- **Action:** Replace if >0.002" deep

**True Brinelling**
- Indentations from impact loads
- Irregular pattern
- Indicates shock loading event
- **Action:** Replace bearing, investigate shock cause

**Corrosion**
- Rust or oxidation on surfaces
- Indicates moisture contamination
- Rough surface texture
- **Action:** Replace bearing, check oil system for water

**Heat Discoloration**
- Blue, brown, or black oxide colors
- Indicates overheating (>300°F)
- Correlates with sensor_3, sensor_9 elevation
- **Action:** Replace bearing, investigate cooling system

**Smearing**
- Metal transfer between rolling elements and races
- Indicates excessive slip or skidding
- Shiny, smeared appearance
- **Action:** Replace bearing, check lubrication system

---

## 3. Measurement Procedures

### Required Measurements

1. **Race Diameter Measurement**

   **Inner Race ID:**
   - Use inside micrometer or bore gauge
   - Measure at 4 locations (90° apart)
   - Record to 0.0001" precision
   - Compare to specification: 2.5000" ±0.0005"

   **Outer Race OD:**
   - Use outside micrometer
   - Measure at 4 locations (90° apart)
   - Record to 0.0001" precision
   - Compare to specification: 4.0000" ±0.0005"

2. **Race Width Measurement**

   - Use vernier caliper or depth micrometer
   - Measure at 4 locations around circumference
   - Record to 0.001" precision
   - Compare to specification: 1.000" ±0.005"

3. **Rolling Element Diameter**

   **For Ball Bearings:**
   - Use ball micrometer
   - Measure all balls individually
   - Record to 0.00001" precision
   - Specification: 0.5000" ±0.00005"
   - All balls must be within 0.0001" of each other

   **For Roller Bearings:**
   - Use roller micrometer
   - Measure diameter and length of each roller
   - Record to 0.0001" precision
   - Verify all rollers are within tolerance

4. **Cage Measurements**

   - Pocket diameter: Use pin gauges
   - Cage concentricity: Use dial indicator
   - Rivet tightness: Visual and tactile check
   - Record any deviations from as-new condition

5. **Surface Roughness**

   - Use surface roughness tester (profilometer)
   - Measure in rolling element path
   - New bearing: Ra < 4 micro-inches
   - Acceptable: Ra < 8 micro-inches
   - Replace if: Ra > 12 micro-inches

### Measurement Documentation

Create inspection report including:
- Date and inspector name
- Bearing P/N and serial number
- All dimensional measurements
- Photographs of any defects
- Comparison to previous inspection (if available)
- Sensor correlation data
- Replacement recommendation

---

## 4. Wear Tolerance Limits

### Dimensional Tolerances

| Measurement | New | Acceptable Wear | Reject Limit |
|-------------|-----|-----------------|--------------|
| Inner race ID | 2.5000" ±0.0005" | +0.0015" max | +0.0025" |
| Outer race OD | 4.0000" ±0.0005" | -0.0015" max | -0.0025" |
| Race width | 1.000" ±0.005" | -0.010" max | -0.015" |
| Ball diameter | 0.5000" ±0.00005" | -0.0002" max | -0.0004" |
| Ball diameter variation | < 0.0001" | < 0.0003" | > 0.0005" |
| Surface roughness | Ra < 4 μin | Ra < 8 μin | Ra > 12 μin |

### Visual Defect Limits

| Defect Type | Acceptable | Reject |
|-------------|------------|--------|
| Pitting | None | Any pitting visible |
| Spalling | None | Any spalling visible |
| Scratches | < 0.001" deep, <5% area | > 0.001" deep or >5% area |
| Discoloration | Light straw color | Blue, brown, or black |
| Corrosion | None | Any visible corrosion |
| Cracks | None | Any cracks visible |

### Operating Hour Limits

Even if measurements are acceptable, replace bearings based on operating hours:

- **Forward bearing:** 15,000 hours maximum
- **Aft bearing:** 12,000 hours maximum (higher load)
- **Intermediate bearing:** 18,000 hours maximum

If sensor data shows degradation, reduce these limits by 30%.

---

## 5. Failure Indicators

### Early Stage Failure (0-25% Life Remaining)

**Physical Indicators:**
- Very fine pitting beginning to appear
- Slight surface roughness increase
- Minor discoloration (straw color)
- Cage pockets show polishing

**Sensor Indicators:**
- sensor_3 elevated 5-10 units above baseline
- sensor_9 shows slight upward trend
- sensor_11 elevated 0.2-0.4 units
- Vibration spectrum shows slight increase at bearing frequencies

**Action:** Plan replacement at next scheduled maintenance

### Mid Stage Failure (25-50% Life Remaining)

**Physical Indicators:**
- Visible pitting on race surfaces
- Measurable surface roughness
- Heat discoloration (light brown)
- Cage wear visible in pockets

**Sensor Indicators:**
- sensor_3 elevated 10-15 units above baseline
- sensor_9 increasing steadily
- sensor_11 elevated 0.5-0.8 units
- Clear vibration signature at bearing defect frequencies

**Action:** Schedule replacement within 50 operating hours

### Late Stage Failure (50-75% Life Remaining)

**Physical Indicators:**
- Extensive pitting or beginning spalling
- Significant surface roughness
- Dark heat discoloration
- Cage showing cracks or deformation

**Sensor Indicators:**
- sensor_3 elevated >15 units above baseline
- sensor_9 elevated >25 units
- sensor_11 elevated >1.0 units
- Strong vibration, possible audible noise

**Action:** Replace immediately, ground aircraft/shutdown equipment

### Critical Failure (75-100% Life Remaining)

**Physical Indicators:**
- Active spalling with material loss
- Severe heat damage
- Cage broken or severely deformed
- Metal particles in oil

**Sensor Indicators:**
- sensor_3 >20 units above baseline
- sensor_9 >30 units above baseline
- sensor_11 >1.5 units
- Excessive vibration, definite abnormal noise

**Action:** IMMEDIATE SHUTDOWN - Risk of catastrophic failure

---

## 6. Sensor Correlation Analysis

### Understanding Sensor-Bearing Relationships

**sensor_3 (LPT Outlet Temperature):**
- Directly affected by bearing friction
- 10-unit increase typically indicates 0.002" wear on race
- Gradual increase over 100+ cycles: normal wear
- Rapid increase over 10-20 cycles: accelerated degradation

**sensor_9 (Pressure Sensor):**
- Indirectly affected by bearing clearance changes
- Increases as bearing clearance grows
- 20-30 unit increase correlates with 0.003-0.005" clearance increase
- Trend analysis more important than absolute value

**sensor_11 (Bearing Cavity Pressure):**
- Most direct bearing health indicator
- Increases with bearing clearance
- 0.5 unit increase suggests early degradation
- 1.0 unit increase indicates significant wear

### Correlation Examples

**Case 1: Normal Bearing**
- sensor_3: 1405 (baseline 1405)
- sensor_9: 2388 (baseline 2388)
- sensor_11: 14.62 (baseline 14.62)
- **Assessment:** Bearing in excellent condition

**Case 2: Early Degradation**
- sensor_3: 1413 (baseline 1405) → +8 units
- sensor_9: 2398 (baseline 2388) → +10 units
- sensor_11: 14.85 (baseline 14.62) → +0.23 units
- **Assessment:** Early wear, plan replacement in 1000-2000 hours

**Case 3: Moderate Degradation**
- sensor_3: 1418 (baseline 1405) → +13 units
- sensor_9: 2410 (baseline 2388) → +22 units
- sensor_11: 15.12 (baseline 14.62) → +0.50 units
- **Assessment:** Moderate wear, replace within 200-500 hours

**Case 4: Severe Degradation**
- sensor_3: 1426 (baseline 1405) → +21 units
- sensor_9: 2425 (baseline 2388) → +37 units
- sensor_11: 15.85 (baseline 14.62) → +1.23 units
- **Assessment:** Severe wear, immediate replacement required

### Trend Analysis Guidelines

Monitor sensor trends over time:

**Normal Degradation Rate:**
- sensor_3: 0.5-1.0 units per 1000 hours
- sensor_9: 1-2 units per 1000 hours
- sensor_11: 0.02-0.04 units per 1000 hours

**Accelerated Degradation (Action Required):**
- sensor_3: >2 units per 1000 hours
- sensor_9: >5 units per 1000 hours
- sensor_11: >0.08 units per 1000 hours

Plot sensor values over operating hours to identify:
- Linear trends (normal wear)
- Exponential trends (accelerating failure)
- Step changes (sudden damage events)

---

## 7. Replacement Decision Matrix

### Decision Tree

**Step 1: Visual Inspection**
- Any cracks, spalling, or severe pitting? → REPLACE
- Severe discoloration (blue/black)? → REPLACE
- Otherwise → Proceed to Step 2

**Step 2: Measurements**
- Any dimension outside reject limits? → REPLACE
- Surface roughness > 12 μin? → REPLACE
- Ball diameter variation > 0.0005"? → REPLACE
- Otherwise → Proceed to Step 3

**Step 3: Operating Hours**
- Hours > maximum for bearing type? → REPLACE
- Hours > 75% of maximum + sensor elevation? → REPLACE
- Otherwise → Proceed to Step 4

**Step 4: Sensor Analysis**
- sensor_3 > baseline + 15 units? → REPLACE
- sensor_9 > baseline + 25 units? → REPLACE
- sensor_11 > baseline + 1.0 units? → REPLACE
- Sensor trending shows acceleration? → PLAN REPLACEMENT
- Otherwise → CONTINUE MONITORING

### Cost-Benefit Analysis

**Preventive Replacement:**
- Labor cost: $1,200
- Parts cost: $2,500
- Downtime cost: $8,000 (8 hours @ $1,000/hour)
- **Total:** $11,700

**Failure Replacement:**
- Labor cost: $2,800 (more extensive disassembly)
- Parts cost: $3,500 (bearing + damaged mating surfaces)
- Downtime cost: $32,000 (16 hours emergency + lost production)
- Additional damage: $15,000-$25,000 (possible shaft, housing damage)
- **Total:** $53,300-$63,300

**Savings:** $41,600-$51,600 by replacing proactively

### Replacement Schedule Optimization

Based on sensor trends, optimize replacement timing:

**Scenario A: Slow Degradation**
- sensor_3 increasing 0.8 units/1000 hours
- Current elevation: +8 units
- Projected to +15 units (replacement threshold): ~8,750 hours
- **Recommendation:** Schedule at next B-check if within 2,000 hours

**Scenario B: Moderate Degradation**
- sensor_3 increasing 2.5 units/1000 hours
- Current elevation: +12 units
- Projected to +15 units: ~1,200 hours
- **Recommendation:** Schedule dedicated maintenance in 800-1,000 hours

**Scenario C: Rapid Degradation**
- sensor_3 increasing 5 units/1000 hours
- Current elevation: +14 units
- Projected to +15 units: ~200 hours
- **Recommendation:** Replace immediately, do not exceed 100 operating hours

---

## 8. Inspection Equipment

### Required Tools

| Tool | Purpose | P/N | Calibration |
|------|---------|-----|-------------|
| Inside micrometer 2-3" | Inner race ID measurement | MICRO-250 | Annual |
| Outside micrometer 3-5" | Outer race OD measurement | MICRO-450 | Annual |
| Ball micrometer | Ball diameter measurement | MICRO-BALL | Annual |
| Depth micrometer | Race width measurement | MICRO-DEPTH | Annual |
| Surface roughness tester | Surface finish verification | ROUGH-100 | Semi-annual |
| Dial indicator 0.0001" | Runout and concentricity | DIAL-001 | Annual |
| Pin gauge set | Cage pocket measurement | PIN-SET | None required |
| Magnifying glass 10x | Visual inspection | MAG-10X | None required |
| LED inspection light | Visual inspection | LED-1000 | None required |
| Digital camera | Documentation | CAM-DIGI | None required |

### Calibration Requirements

All measurement tools must be calibrated per ISO 17025 standards:
- Micrometers: Annual calibration, traceable to NIST
- Surface roughness tester: Semi-annual calibration
- Keep calibration certificates on file for audit

---

## 9. Safety Requirements

### Personal Protective Equipment

- Safety glasses with side shields (REQUIRED)
- Nitrile gloves (for handling solvents)
- Clean room gloves (for handling cleaned bearings)
- Hearing protection if using compressed air

### Hazardous Materials

**Cleaning Solvents:**
- Use in well-ventilated area only
- Avoid skin contact
- Dispose per EPA regulations
- Keep away from heat sources

**Compressed Air:**
- Never exceed 30 psi for cleaning
- Always use filtered, dry air
- Point away from body and face
- Wear safety glasses

### Bearing Handling

- Never spin bearing with compressed air (can cause injury)
- Handle only by outer race when possible
- Support bearing weight - do not drop
- Keep bearings clean - contamination causes failure

---

**END OF DOCUMENT**

**Related Documents:**
- DOC-TF-001: Turbofan Maintenance Guide
- DOC-TEMP-003: Temperature Sensor Troubleshooting
- DOC-VIB-004: Vibration Analysis Guide

For questions, contact bearing engineering specialist.
