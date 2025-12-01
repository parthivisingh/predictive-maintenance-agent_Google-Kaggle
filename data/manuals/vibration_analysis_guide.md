# Vibration Analysis Guide

**Document ID:** DOC-VIB-004
**Version:** 1.0
**Last Updated:** December 1, 2025
**Applies To:** Turbofan engine rotating equipment

---

## Table of Contents

1. [Introduction](#introduction)
2. [Vibration Measurement Basics](#vibration-measurement-basics)
3. [Frequency Analysis Fundamentals](#frequency-analysis-fundamentals)
4. [Bearing Defect Frequencies](#bearing-defect-frequencies)
5. [Sensor Correlation](#sensor-correlation)
6. [Vibration Threshold Limits](#vibration-threshold-limits)
7. [Case Studies](#case-studies)
8. [Diagnostic Procedures](#diagnostic-procedures)

---

## 1. Introduction

Vibration analysis is a powerful predictive maintenance technique for detecting mechanical degradation before failure. This guide focuses on vibration analysis specific to turbofan engines, with correlation to NASA C-MAPSS sensor data.

### Why Vibration Analysis?

Rotating machinery generates vibration signatures that change with component condition:
- **Healthy equipment:** Low, stable vibration
- **Degrading components:** Increasing vibration at specific frequencies
- **Imminent failure:** High vibration amplitude and multiple frequency peaks

Early detection through vibration analysis prevents:
- Catastrophic failures ($45,000+ cost)
- Extended downtime (16+ hours)
- Secondary damage to adjacent components
- Safety incidents

### Vibration Sources in Turbofan Engines

**Normal Vibration Sources:**
- Rotor imbalance (minor, inherent)
- Bearing contact (rolling elements)
- Blade passing frequencies
- Gear meshing (if applicable)

**Abnormal Vibration Sources:**
- Bearing degradation (defects)
- Rotor imbalance (damage, debris)
- Blade damage or erosion
- Misalignment
- Loose components
- Rub (contact between rotating and stationary parts)

---

## 2. Vibration Measurement Basics

### Vibration Parameters

**Displacement:**
- Measures actual movement distance
- Units: mils (0.001 inches) peak-to-peak
- Best for low-frequency vibration (<1000 Hz)
- Typical range for turbofans: 0.1-2.0 mils

**Velocity:**
- Measures speed of movement
- Units: inches per second (in/sec) RMS or peak
- Best for mid-frequency vibration (10 Hz - 1000 Hz)
- Most commonly used parameter
- Typical range for turbofans: 0.05-0.30 in/sec

**Acceleration:**
- Measures rate of velocity change
- Units: g's (multiples of gravity) peak or RMS
- Best for high-frequency vibration (>1000 Hz)
- Sensitive to bearing defects and impacts
- Typical range for turbofans: 0.1-3.0 g's

### Sensor Placement

For turbofan engines, measure vibration at:

**Forward Bearing Location:**
- Horizontal direction
- Vertical direction
- Axial direction (along shaft)

**Aft Bearing Location:**
- Horizontal direction
- Vertical direction
- Axial direction

**Turbine Section:**
- Casing vibration (vertical)

**Recommended Sensor:** Accelerometer, 100 mV/g sensitivity, 0.5 Hz - 10 kHz range

### Measurement Technique

1. **Ensure Proper Sensor Mounting**
   - Use threaded stud mount (best) or magnetic mount (acceptable)
   - Clean mounting surface
   - Verify sensor is secure and perpendicular to surface

2. **Establish Baseline**
   - Measure on newly installed or overhauled engine
   - Record at multiple operating conditions (idle, 50%, 75%, full power)
   - Document as "baseline signature"

3. **Periodic Measurements**
   - Measure at same locations and conditions as baseline
   - Frequency: Every 500 operating hours or monthly
   - Always measure at same operating conditions for comparison

4. **Trending**
   - Plot overall vibration level vs. time
   - Plot frequency spectrum over time
   - Identify increasing trends

---

## 3. Frequency Analysis Fundamentals

### Time Domain vs. Frequency Domain

**Time Domain:**
- Shows vibration amplitude vs. time
- Good for seeing overall levels
- Difficult to identify specific faults

**Frequency Domain (FFT Spectrum):**
- Shows vibration amplitude vs. frequency
- Reveals specific fault frequencies
- Enables precise diagnosis

### Interpreting FFT Spectrum

**X-Axis:** Frequency (Hz or CPM - cycles per minute)
**Y-Axis:** Amplitude (velocity or acceleration)

**Key Peaks to Identify:**

**1X Running Speed (Fundamental Frequency):**
- Frequency = RPM / 60
- Example: 2388 RPM fan → 39.8 Hz
- Indicates imbalance if elevated

**2X Running Speed:**
- Frequency = 2 × (RPM / 60)
- Indicates misalignment or looseness

**Blade Passing Frequency (BPF):**
- Frequency = (Number of blades) × (RPM / 60)
- Example: 16-blade fan at 2388 RPM → 637 Hz
- Normal to see small peak
- Large peak indicates blade issues

**Bearing Frequencies:**
- Unique frequencies based on bearing geometry
- Indicates bearing defects when elevated
- See section 4 for calculations

### Spectral Comparison

**Healthy Spectrum:**
- Low overall amplitude (<0.15 in/sec)
- Small peak at 1X speed
- Minimal energy at other frequencies
- Smooth noise floor

**Degraded Spectrum:**
- Increased overall amplitude (>0.25 in/sec)
- Multiple harmonic peaks (1X, 2X, 3X)
- Bearing defect peaks visible
- Elevated noise floor

---

## 4. Bearing Defect Frequencies

### Bearing Geometry Parameters

For typical turbofan engine bearings:

**Forward Bearing:**
- Bearing P/N: 12345-B
- Pitch diameter (Pd): 3.250"
- Ball diameter (Bd): 0.500"
- Number of balls (n): 12
- Contact angle (θ): 15°

**Aft Bearing:**
- Bearing P/N: 12346-B
- Pitch diameter (Pd): 3.750"
- Ball diameter (Bd): 0.625"
- Number of balls (n): 10
- Contact angle (θ): 20°

### Defect Frequency Calculations

**Fundamental Train Frequency (FTF):**
- Cage rotation frequency
- FTF = 0.5 × RPM × [1 - (Bd/Pd) × cos(θ)] / 60

**Ball Pass Frequency Outer Race (BPFO):**
- Frequency at which balls pass a defect on outer race
- BPFO = (n/2) × RPM × [1 - (Bd/Pd) × cos(θ)] / 60

**Ball Pass Frequency Inner Race (BPFI):**
- Frequency at which balls pass a defect on inner race
- BPFI = (n/2) × RPM × [1 + (Bd/Pd) × cos(θ)] / 60

**Ball Spin Frequency (BSF):**
- Rotation frequency of ball around its own axis
- BSF = (Pd/Bd) × RPM × [1 - (Bd/Pd)² × cos²(θ)] / 120

### Calculated Frequencies (Forward Bearing at 2388 RPM)

| Defect Type | Frequency | Harmonics |
|-------------|-----------|-----------|
| FTF (cage) | 15.8 Hz | 31.6, 47.4, 63.2 Hz |
| BPFO (outer race) | 189.6 Hz | 379.2, 568.8 Hz |
| BPFI (inner race) | 286.4 Hz | 572.8, 859.2 Hz |
| BSF (ball) | 126.7 Hz | 253.4, 380.1 Hz |

### Calculated Frequencies (Aft Bearing at 2388 RPM)

| Defect Type | Frequency | Harmonics |
|-------------|-----------|-----------|
| FTF (cage) | 14.2 Hz | 28.4, 42.6, 56.8 Hz |
| BPFO (outer race) | 141.6 Hz | 283.2, 424.8 Hz |
| BPFI (inner race) | 226.8 Hz | 453.6, 680.4 Hz |
| BSF (ball) | 94.3 Hz | 188.6, 282.9 Hz |

### Interpreting Bearing Defect Peaks

**Outer Race Defect:**
- Strong peak at BPFO and harmonics
- Usually higher amplitude than inner race defects
- Stationary defect, constant impact

**Inner Race Defect:**
- Strong peak at BPFI and harmonics
- Amplitude may vary (modulated)
- Rotating defect, variable load

**Ball Defect:**
- Peak at BSF and harmonics
- Often accompanied by BPFO and BPFI
- Multiple balls may be affected

**Cage Defect:**
- Peak at FTF
- Unstable, may have sidebands
- Can cause erratic overall vibration

**Severity Assessment:**

| Amplitude at Defect Frequency | Condition | Action |
|-------------------------------|-----------|--------|
| <0.05 in/sec | Normal | Continue monitoring |
| 0.05-0.15 in/sec | Early defect | Increase monitoring frequency |
| 0.15-0.30 in/sec | Progressing defect | Plan replacement in 500 hours |
| >0.30 in/sec | Advanced defect | Replace within 100 hours |
| >0.50 in/sec | Severe defect | Immediate replacement |

---

## 5. Sensor Correlation

### Vibration-Sensor Relationships

Vibration increases correlate with temperature sensor changes:

**Forward Bearing Degradation:**
- Vibration increases at 189.6 Hz (BPFO) or 286.4 Hz (BPFI)
- sensor_3 (LPT outlet temperature) increases 10-15 units
- sensor_9 shows upward drift
- sensor_11 (bearing cavity pressure) increases 0.5-1.0 units

**Correlation Timeline:**

| Stage | Vibration | sensor_3 | sensor_9 | sensor_11 |
|-------|-----------|----------|----------|-----------|
| Normal | <0.05 in/sec | Baseline | Baseline | Baseline |
| Early (25%) | 0.10 in/sec | +5 units | +8 units | +0.3 units |
| Moderate (50%) | 0.20 in/sec | +12 units | +20 units | +0.7 units |
| Advanced (75%) | 0.35 in/sec | +18 units | +30 units | +1.2 units |
| Severe (90%) | >0.50 in/sec | +25 units | +40 units | +1.8 units |

**Rotor Imbalance:**
- Vibration increases at 1X speed (39.8 Hz)
- sensor_8 (fan speed) may show variance
- sensor_13, sensor_14 (core speeds) may show instability
- Temperature sensors typically stable (not friction-related)

**Blade Damage:**
- Vibration increases at BPF (637 Hz for fan)
- May see 2X BPF, 3X BPF harmonics
- Pressure sensors (sensor_7) may show pulsations
- Efficiency decreases, temperatures may rise slightly

---

## 6. Vibration Threshold Limits

### Overall Vibration Limits (Velocity)

| Location | Good | Fair | Alert | Alarm | Shutdown |
|----------|------|------|-------|-------|----------|
| Forward bearing | <0.10 | 0.10-0.20 | 0.20-0.30 | 0.30-0.50 | >0.50 |
| Aft bearing | <0.12 | 0.12-0.22 | 0.22-0.35 | 0.35-0.60 | >0.60 |
| Turbine casing | <0.15 | 0.15-0.25 | 0.25-0.40 | 0.40-0.70 | >0.70 |

Units: in/sec RMS

### Frequency-Specific Limits

**1X Running Speed:**
- Good: <0.05 in/sec
- Alert: >0.10 in/sec
- Alarm: >0.20 in/sec
- Indicates: Imbalance, need rotor balancing

**2X Running Speed:**
- Good: <0.03 in/sec
- Alert: >0.05 in/sec
- Alarm: >0.10 in/sec
- Indicates: Misalignment or looseness

**Bearing Frequencies (BPFO, BPFI):**
- Good: <0.05 in/sec
- Alert: >0.10 in/sec
- Alarm: >0.25 in/sec
- Indicates: Bearing degradation

**Blade Passing Frequency:**
- Good: <0.08 in/sec
- Alert: >0.15 in/sec
- Alarm: >0.30 in/sec
- Indicates: Blade damage or aerodynamic issue

---

## 7. Case Studies

### Case Study 1: Forward Bearing Outer Race Defect

**Background:**
- Engine operating hours: 8,200
- Last bearing replacement: 7,500 hours ago (at overhaul)
- Routine vibration measurement showed increase

**Vibration Data:**
- Overall level: 0.28 in/sec (Alert level)
- Strong peak at 189.6 Hz (BPFO)
- Amplitude at BPFO: 0.22 in/sec
- Harmonics visible at 379.2 Hz and 568.8 Hz

**Sensor Data:**
- sensor_3: 1417 (baseline 1405) → +12 units
- sensor_9: 2408 (baseline 2388) → +20 units
- sensor_11: 15.22 (baseline 14.62) → +0.60 units

**Diagnosis:** Outer race defect on forward bearing, moderate stage

**Action Taken:**
- Bearing replaced within 200 operating hours
- Post-replacement vibration: 0.08 in/sec
- sensor_3 returned to 1406
- Cost: $3,500 preventive vs. estimated $45,000 failure cost

**Lessons Learned:**
- Combined vibration and sensor analysis enabled early detection
- Prevented in-flight failure
- Saved $41,500 through proactive replacement

### Case Study 2: Rotor Imbalance from Blade Erosion

**Background:**
- Engine operating hours: 12,500
- Operating environment: Dusty industrial site
- Gradual performance decrease noted

**Vibration Data:**
- Overall level: 0.32 in/sec (Alarm level)
- Dominant peak at 1X speed (39.8 Hz)
- Amplitude at 1X: 0.25 in/sec
- No bearing defect frequencies present

**Sensor Data:**
- sensor_2: 663 (baseline 650) → +13 units
- sensor_7: 542 (baseline 555) → -13 units (decreased!)
- sensor_13: 9032 (baseline 9045) → -13 RPM
- Bearing temperatures normal

**Diagnosis:** Compressor blade erosion causing imbalance and efficiency loss

**Action Taken:**
- Borescope inspection confirmed blade erosion
- Compressor blade replacement performed
- Rotor balanced after blade replacement
- Post-maintenance vibration: 0.09 in/sec

**Cost:** $8,500 blade replacement vs. estimated $65,000 if erosion progressed to blade liberation

**Lessons Learned:**
- Imbalance (1X vibration) combined with efficiency loss (pressure, temperature sensors) indicated blade erosion
- Environmental conditions require more frequent inspections

### Case Study 3: False Alarm - Loose Sensor Mount

**Background:**
- Sudden vibration increase during routine monitoring
- Overall level: 0.45 in/sec (appeared to be alarm condition)
- No changes in engine performance

**Investigation:**
- Sensor data (sensor_3, sensor_9, sensor_11) all normal
- No temperature increase
- Frequency spectrum showed broadband increase (not specific frequencies)

**Root Cause:**
- Vibration sensor magnetic mount had weakened
- Sensor rattling on casing, measuring its own vibration

**Resolution:**
- Remounted sensor with stud mount
- Re-measured vibration: 0.11 in/sec (normal)
- No engine maintenance required

**Lessons Learned:**
- Always verify sensor mounting before committing to major maintenance
- Cross-check vibration with temperature sensors
- Broadband increase without specific peaks often indicates measurement issue

---

## 8. Diagnostic Procedures

### Procedure: Bearing Defect Detection

1. **Acquire Vibration Data**
   - Measure at bearing locations (horizontal, vertical, axial)
   - Use acceleration units for best sensitivity
   - Acquire FFT spectrum (0-2000 Hz, 3200 lines resolution)

2. **Calculate Bearing Defect Frequencies**
   - Use bearing geometry and current RPM
   - Calculate FTF, BPFO, BPFI, BSF

3. **Analyze Spectrum**
   - Look for peaks at calculated frequencies
   - Check for harmonics (2X, 3X defect frequencies)
   - Assess amplitude relative to thresholds

4. **Correlate with Sensor Data**
   - Check sensor_3, sensor_9, sensor_11 trends
   - Temperature increase confirms bearing degradation
   - No temperature increase suggests other vibration source

5. **Determine Action**
   - Use severity table (Section 6) for decision
   - Consider operating hours since last bearing change
   - Plan maintenance accordingly

### Procedure: Imbalance Detection and Balancing

1. **Identify Imbalance**
   - Dominant peak at 1X running speed
   - Typically appears in radial directions (horizontal/vertical)
   - Phase relationship between locations indicates imbalance type

2. **Determine Balancing Need**
   - 1X amplitude >0.10 in/sec: Balancing recommended
   - 1X amplitude >0.20 in/sec: Balancing required

3. **Single-Plane vs. Two-Plane Balancing**
   - If axial vibration low: Single-plane balance sufficient
   - If axial vibration high: Two-plane balance required

4. **Balancing Procedure**
   - Requires specialized balancing equipment
   - Add/remove balance weights
   - Iterative process, typically 2-3 runs
   - Target: 1X amplitude <0.05 in/sec

**Cost:** $2,800 for rotor balancing service

---

**END OF DOCUMENT**

**Related Documents:**
- DOC-TF-001: Turbofan Maintenance Guide
- DOC-BEAR-002: Bearing Inspection Procedures
- DOC-TEMP-003: Temperature Sensor Troubleshooting

For vibration analysis support, contact rotating equipment specialist.
