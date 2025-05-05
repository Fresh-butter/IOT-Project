# Train Tracking System - Trial Runs Overview

## Summary
This document outlines the trial runs conducted to test the GPS & RFID-based Train Collision Avoidance System. Seven trial runs were executed testing various aspects of the system including basic functionality, collision detection, route deviation monitoring, and alert generation capabilities.

## Trial Run #1: Basic System Functionality
**Date & Time:** April 19, 2025, 09:30-10:45 IST  
**Trains Involved:** Train 201 (OBH Express)  
**Purpose:** Verify basic hardware and software integration  
**Description:**  
Initial test to verify GPS tracking, data transmission to backend. Train 201 was operated along Route R201 (Nilgiri to OBH) to test end-to-end data flow.

**Results:**
- ✅ Successfully established connection between hardware module and backend API
- ✅ Log entries generated at 6-second intervals and saved in database
- ✅ RFID detection successful

## Trial Run #2: Alert Generation for Train Status Changes
**Date & Time:** April 19, 2025, 11:00-12:30 IST  
**Trains Involved:** Train 203 (Main-Gate-Parijat Express)  
**Purpose:** Test alert generation for train status changes  
**Description:**  
Train 203 was operated with planned stops and starts to test the system's ability to detect status changes and generate appropriate alerts.

**Results:**
- ✅ System correctly detected when train stopped at unscheduled locations
- ✅ Status change alerts triggered when train stopped and resumed movement
- ✅ Alerts contained accurate timestamp and location information

## Trial Run #3: Route Deviation Detection
**Date & Time:** April 19, 2025, 13:15-14:30 IST  
**Trains Involved:** Train 207 (OBH-Nilgiri Express)  
**Purpose:** Test route deviation detection capabilities  
**Description:**  
Train 207 was deliberately operated off its designated route (R207) to test the system's ability to detect deviations.

**Results:**
- ✅ System detected deviation when train moved >20m away from designated route
- ✅ Warning alert generated with correct deviation distance
- ✅ Location coordinates in alert matched actual deviation point
- ✅ System recognized return to route when train moved back to designated path
- ❌ RFID reading at OBH checkpoint failed due to tag malfunction


## Trial Run #4: Collision Detection 
**Date & Time:** April 20, 2025, 09:00-10:30 IST  
**Trains Involved:** Train 201 (OBH Express) and Train 207 (OBH-Nilgiri Express)  
**Purpose:** Test collision detection  
**Description:**  
Trains were operated on same routes to test if collision detection triggers appropriately.

**Results:**
- ❌ System failed to detect potential collision risk
- ✅ Train position tracking remained accurate throughout the test
- ✅ RFID checkpoint detection functioned correctly for both trains


## Trial Run #5: Collision Detection - After Algorithm Adjustment
**Date & Time:** April 20, 2025, 11:30-13:00 IST  
**Trains Involved:** Train 201 (OBH Express) and Train 207 (OBH-Nilgiri Express)  
**Purpose:** Retest collision detection after algorithm adjustment  
**Description:**  
After adjusting the collision detection algorithm, the same test scenario was repeated

**Results:**
- ✅ System successfully detected collision risks when distance fell below 15m 
- ✅ Alert contained accurate location coordinates of potential collision point
- ✅ Resolution Alerts triggered when trains stopped running

## Trial Run #6: Complete System Check - Parallel Routes
**Date & Time:** April 20, 2025, 14:00-15:15 IST  
**Trains Involved:** Train 201 (OBH Express) and Train 207 (OBH-Nilgiri Express)  
**Purpose:** Test system with trains running on parallel routes in opposite directions  
**Description:**  
Train 201 operated on Route R201 (Nilgiri to OBH) while Train 207 operated on Route R207 (OBH to Nilgiri) simultaneously, testing the system's ability to avoid false alerts.

**Results:**
- ✅ Both trains tracked accurately throughout their routes
- ✅ System correctly identified trains were on separate parallel tracks
- ✅ No false collision alerts generated despite trains passing each other
- ✅ All RFID checkpoints correctly detected for both trains
- ✅ Status change alerts properly generated when trains stopped at stations

