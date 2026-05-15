# RNRA Data Processing – User Guide

## Table of Contents

- [1. Overview](#1-overview)
- [2. Installation](#2-installation)
  - [Requirements](#requirements)
  - [Setup](#setup)
  - [Running](#running)
- [3. Modular Workflow Concept](#3-modular-workflow-concept)
- [4. Input Files](#4-input-files)
- [5. Processing Modules](#5-processing-modules)
  - [5.1 Conversion Module (Raw → Spectra)](#51-conversion-module-raw--spectra)
  - [5.2 Calibration Module (Channel → Energy)](#52-calibration-module-channel--energy)
  - [5.3 Processing Module (Excitation Profiles)](#53-processing-module-excitation-profiles)
  - [5.4 ANOVA Module (Statistical Analysis)](#54-anova-module-statistical-analysis)
- [6. Interface Description](#6-interface-description)
  - [6.1 Conversion Tab](#61-conversion-tab)
  - [6.2 Calibration Tab](#62-calibration-tab)
  - [6.3 Processing Tab](#63-processing-tab)
  - [6.4 ANOVA Tab](#64-anova-tab)
- [7. Typical Workflow](#7-typical-workflow)
- [8. Output Files](#8-output-files)
- [9. Full Pipeline (Optional)](#9-full-pipeline-optional)
- [10. Key Design Principle](#10-key-design-principle)
- [11. Current Status](#11-current-status)
- [12. Next Steps](#12-next-steps)

---

## 1. Overview

This software is intended for the processing of **RNRA hydrogen profiling data** from raw `.mpa` acquisition files to excitation-profile files, optional profile cleaning, sigmoid fitting, and statistical analysis. 

The project follows a **modular workflow**: conversion, calibration, profile processing, and ANOVA can be used as separate steps depending on the available input data. 

At the current stage, the code clearly implements:
- conversion of `.mpa` files into `.txt` spectra with dead-time information;
- peak-based linear calibration from channel to energy;
- ROI integration and charge normalization for excitation-profile construction;
- optional peak removal, sigmoid fitting, and ANOVA post-processing. 

---

## 2. Installation

### Requirements

- Python ≥ 3.10
- `numpy`
- `scipy`
- `pandas`
- `matplotlib`
- `tkinter` (standard library)
- Additional statistical plotting packages may be required for the ANOVA workflow depending on the environment, such as `seaborn` and `pingouin`. 

### Setup

```bash
git clone https://github.com/Cforgion/rnra_measurement_gui
cd rnra_measurement_gui
pip install -r requirements.txt
```

> **Note:** Use PowerShell (Windows), Terminal (macOS), or your preferred shell (Linux). 

### Running

Once the setup is complete, run the application from the project folder:

```bash
python main.py
```

If you use VS Code, you can also open the project folder and launch the main script from the editor, provided Python is properly configured. 

---

## 3. Modular Workflow Concept

The software is organized around **four main processing blocks**:

| Module | Purpose | Main input |
|--------|---------|------------|
| Conversion | Convert raw `.mpa` files into text spectra | Raw `.mpa` files and conversion settings |
| Calibration | Build a linear energy calibration | `.txt` spectra |
| Processing | Build excitation profiles from integrated spectra | Processing Excel file and calibrated data |
| ANOVA | Statistical analysis of grouped results | Excel table of grouped values |

Each block can be used independently if the required inputs are already available. For example, calibration can be done directly from existing `.txt` spectra, and ANOVA can be run on already exported fit results. 

---

## 4. Input Files

The workflow uses several input files depending on the entry point chosen by the user. 

Typical inputs are:

- `input_mpa.xlsx` for raw acquisition conversion settings. 
- `input_loop.xlsx` for excitation-profile construction. 
- `input_anova.xlsx` for grouped statistical analysis. 
- `.txt` spectrum files for calibration. These files contain channel/count values and may include a dead-time header generated during conversion. 

For the processing stage, the code also relies on Excel-based measurement tables and on external energy values read from Excel files during the loop. In the current implementation, energy points are not described only by the ROI definition itself; they are also retrieved from dedicated Excel data used by the loop. 

---

## 5. Processing Modules

### 5.1 Conversion Module (Raw → Spectra)

**Purpose**

Convert raw `.mpa` acquisition files into `.txt` spectra usable by the downstream workflow. 

**What the code does**

For each `.mpa` file, the converter scans ADC sections, extracts `livetime` and `realtime`, computes a dead-time factor as `realtime / livetime`, and exports one text spectrum per ADC channel. 

**Output**

Each exported `.txt` file contains:
1. a header line with the dead-time factor;
2. two data columns corresponding to channel index and counts. 

**Independent use**

Yes. This module is only required when starting from raw `.mpa` files. 

---

### 5.2 Calibration Module (Channel → Energy)

**Purpose**

Build a linear calibration of the form:

\(E = aC + b\)

from reference peaks identified in spectrum files. 

**What the code does**

The calibration module loads a `.txt` spectrum, extracts the channel/count data, optionally reads the dead-time factor from the first line, fits Gaussian peaks with a local linear background, and then performs a weighted linear regression using the fitted centroid uncertainties. 

**Current calibration model**

- Peak model: Gaussian peak with linear background. 
- Final regression: weighted linear fit \(E = aC + b\) with weights based on centroid uncertainties. 

**Output**

The code returns calibration coefficients, their uncertainties, the covariance matrix, and \(R^2\). 

**Independent use**

Yes. The calibration logic works directly from `.txt` spectra and does not require the conversion step if suitable text spectra already exist. 

> **Important:** The current code clearly computes calibration coefficients, but automatic writing of these coefficients back into a project configuration Excel file should only be documented if that behavior is explicitly confirmed in the GUI layer. 

---

### 5.3 Processing Module (Excitation Profiles)

**Purpose**

Build excitation profiles by integrating counts in a selected ROI and normalizing the result by the collected charge. 

**What the code does**

The processing loop reads measurement information from Excel input files, opens the relevant spectrum files, integrates counts inside a ROI, applies dead-time correction, computes the collected charge, and exports excitation-profile results to Excel. 

**Important implementation note**

In the current processing logic, the ROI integration is performed using **channel bounds** (`c_min`, `c_max`) and not only as a direct energy interval typed by the user. The energy associated with each output point is read separately from Excel-based input data used by the loop. 

**Optional post-processing**

Additional functions are available to:
- remove a local build-up peak near a chosen energy window from exported profile files;
- fit a sigmoid model to processed profiles and extract parameters. 

**Output**

The processing stage produces excitation-profile Excel files containing at least:
- energy values;
- normalized counts (`N/C`);
- associated uncertainties. 

---

### 5.4 ANOVA Module (Statistical Analysis)

**Purpose**

Evaluate repeatability and estimate a random uncertainty contribution from grouped measurement results. 

**What the code does**

The ANOVA function fits a one-way model, computes the ANOVA table, extracts residuals, and estimates a total uncertainty from intra-group and inter-group variance terms. 

**Current implementation note**

The present code uses `n_per_group = 5` inside the uncertainty calculation. This means the current implementation assumes five values per group for the inter-group uncertainty term and should not yet be described as fully generic. 

**Available outputs**

- ANOVA table;
- residuals;
- total uncertainty estimate;
- relative uncertainty in percent. 

The ANOVA module also includes helper functions for histogram, boxplot, violin plot, and Q-Q plot generation. 

---

## 6. Interface Description

This section describes the intended role of each tab while remaining consistent with the currently visible processing code. Some GUI details may evolve, but the scientific role of each tab is already defined by the underlying modules. 

### 6.1 Conversion Tab

The **Conversion** tab is used to batch-convert raw `.mpa` files into `.txt` spectra. 

Typical user actions are:
1. select the conversion-related input information;
2. choose an output folder;
3. launch conversion;
4. inspect conversion logs and errors. 

Each generated text file follows the pattern `baseName_ADCx.txt` and contains a dead-time header plus channel/count values. 

---

### 6.2 Calibration Tab

The **Calibration** tab is used to load a spectrum, identify reference peaks, fit them, and derive a linear channel-to-energy relation. 

The underlying calibration code supports:
- spectrum loading from `.txt`;
- dead-time header reading when present;
- Gaussian peak fitting around an approximate center and tolerance;
- weighted linear regression from fitted peak centroids. 

The exact GUI layout may evolve, but the calibration logic already corresponds to this workflow. 

---

### 6.3 Processing Tab

The **Processing** tab is dedicated to excitation-profile construction and related post-processing. 

In the current code base, the core operations are:
- loop over configured measurements;
- integrate counts in a ROI;
- normalize by collected charge;
- export profile tables;
- optionally clean profiles and fit a sigmoid. 

To avoid ambiguity, the documentation should state that the present implementation combines ROI channel integration with externally read energy values from Excel tables. It should not state that the profile is built only from a directly selected energy ROI unless that exact behavior is confirmed in the GUI code. 

---

### 6.4 ANOVA Tab

The **ANOVA** tab is intended for grouped statistical analysis of exported results such as fit parameters or other scalar quantities. 

The current analysis functions support one-way ANOVA, residual extraction, uncertainty estimation, and optional diagnostic plotting. 

Because the current uncertainty expression uses a fixed `n_per_group = 5`, users should prepare grouped datasets accordingly or treat the result as specific to that current implementation. 

---

## 7. Typical Workflow

A typical use case is:

1. Convert raw `.mpa` files into `.txt` spectra. 
2. Perform calibration from known peaks in selected spectra. 
3. Run the processing loop to build excitation profiles. 
4. Optionally remove a local build-up peak from exported profiles. 
5. Optionally fit sigmoid functions to the processed profiles. 
6. Use the exported scalar results for ANOVA-based repeatability analysis. 

This workflow is recommended, but not mandatory. Each step can be reused independently when its input files already exist. 

---

## 8. Output Files

The application can generate several categories of output files.

- **Converted spectra (`.txt`)**
  - one file per `.mpa` and ADC section;
  - dead-time factor in the header;
  - channel/count pairs in the body. 

- **Calibration results**
  - calibration coefficients and regression quality indicators returned by the calibration functions;
  - optional text export or GUI-managed reporting depending on the interface implementation. 

- **Excitation-profile files (`.xlsx`)**
  - energy values;
  - normalized counts `N/C`;
  - uncertainty values. 

- **Cleaned profile files**
  - generated after local peak removal;
  - saved as `_cleaned.xlsx`. 

- **Sigmoid-fit outputs**
  - per-profile fit curves saved to Excel;
  - summary file such as `fit_results.xlsx`;
  - plot images saved during fitting. 

- **ANOVA diagnostic plots**
  - histogram, boxplot, violin plot, and Q-Q plots when enabled in the statistical workflow. 

---

## 9. Full Pipeline (Optional)

If starting from raw data, the complete workflow is:

```text
Conversion → Calibration → Processing → Optional cleaning / sigmoid fit → ANOVA
```

This sequence matches the current project logic more closely than a stricter pipeline that would assume every step is always automated inside a single run. 

---

## 10. Key Design Principle

The software does **not** enforce a single rigid pipeline. 

Instead, the project is designed so that each module can be reused as a scientific processing block with standardized intermediate files. This makes it possible to start from raw data, existing spectra, already exported profiles, or grouped result tables depending on the analysis need. 

---

## 11. Current Status

This project should currently be presented as a **first functional version** of the RNRA processing workflow rather than as a fully finalized end-user application. 

The scientific core already includes:
- `.mpa` to `.txt` conversion with dead-time handling;
- linear calibration from fitted peaks;
- ROI-based profile construction with charge normalization;
- profile cleaning, sigmoid fitting, and ANOVA tools. 

However, documentation should remain cautious about any feature that depends on GUI behavior not explicitly verified in the current code review, such as automatic configuration-file updates or fully generic ANOVA settings. 

---

## 12. Next Steps

- For the scientific rationale and uncertainty treatment, see `2-SCIENTIFIC_METHOD.md`. 
- For example input files, use the project examples if available in the repository structure. 
- For development updates or issues, use the project GitHub repository. 