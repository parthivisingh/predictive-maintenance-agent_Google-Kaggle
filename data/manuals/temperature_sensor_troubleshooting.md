# Temperature Sensor Troubleshooting Guide

**Document ID:** DOC-TEMP-003
**Version:** 1.0
**Last Updated:** December 1, 2025
**Applies To:** NASA C-MAPSS temperature sensors (sensor_1 through sensor_21)

---

## Table of Contents

1. [Introduction](#introduction)
2. [Sensor Locations and Normal Ranges](#sensor-locations-and-normal-ranges)
3. [Common Failure Modes](#common-failure-modes)
4. [Diagnostic Procedures for High Readings](#diagnostic-procedures-for-high-readings)
5. [Diagnostic Procedures for Low Readings](#diagnostic-procedures-for-low-readings)
6. [Sensor Replacement Procedures](#sensor-replacement-procedures)
7. [Calibration Requirements](#calibration-requirements)
8. [Troubleshooting Flowcharts](#troubleshooting-flowcharts)

---

## 1. Introduction

Temperature sensors are critical for monitoring turbofan engine health. The NASA C-MAPSS system uses 21 sensors to monitor various engine locations. Accurate sensor readings enable early detection of degradation and prevent catastrophic failures.

### Purpose

This guide provides:
- Normal operating ranges for all temperature sensors
- Diagnostic procedures for abnormal readings
- Differentiation between sensor failure and actual temperature issues
- Step-by-step troubleshooting workflows
- Replacement and calibration procedures

### Sensor Technology

All temperature sensors use Type K thermocouples except where noted:
- **Type K:** Chromel-Alumel, range -200°C to +1350°C
- **Type N:** Nicrosil-Nisil, range -270°C to +1300°C (high-temp locations)
- **RTD (PT100):** Platinum resistance, range -200°C to +850°C (precision locations)

---

## 2. Sensor Locations and Normal Ranges

### Primary Temperature Sensors

#### sensor_1: LPC Inlet Temperature
- **Location:** Fan inlet, upstream of low-pressure compressor
- **Type:** Type K thermocouple
- **Normal Range:** 518-520 units (normalized)
- **Physical Temperature:** 15-25°C (59-77°F) at sea level
- **Function:** Ambient air temperature monitoring
- **Criticality:** Medium - affects performance calculations

**Normal Behavior:**
- Varies with ambient conditions
- Should match atmospheric temperature
- Minimal change during engine operation

**Abnormal Patterns:**
- Reading >530: Sensor drift or contamination
- Reading <510: Sensor failure or ice formation
- Rapid fluctuations: Loose connection or damaged wire

#### sensor_2: HPC Discharge Temperature
- **Location:** High-pressure compressor outlet, before combustor
- **Type:** Type K thermocouple
- **Normal Range:** 640-660 units
- **Physical Temperature:** 400-450°C (752-842°F)
- **Function:** Compressor efficiency monitoring
- **Criticality:** High - indicates compressor health

**Normal Behavior:**
- Increases slowly during engine startup
- Stabilizes during steady-state operation
- Gradual increase (0.5-1 unit/1000 hours) indicates normal wear

**Abnormal Patterns:**
- Reading >670: Compressor fouling or blade erosion
- Reading <630: Sensor drift or compressor damage
- Rapid increase: Possible compressor surge
- Oscillating: Unstable combustion or sensor fault

#### sensor_3: LPT Outlet Temperature
- **Location:** Low-pressure turbine exhaust
- **Type:** Type N thermocouple (high temperature)
- **Normal Range:** 1400-1410 units
- **Physical Temperature:** 550-600°C (1022-1112°F)
- **Function:** Turbine efficiency and bearing temperature
- **Criticality:** Very High - key bearing degradation indicator

**Normal Behavior:**
- Stable during steady-state operation
- Correlates with power output
- Increases 10-15 units with bearing degradation

**Abnormal Patterns:**
- Reading >1425: Bearing degradation or cooling failure
- Reading <1390: Sensor failure or fuel system issue
- Sudden jump >5 units: Sensor fault, not physical
- Gradual increase >2 units/1000 hours: Accelerated bearing wear

#### sensor_4: HPT Inlet Temperature
- **Location:** High-pressure turbine inlet, post-combustor
- **Type:** Type N thermocouple (ultra-high temperature)
- **Normal Range:** 1580-1620 units
- **Physical Temperature:** 1200-1400°C (2192-2552°F)
- **Function:** Combustion monitoring, turbine protection
- **Criticality:** Critical - exceeding limits causes turbine damage

**Normal Behavior:**
- Highest temperature in engine
- Directly proportional to fuel flow
- Increases with power demand

**Abnormal Patterns:**
- Reading >1635: Overheating - reduce power immediately
- Reading >1650: Critical - shutdown required
- Reading <1570: Sensor failure or fuel system fault
- Oscillating: Combustion instability
- Step change: Sensor drift or failure

### Secondary Temperature Sensors

#### sensor_5 through sensor_10: Various Compressor Locations
- **Normal Ranges:** 400-800 units depending on location
- **Function:** Detailed compressor performance mapping
- **Criticality:** Medium

#### sensor_11: Bearing Cavity Temperature
- **Location:** Main bearing housing
- **Type:** Type K thermocouple
- **Normal Range:** 14.5-14.8 units (normalized)
- **Physical Temperature:** 80-120°C (176-248°F)
- **Function:** Direct bearing health monitoring
- **Criticality:** Very High

**Normal Behavior:**
- Stable during operation
- Slight increase with bearing wear

**Abnormal Patterns:**
- Reading >15.0: Bearing degradation
- Reading >15.5: Bearing failure imminent
- Rapid increase: Lubrication failure

#### sensor_12: Fuel Flow Ratio (Temperature-Based)
- **Location:** Fuel system manifold
- **Type:** PT100 RTD
- **Normal Range:** 1.28-1.32 units (ratio)
- **Function:** Fuel system efficiency
- **Criticality:** High

#### sensor_13 through sensor_19: Turbine and Exhaust
- **Normal Ranges:** 900-1600 units depending on location
- **Function:** Turbine section monitoring
- **Criticality:** High

#### sensor_20 and sensor_21: Coolant Bleed Temperature
- **Location:** Turbine coolant bleed system
- **Type:** Type K thermocouple
- **Normal Ranges:** 38-40 units (sensor_20), 23-24 units (sensor_21)
- **Physical Temperature:** 300-400°C
- **Function:** Cooling system efficiency
- **Criticality:** High - critical for turbine life

---

## 3. Common Failure Modes

### Sensor Drift

**Description:** Gradual shift in sensor output over time

**Causes:**
- Thermocouple wire degradation from high temperature exposure
- Junction contamination
- Insulation breakdown
- Thermal cycling fatigue

**Symptoms:**
- Reading shifts 3-10 units over months
- Usually shifts higher (positive drift)
- Stable reading, not fluctuating

**Diagnosis:**
- Compare to redundant sensor if available
- Check historical trend - is shift gradual?
- Physical inspection shows no obvious damage

**Resolution:**
- Recalibrate if drift <5 units
- Replace if drift >5 units or recurring

**Cost:** $220-$380 per sensor + 2 hours labor

### Open Circuit

**Description:** Broken wire or failed connection

**Causes:**
- Vibration-induced wire breakage
- Corrosion at connection points
- Physical damage during maintenance
- Thermal expansion/contraction cycling

**Symptoms:**
- Reading drops to minimum scale (often -459°F or 0 units)
- Error code on display
- Abrupt failure, not gradual
- Reading does not respond to engine changes

**Diagnosis:**
- Check resistance between sensor leads (should be 4-8 ohms for Type K)
- Open circuit shows infinite resistance
- Inspect wiring for visible breaks

**Resolution:**
- Check connections first - clean and tighten
- If wire damaged, replace sensor
- Cannot repair open thermocouple

**Cost:** $220-$380 per sensor + 1-2 hours labor

### Short Circuit

**Description:** Insulation failure causing wire contact

**Causes:**
- Insulation melted from overheating
- Wire chafing against metal surfaces
- Moisture ingress causing conduction
- Crushing during installation

**Symptoms:**
- Reading drops to near-zero or incorrect value
- Reading appears plausible but doesn't respond to changes
- Intermittent readings if short is inconsistent

**Diagnosis:**
- Measure resistance to ground (should be >10 megohms)
- Short circuit shows low resistance to ground (<1 megohm)
- Insulation resistance test with megohmmeter

**Resolution:**
- Replace sensor - shorts cannot be reliably repaired
- Inspect wire routing to prevent recurrence
- Check for heat damage on adjacent components

**Cost:** $220-$380 per sensor + 1.5-2.5 hours labor

### Contamination

**Description:** Foreign material affecting sensor junction

**Causes:**
- Oil vapor deposition
- Carbon buildup from combustion
- Salt from marine environments
- Dust and debris

**Symptoms:**
- Sluggish response to temperature changes
- Reading lower than actual temperature
- Gradual onset over weeks/months
- Cleaning temporarily improves accuracy

**Diagnosis:**
- Remove sensor and inspect junction
- Dark deposits or oily residue visible
- Cleaning shows immediate improvement

**Resolution:**
- Clean sensor with appropriate solvent
- If contamination returns quickly, address source
- Replace if cleaning doesn't restore accuracy

**Cost:** $50 cleaning + 1 hour labor, or $220-$380 replacement

### Junction Degradation

**Description:** Thermocouple junction deteriorates from heat

**Causes:**
- Prolonged exposure to temperatures >90% of rated max
- Thermal cycling (heat/cool cycles)
- Oxidation at high temperatures
- Grain growth in thermocouple metals

**Symptoms:**
- Decreasing output over time
- Increased noise in signal
- Loss of calibration
- Usually affects high-temp sensors (sensor_3, sensor_4)

**Diagnosis:**
- Sensor shows age and thermal cycles
- Comparison to new sensor shows deficit
- Other causes ruled out

**Resolution:**
- Replace sensor
- Cannot repair junction degradation
- Preventive replacement based on operating hours

**Cost:** $380 per high-temp sensor + 2 hours labor

---

## 4. Diagnostic Procedures for High Readings

### Initial Assessment

**Step 1: Determine if Reading is Physically Possible**

- Is the high reading consistent with engine operation?
- Are correlated sensors also high (e.g., sensor_3 and sensor_4 together)?
- Is the reading beyond physical limits (>1700 for any sensor)?

**If reading is impossible (>1700 or illogical):**
→ Sensor fault confirmed, proceed to sensor replacement

**If reading is high but plausible:**
→ Proceed to Step 2

**Step 2: Check Trend History**

- Review past 100 operating cycles
- Is increase gradual (>10 cycles) or sudden (<3 cycles)?
- Are other related sensors showing similar trends?

**If sudden increase:**
→ Likely sensor drift or failure, proceed to sensor testing

**If gradual increase:**
→ Likely real physical condition, proceed to physical diagnosis

**Step 3: Check for Correlated Sensor Patterns**

**High sensor_3 alone:**
- Bearing degradation likely
- Check sensor_9, sensor_11 for confirmation
- If sensor_9 and sensor_11 normal, suspect sensor_3 drift

**High sensor_4 alone:**
- Combustor issue or sensor drift
- Check fuel flow sensor_12
- If fuel flow normal, suspect sensor_4 drift

**High sensor_3 AND sensor_4 together:**
- True overheating condition
- Check cooling system (sensor_20, sensor_21)
- Urgent action required if >20 units above baseline

### Physical vs. Sensor Fault Differentiation

**Indicators of Physical Temperature Increase:**
1. Multiple correlated sensors elevated
2. Gradual increase over 50-100 cycles
3. Increase correlates with operating conditions
4. Other performance parameters affected (vibration, pressure)
5. Sensor resistance checks normal

**Indicators of Sensor Fault:**
1. Single sensor elevated, others normal
2. Sudden change in 1-5 cycles
3. Reading doesn't respond to power changes
4. Sensor resistance abnormal
5. Historical pattern shows sensor drift

### Sensor Testing Procedure

**Resistance Check:**
1. Shut down engine and lockout
2. Disconnect sensor at junction box
3. Measure resistance between sensor leads:
   - Type K: 4-8 ohms normal
   - Type N: 5-10 ohms normal
   - PT100: 100 ohms at 0°C
4. Measure resistance to ground:
   - Should be >10 megohms
   - <1 megohm indicates insulation failure

**Voltage Check:**
1. With sensor connected, engine at operating temperature
2. Measure millivolt output at junction box
3. Compare to temperature/voltage tables for thermocouple type
4. Deviation >2% indicates drift

**Resolution Decision:**

- If resistance or voltage test fails → Replace sensor
- If tests pass but reading still high → Investigate physical cause
- If uncertain → Compare to calibrated reference sensor

---

## 5. Diagnostic Procedures for Low Readings

### Initial Assessment

**Step 1: Check for Open Circuit**

Low readings often indicate open circuit failure:
- Reading at minimum scale (often 0 or -459°F display)
- Error code present
- No response to temperature changes

**Test:** Measure resistance between sensor leads
- Infinite resistance = open circuit → Replace sensor
- Normal resistance → Proceed to Step 2

**Step 2: Evaluate Reading Plausibility**

- Is reading below ambient temperature? (Impossible)
- Is reading lower than inlet temperature? (Check logic)
- Are related sensors also low?

**If reading is impossibly low:**
→ Sensor fault confirmed

**If reading is low but possible:**
→ Check for physical causes

### Common Low Reading Causes

**Fuel System Issues (sensor_4, sensor_3 low):**
- Reduced fuel flow
- Clogged fuel nozzles
- Fuel pump degradation
- Check sensor_12 (fuel flow ratio)

**Compressor Issues (sensor_2 low):**
- Compressor damage
- Inlet restriction
- Blade erosion
- Check pressure sensors for confirmation

**Sensor Sheath Damage:**
- Thermocouple junction not in gas stream
- Sheath bent or crushed
- Improper installation depth
- Visual inspection required

### Diagnostic Testing

**Thermal Shock Test:**
1. Record sensor reading at idle
2. Increase power to 50%
3. Monitor sensor response time
4. Good sensor: Responds within 2-5 seconds
5. Degraded sensor: Slow response (>10 seconds)
6. Failed sensor: No response

**Comparative Test:**
1. Install calibrated reference sensor nearby
2. Compare readings at various power levels
3. Difference >3% indicates drift
4. Pattern of difference indicates fault type

---

## 6. Sensor Replacement Procedures

### Pre-Replacement Steps

1. **Verify Correct Replacement Part**
   - Consult parts manual for exact P/N
   - Verify thermocouple type matches
   - Check probe length and thread size

2. **Prepare Workspace**
   - Lockout/tagout engine
   - Allow engine to cool (<100°F)
   - Gather tools and new sensor
   - Review installation procedure

### Removal Procedure

1. **Disconnect Electrical**
   - Disconnect sensor lead at junction box
   - Label wires for correct reconnection
   - Cap connector to prevent contamination

2. **Remove Sensor**
   - Loosen compression fitting or mounting nut
   - Carefully unthread sensor probe
   - Inspect hole for damage or debris
   - Clean mounting threads

**Caution:** Do not force sensor removal. If seized, apply penetrating oil and wait 30 minutes.

### Installation Procedure

1. **Prepare New Sensor**
   - Verify part number one final time
   - Inspect for shipping damage
   - Check that protective cap is removed

2. **Install Sensor**
   - Apply anti-seize compound to threads (high-temp rated)
   - Insert sensor to proper depth (mark on probe)
   - Hand-tighten, then wrench to specification:
     - 1/8" sensors: 12 ft-lbs
     - 1/4" sensors: 18 ft-lbs
     - 1/2" sensors: 25 ft-lbs
   - Do not overtighten - can damage sensor

3. **Route Wiring**
   - Secure lead wire away from hot surfaces
   - Use thermal insulation sleeving
   - Avoid sharp bends (minimum 2" radius)
   - Secure with high-temp cable ties

4. **Connect Electrical**
   - Connect leads per wiring diagram
   - Verify polarity (positive lead to positive terminal)
   - Check connection security
   - Seal connector against moisture

### Post-Installation Verification

1. **Resistance Check**
   - Measure sensor resistance (should match specifications)
   - Measure insulation resistance (>10 megohms)

2. **System Check**
   - Power up monitoring system
   - Verify sensor reading appears on display
   - Reading should be near ambient temperature

3. **Functional Test**
   - Run engine through power cycle
   - Verify sensor responds appropriately
   - Compare to historical baseline
   - Document new baseline reading

---

## 7. Calibration Requirements

### Calibration Frequency

- **Annual calibration:** All sensors
- **After replacement:** Immediate calibration verification
- **After overheating event:** Affected sensors
- **When drift suspected:** On-demand calibration

### Field Calibration Procedure

**Equipment Required:**
- Calibrated temperature source (dry block calibrator)
- Precision multimeter (0.01 mV resolution)
- Thermocouple reference tables
- Calibration worksheet

**Procedure:**

1. **Remove Sensor** from engine
2. **Clean Sensor** junction area
3. **Insert into Calibrator** set to 3 test points:
   - Low: 100°C (212°F)
   - Mid: 500°C (932°F)
   - High: 1000°C (1832°F) - for high-temp sensors only
4. **Measure Output** at each temperature
5. **Compare to Tables** for that thermocouple type
6. **Record Deviation** at each point
7. **Pass Criteria:** <2% deviation at all points

**If sensor fails calibration:**
- Replace if >5% deviation
- Acceptable to use with correction factor if 2-5% deviation
- Document correction in system calibration file

### System Calibration

Beyond individual sensors, verify complete system:
- Junction box connections
- Signal conditioning modules
- A/D converter calibration
- Display calibration

Requires certified calibrator with NIST traceability.

---

## 8. Troubleshooting Flowcharts

### High Temperature Reading Flowchart

```
High Temperature Alarm
         |
         v
Is reading >1700 (impossible)?
    |              |
   Yes            No
    |              |
    v              v
Sensor       Gradual increase
Fault        (>10 cycles)?
Replace           |         |
              Yes         No
               |           |
               v           v
          Check for    Sudden jump
          Physical     Sensor drift
          Causes       Replace
               |
               v
          Multiple sensors high?
               |         |
              Yes       No
               |         |
               v         v
          True     Single sensor
          Overheating  Check sensor
          (Investigate resistance
          root cause)  Likely drift
```

### Low Temperature Reading Flowchart

```
Low Temperature Alarm
         |
         v
Check sensor resistance
         |
         v
Infinite resistance?
    |         |
   Yes       No
    |         |
    v         v
Open      Reading responds
Circuit   to power changes?
Replace      |         |
           Yes       No
            |         |
            v         v
        Check fuel  Sensor
        system &    degradation
        physical    Replace
        causes
```

### Sensor Replacement Decision

```
Sensor Issue Detected
         |
         v
Failed calibration?
    |         |
   Yes       No
    |         |
    v         v
Replace   Drift >5 units?
             |         |
            Yes       No
             |         |
             v         v
         Replace   Operating
                   hours >5000?
                      |      |
                     Yes    No
                      |      |
                      v      v
                  Replace  Continue
                           Monitoring
```

---

**END OF DOCUMENT**

**Related Documents:**
- DOC-TF-001: Turbofan Maintenance Guide
- DOC-BEAR-002: Bearing Inspection Procedures
- DOC-VIB-004: Vibration Analysis Guide

For sensor technical support, contact instrumentation engineering.
