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
- [11. Next Steps](#11-next-steps)

---

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

```bash
git clone https://github.com/Cforgion/rnra_measurement_gui
cd rnra_measurement_gui
pip install -r requirements.txt
```

> **Note:** Use PowerShell (Windows), Terminal (macOS), or your preferred shell (Linux).

### Running

Once the setup is done, to run the code at any time you need to be in the folder `rnra_measurement_gui` and run the following command:

```bash
python main.py
```

Alternatively, you can use VS Code to run the code by opening the project folder and clicking the "Run" button, provided Python is properly configured in VS Code.

---

## 3. Modular Workflow Concept

The software is structured into **four independent modules**:

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

The workflow is driven by Excel configuration files. Each file corresponds to a **specific entry point in the pipeline**.

* `input_mpa.xlsx` → raw acquisition conversion setup  
  ➜ start from `.mpa` files

* `input_loop.xlsx` → excitation profile construction  
  ➜ start from calibrated `.txt` spectra

* `input_anova.xlsx` → statistical analysis (ANOVA)  
  ➜ start from processed excitation profiles

📁 Example files are available in the `/examples` folder.

---

## 5. Processing Modules

### 5.1 Conversion Module (Raw → Spectra)

**Tab: Conversion**

#### Purpose

Convert raw `.mpa` files into usable `.txt` spectra.

#### Entry condition

* Requires: `input_mpa.xlsx`

#### Actions

* Load configuration file
* Select sample/day root
* Define output folder
* Run conversion

#### Output

* `.txt` spectra (channel, counts)
* Dead-time corrected files

#### Can be used independently

Yes — this module is only needed if starting from raw data.

---

### 5.2 Calibration Module (Channel → Energy)

**Tab: Calibration**

#### Purpose

Build energy calibration:

\[ E = aC + b \]

#### Entry condition (flexible)

* Requires: `.txt` spectra
* Can come from:
  * Conversion module, OR
  * external pre-processed data

#### Actions

* Load spectrum
* Select peaks
* Fit Gaussian peaks
* Perform linear calibration

#### Output

Calibration coefficients (a, b) stored either in:
- the main configuration file (conversion config file), or
- a separate exported `.txt` file

#### Can be used independently

Yes. The Calibration module works with any `.txt` spectra (from the Conversion module or from external sources).

Calibration results can be:
- exported to a standalone `.txt` file for later use, or
- optionally written back to the project configuration file for automatic integration with the Processing workflow.

---

### 5.3 Processing Module (Excitation Profiles)

**Tab: Processing**

#### Purpose

Build excitation profiles and perform advanced analysis.

#### Entry condition

* Requires: `input_loop.xlsx`
* Requires: existing calibration

#### Actions

* Define ROI in energy
* Run integration loop
* Normalize by charge
* Optional:
  * peak removal
  * sigmoid fitting

#### Output

* Excitation profiles (Energy vs NC)
* Filtered datasets
* Sigmoid fit parameters

#### Can be used independently

Yes — if a calibration already exists.

---

### 5.4 ANOVA Module (Statistical Analysis)

**Tab: ANOVA**

#### Purpose

Evaluate repeatability and random uncertainty.

#### Entry condition

* Requires: `input_anova.xlsx`
* Requires: excitation profiles

#### Output

* p-value
* variance decomposition
* random uncertainty estimate

---

## 6. Interface Description

This section describes the graphical interface for each tab in detail.

### 6.1 Conversion Tab

The **Conversion** tab performs batch conversion of raw `.mpa` acquisition files into structured `.txt` spectra.

#### Layout and controls

- **Configuration file (Excel)**
  - Read-only text field displaying the path to the global configuration Excel file
  - **Browse** button to select the configuration file (e.g., `config.xlsx`)

- **Day root (sample name root)**
  - Text entry where the user enters the day or sample root (e.g., `250317`)
  - This value filters rows in the configuration file corresponding to a given measurement day

- **Output folder for .txt files**
  - Text entry displaying the path where converted `.txt` files will be written
  - **Browse** button to choose or create this directory

- **Conversion controls**
  - **Convert .mpa → .txt** button to start the conversion for the selected day
  - Progress bar indicating current file index and total number of files
  - Status label showing "Waiting", "Conversion in progress…", "Finished", or "Finished with errors"

- **Log window**
  - Multi-line text area showing detailed messages about folders, files, and errors

#### User actions

1. **Load the configuration file**
   - Click **Browse** in the "config Excel" section
   - Select the Excel configuration file describing your measurements
   - The selected path appears in the read-only entry

2. **Define the day root**
   - In the **day root** entry, type the day/sample root (e.g., `250317`)
   - The software looks for rows in the configuration file matching this root

3. **Choose the output folder for `.txt` files**
   - Click **Browse** and select a directory
   - The program creates a subfolder named after the day root (e.g., `.../250317/`)

4. **Launch the conversion**
   - Click **Convert .mpa → .txt**
   - Progress is displayed in the progress bar and log

5. **Check for errors**
   - At the end, any errors are listed in the log area
   - The status label indicates success or errors

#### Output text file structure

For each `.mpa` file and ADC channel, one `.txt` file is generated:

- **File naming**: `filename_ADCname.txt`  
  Example: `sample01_ADC1.txt`

- **File content**:
  1. **Header line**: Dead time factor (e.g., `Dead time factor = 1.023`)
  2. **Data lines**: Two columns — `Channel` (integer) and `Count` (measured counts)

---

### 6.2 Calibration Tab

The **Calibration** tab builds an energy calibration curve \(E = a \cdot C + b\) from `.txt` spectra.

#### Layout and controls

- **Left panel – File and peak management**
  - **Load spectrum** button to select a `.txt` spectrum file
  - File information labels showing filename and dead time factor
  - Peak selection area with instruction label and interval display
  - **Energy (keV)** entry field for reference energy
  - **Fit Gaussian** button to launch peak fit
  - **Reset selection** button to clear current selection
  - **Peak list (Treeview)** with columns: Index, Channel, Energy (keV)
  - **Delete selected peak** and **Clear all peaks** buttons
  - **Run calibration** button (enabled when ≥2 peaks defined)
  - Calibration result label

- **Center panel – Spectrum and fits**
  - Matplotlib figure displaying spectrum (counts vs. channel)
  - Interactive **SpanSelector** for channel interval selection
  - Zoom/pan tools (Matplotlib toolbar)
  - Fitted peaks shown as vertical lines and Gaussian curves

- **Right panel – Detailed results and export**
  - Text area listing spectrum info, peak fit details, and calibration results
  - **Export results** button to save peaks and calibration summary

#### User actions

1. **Load a spectrum**
   - Click **Load spectrum** and select a `.txt` file
   - The spectrum is displayed with dead time factor

2. **Select a peak**
   - Click and drag on the spectrum (SpanSelector), OR
   - Simply click to set an approximate center
   - The selection is displayed as `center = ..., width = ...`

3. **Associate a reference energy**
   - Type the known energy in the **Energy (keV)** entry

4. **Fit a Gaussian peak**
   - Click **Fit Gaussian**
   - The peak is fitted and added to the Treeview

5. **Repeat for all calibration peaks**
   - Add ≥2 peaks to enable calibration

6. **Run the linear calibration**
   - Click **Run calibration**
   - The software performs weighted linear regression \(E = a \cdot C + b\)
   - Results: slope \(a\), intercept \(b\), uncertainties, \(R^2\), relative RMS

7. **Update the configuration file (if applicable)**
   - Calibration results can be written back to the configuration file

8. **Export calibration results (optional)**
   - Click **Export results** to save peaks and calibration summary

---

### 6.3 Processing Tab

The **Processing** tab controls the full data-processing pipeline: ROI integration, peak removal, and sigmoid fitting.

#### Layout and controls

- **Configuration and ROI (left panel)**
  - **Configuration file** section with path display and **Load** button
  - **ROI selection** entry (energy range in keV)
  - **Choose ROI on a spectrum** button for interactive selection
  - **Save results** checkbox and output folder entry with **Browse** button
  - **Process files** button to start the loop

- **Carbon build-up peak removal**
  - **Energy center (keV)**: resonance energy (default ~6385 keV)
  - **Search window (keV)**: energy window for peak search
  - **Removal half-width (keV)**: interval to remove
  - **Remove build-up peak** button

- **Sigmoid fitting**
  - **Run sigmoid fit on output profiles** button

- **Visualization options**
  - **Display output profile** button to view `.xlsx` or `.png` files

- **Right panel – Plot and detailed log**
  - Matplotlib figure with axes labeled "Energy (keV)" and "NC"
  - Zoom/pan toolbar
  - Text area for detailed log messages

#### User actions

**A. Loop over ROI**

1. **Load the configuration file**
   - Click **Load Excel configuration file**
   - The program checks required columns

2. **Define the ROI in energy**
   - **Manual**: type ROI in keV (e.g., `6400–6600 keV`)
   - **Interactive**: click **Choose ROI on a spectrum** to select graphically

3. **Choose whether to save results**
   - Check **Save results** and choose output folder, or use temp directory

4. **Run the processing loop**
   - Click **Process files**
   - For each scenario, the program integrates counts, normalizes by charge, and builds excitation profiles

**B. Peak removal (optional)**

1. **Set the build-up energy and windows**
   - Keep default (6385 keV) or adjust

2. **Apply the removal to all profiles**
   - Click **Remove build-up peak**
   - Filtered profiles saved in `filtered/` subfolder

**C. Sigmoid fit**

1. **Select the input folder for fitting**
   - Uses `filtered/` if peak removal was performed, otherwise raw output

2. **Run the sigmoid fits**
   - Click **Run sigmoid fit on output profiles**
   - Extracts plateau values, midpoint, width
   - Results saved to output directory

**D. Visualization**

1. **Open a processed profile or image**
   - Click **Display output profile**
   - Select `.xlsx` or `.png` file

2. **Inspect the result**
   - Profile plotted with optional error bars
   - Images displayed directly

---

### 6.4 ANOVA Tab

The **ANOVA** tab performs statistical analysis for repeatability and random uncertainty estimation.

#### User actions

1. **Load ANOVA input file**
   - Provide an Excel file (e.g., `input_anova.xlsx`) with grouped data

2. **Run ANOVA analysis**
   - The software computes p-value, variance decomposition, and random uncertainty

3. **View results**
   - Results displayed in text area and diagnostic plots saved

---

## 7. Typical Workflow

This section summarizes the recommended end-to-end workflow.

1. **Configure and convert**
   - Prepare the Excel configuration file
   - Use the **Conversion** tab to convert `.mpa` files to `.txt` spectra

2. **Calibrate energy**
   - In the **Calibration** tab, load spectra, identify peaks, and run calibration
   - Store calibration coefficients in the configuration file

3. **Process profiles**
   - In the **Processing** tab, define ROI and run the loop
   - Optionally remove carbon build-up peak

4. **Fit and analyze**
   - Perform sigmoid fits on excitation profiles
   - Use exported files for further analysis and ANOVA

---

## 8. Output Files

The application generates several categories of output files:

- **Converted spectra (`.txt`)**
  - Location: subfolder named after day root (e.g., `.../250317/`)
  - One file per `.mpa` and ADC channel
  - Header: dead time factor; body: channel, count pairs

- **Calibration exports**
  - Optional `.txt` files with peak list and calibration parameters
  - Calibration coefficients may also be written to configuration Excel file

- **Loop / ROI integration outputs**
  - Excel files with excitation profiles: energy, normalized counts, uncertainties
  - Organized per sample/scenario

- **Filtered profiles (after peak removal)**
  - Stored in `filtered/` subfolder

- **Sigmoid fit results and images**
  - Numerical summaries of fit parameters
  - Plots (`.png`) showing data and fitted curves

These outputs can be used in subsequent analysis scripts and statistical post-processing (ANOVA, uncertainty propagation).

---

## 9. Full Pipeline (Optional)

If starting from raw data:

```
Conversion → Calibration → Processing → ANOVA
```

---

## 10. Key Design Principle

The software does **not** enforce a strict pipeline.

Instead:

> Each module is independent but interoperable through standardized file formats.

This allows:

* starting at any stage
* reprocessing only part of the workflow
* integrating external datasets
* iterative calibration and analysis

---

## 11. Next Steps

- For detailed scientific methodology and uncertainty propagation, see `METHODOLOGY.md`.
- For example input files, check the `/examples` folder.
- For questions or issues, open an issue on [GitHub](https://github.com/Cforgion/rnra_measurement_gui/issues).
