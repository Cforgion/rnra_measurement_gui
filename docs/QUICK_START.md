# RNRA Data Processing – Quick Start Guide

## 1. Overview

This software processes **RNRA hydrogen profiling data** from raw `.mpa` files to excitation profiles, sigmoid fits, and statistical analysis (ANOVA + uncertainty evaluation).

The workflow is designed as a **modular pipeline**, meaning each stage can be executed independently depending on available input data.

---

## 2. Installation

### Requirements

* Python ≥ 3.10
* `numpy`, `scipy`, `pandas`, `matplotlib`
* `tkinter` (standard library)

### Setup

```bash id="q1w8kx"
git clone https://github.com/Cforgion/rnra_measurement_gui
cd rnra_measurement_gui
pip install -r requirements.txt
python main.py
```

---

## 3. Modular Workflow Concept

The software is structured into **three independent modules**:

| Module      | Purpose                    | Required Input     |
| ----------- | -------------------------- | ------------------ |
| Conversion  | Convert raw `.mpa` files   | `input_mpa.xlsx`   |
| Calibration | Energy calibration         | `.txt` spectra     |
| Processing  | Excitation profiles + fits | `input_loop.xlsx`  |
| ANOVA       | Statistical analysis       | `input_anova.xlsx` |

### ⚠️ Key concept

Each module:

* can be run independently
* requires standardized inputs
* produces outputs usable by downstream modules

---

## 4. Input Files

The workflow is driven by Excel configuration files.
Each file corresponds to a **specific entry point in the pipeline**.

* `input_mpa.xlsx` → raw acquisition conversion setup
  ➜ start from `.mpa` files

* `input_loop.xlsx` → excitation profile construction
  ➜ start from calibrated `.txt` spectra

* `input_anova.xlsx` → statistical analysis (ANOVA)
  ➜ start from processed excitation profiles

📁 Example files are available in the `/example` folder.

---

## 5. Processing Modules

---

## 5.1 Conversion Module (Raw → Spectra)

**Tab: Conversion**

### Purpose

Convert raw `.mpa` files into usable `.txt` spectra.

### Entry condition

* Requires: `input_mpa.xlsx`

### Actions

* Load configuration file
* Select sample/day root
* Define output folder
* Run conversion

### Output

* `.txt` spectra (channel, counts)
* Dead-time corrected files

###  Can be used independently

Yes — this module is only needed if starting from raw data.

---

##  5.2 Calibration Module (Channel → Energy)

**Tab: Calibration**

### Purpose

Build energy calibration:

E = aC + b

### Entry condition (flexible)

* Requires: `.txt` spectra
* Can come from:

  * Conversion module, OR
  * external pre-processed data

### Actions

* Load spectrum
* Select peaks
* Fit Gaussian peaks
* Perform linear calibration

### Output
Calibration coefficients (a, b)
Stored either in:
- the main configuration file (conversion config file), or
- a separate exported .txt file
#### ⚠️ Important note (verification required)
<span style="color:red;"> It is not fully guaranteed that the calibration module can operate independently without the initial conversion configuration file. The system may still require access to the base configuration file (used in the conversion step) to ensure consistency of sample definitions and file paths. This should be verified depending on the execution mode. </span>
### Can be used independently

Yes — the calibration step can be executed separately if all required inputs are provided (spectra + reference peaks).

However:

- it may still depend on the original configuration file structure
- full standalone execution is not guaranteed in all cases


##  5.3 Processing Module (Excitation Profiles)

**Tab: Processing**

### Purpose

Build excitation profiles and perform advanced analysis.

### Entry condition

* Requires: `input_loop.xlsx`
* Requires: existing calibration

### Actions

* Define ROI in energy
* Run integration loop
* Normalize by charge
* Optional:

  * peak removal
  * sigmoid fitting

### Output

* Excitation profiles (Energy vs NC)
* Filtered datasets
* Sigmoid fit parameters

###  Can be used independently

Yes — if a calibration already exist.

---

##  5.4 ANOVA Module (Statistical Analysis)

**Tab: ANOVA**

### Purpose

Evaluate repeatability and random uncertainty.

### Entry condition

* Requires: `input_anova.xlsx`
* Requires: excitation profiles

### Output

* p-value
* variance decomposition
* random uncertainty estimate

---

## 6. Full Pipeline (optional)

If starting from raw data:

```text id="p9k2xa"
Conversion → Calibration → Processing → ANOVA
```

---

## 7. Key Design Principle

The software does NOT enforce a strict pipeline.

Instead:

> Each module is independent but interoperable through standardized file formats.

This allows:

* starting at any stage
* reprocessing only part of the workflow
* integrating external datasets
* iterative calibration and analysis

---

## 8. Outputs

* `.txt` → spectra
* `.xlsx` → excitation profiles
* `.png` → plots and diagnostics
* ANOVA reports (`.txt`, figures`)
* calibration parameters (a, b, uncertainties)

---

## 9. Summary

* Modular architecture
* Multiple entry points
* Reusable outputs between modules
* Flexible scientific workflow for RNRA analysis

