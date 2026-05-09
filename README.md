# RNRA Data Processing and Error Management

## Description

This project provides a graphical user interface for processing RNRA (Resonant Nuclear Reaction Analysis) data, from raw acquisition files to excitation profiles, fitted sigmoid parameters, and statistical analysis.

The application automates the main data-reduction steps used in hydrogen profiling measurements based on the ¹⁵N nuclear resonance:
- conversion of raw `.mpa` files into structured `.txt` spectra,
- energy calibration by Gaussian peak fitting and linear regression,
- ROI integration and charge normalization,
- optional carbon build-up peak removal,
- sigmoid fitting of excitation profiles,
- statistical analysis through ANOVA.

The tool was developed in the context of thin-layer analysis and hydrogen depth profiling, with a focus on reproducible data processing and practical uncertainty handling.

---

## Scientific Context

The software is designed for experiments based on **Resonant Nuclear Reaction Analysis (RNRA)**, where the measured gamma yield is studied as a function of beam energy in order to characterize hydrogen distributions in matter.

The current workflow includes:
- extraction of spectra from raw acquisition files and application of dead-time correction factors;
- energy calibration from identified reference peaks;
- construction of excitation profiles by integrating counts within a selected ROI and normalizing by integrated charge;
- optional filtering of parasitic build-up peaks;
- sigmoid fitting to extract parameters such as plateau difference and shape descriptors;
- ANOVA-based statistical analysis for repeatability and random uncertainty assessment.

---

## Features

- Batch conversion of `.mpa` acquisition files to `.txt` spectra.
- Automatic extraction of live time and real time metadata, and computation of dead-time correction factors.
- Interactive calibration interface with:
  - peak selection on spectra,
  - Gaussian peak fitting,
  - linear calibration E = a·C + b,
  - uncertainty-related calibration outputs.
- ROI integration and normalization by integrated charge to build excitation profiles.
- Optional removal of build-up peaks in a selected energy range.
- Sigmoid fitting of processed excitation profiles with export of numerical results and figures.
- ANOVA analysis tab for statistical comparison of grouped data and evaluation of random variability.
- Centralized Excel-based configuration for paths, file ranges, ADC channels, and calibration parameters.
- Practical uncertainty propagation at several stages of the workflow, including counting statistics, calibration-related contributions, and normalization terms.

---

## ANOVA and Uncertainty Estimation

The ANOVA tab is used to compare grouped values (for example sigmoid-derived quantities such as `diff_height`) and to estimate repeatability-related variability.

Current implementation details:
- the selected Excel columns are temporarily renamed to `value` and `group` before fitting the one-way model;
- the ANOVA model is computed with `statsmodels` using `value ~ C(group)`;
- the factor row is explicitly read from `C(group)` in the ANOVA table;
- residual diagnostics may include Shapiro-Wilk, Jarque-Bera, Levene, and optional visual plots (Q-Q plot, histogram, boxplot, violin plot);
- the code computes:
  - `u_intra` from the residual mean square,
  - `u_inter` from the excess inter-group variance when applicable,
  - `u_total` as the quadratic combination of intra- and inter-group components,
  - `u_rel_percent` as the relative uncertainty in percent.

### Important caution

ANOVA-based uncertainty estimation is only meaningful when each group contains enough repeated measurements.
Very small sample sizes (for example 2 values in a group, or only 1 residual degree of freedom) can produce unstable and unrealistically large uncertainty estimates.
For this reason, ANOVA results should always be interpreted together with:
- the number of groups,
- the number of repetitions per group,
- the residual degrees of freedom,
- the residual diagnostic tests.

A practical rule is to require at least 3 repeated values per group for exploratory use, and preferably 5 or more for more stable uncertainty estimates.
When the number of repetitions is too small, a simpler descriptive approach (for example standard deviation only) is often more appropriate than adding the ANOVA-derived term to the uncertainty budget.

---

## Installation

### Prerequisites

- Python 3.10+
- A recommended virtual environment (`venv`, `virtualenv`, or `conda`)

### Clone the repository

```bash
git clone https://github.com/Cforgion/rnra_measurement_gui
cd rnra_measurement_gui
```
> **Note:** Use PowerShell (Windows), Terminal (macOS), or your preferred shell (Linux).

### Install dependencies

Install the required packages with:

```bash
pip install -r requirement.txt
```

The project uses at least the following libraries:
- `numpy`
- `scipy`
- `pandas`
- `matplotlib`
- `seaborn`
- `statsmodels`
- `pingouin`
- `tkinter` (usually included with standard Python distributions)

---

## Launch the Application

From the project root, run:

```bash
python main.py
```

This opens the GUI with four tabs:
- **0. Conversion** – batch conversion of `.mpa` files to `.txt` spectra
- **1. Calibration** – interactive energy calibration
- **2. Processing** – ROI integration, peak removal, and sigmoid fitting
- **3. ANOVA** – statistical analysis and uncertainty estimation

> **Note:** Tab labels in the interface may appear in French (`Étalonnage`, `Traitement`). The names above are their English equivalents used throughout this documentation.

---

## Typical Workflow

1. **Prepare the Excel configuration file**  
   Define sample names, folders, file ranges, ADC channels, and calibration-related parameters.

2. **Convert raw acquisition files (`.mpa` → `.txt`)**  
   In the **Conversion** tab, select the configuration file, choose the day or sample root, define the output folder, and run the conversion.

3. **Perform the energy calibration**  
   In the **Calibration** tab, load one or more `.txt` spectra, identify calibration peaks, fit Gaussians, and run the linear calibration.  
   Calibration coefficients can then be exported or optionally written back to the configuration file.

4. **Build excitation profiles**  
   In the **Processing** tab, load the appropriate configuration, define the ROI, and run the processing loop to integrate counts and normalize by charge.

5. **Optionally remove build-up peaks**  
   Use the dedicated controls in the Processing tab to remove parasitic peaks in a selected energy window.

6. **Fit sigmoid curves**  
   Apply the sigmoid fit to raw or filtered excitation profiles and export the fitted parameters and figures.

7. **Run ANOVA analysis**  
   In the **ANOVA** tab, load an Excel file containing grouped values (for example sigmoid-derived parameters such as `diff_height`) and run the statistical analysis.

---

## Project Structure

A typical project structure is:

```text
rnra_measurement_gui/src
├── main.py
├── core/
│   ├── ANOVA.py
│   ├── file_io.py
│   ├── calibration.py
│   ├── Loop_fonction.py
│   ├── Transform_functions.py
│   ├── Traitement_fonctions.py
│   └── etallonnage.py
├── gui/
│   ├── conversion_tab.py
│   ├── calibration_tab.py
│   ├── Loop_tab.py
│   └── ANOVA_tab.py
|
├── data/
|  └── temp/
```

---

## Typical Outputs

Depending on the selected workflow, the application can generate:
- `.txt` spectra containing channel/count values and dead-time factor information;
- `.xlsx` files containing excitation profiles with energy, normalized counts, and propagated uncertainties;
- filtered profile files after peak removal;
- sigmoid fit result files and corresponding figures;
- Excel files containing grouped sigmoid-derived quantities for further statistical analysis;
- ANOVA result text files and optional diagnostic plots.

---

## Uncertainty Handling

The software includes uncertainty handling at several key stages of the workflow.

In the current implementation, this mainly includes:
- calibration-related uncertainty contributions used during profile construction;
- counting-statistics contributions;
- uncertainty terms associated with normalization by integrated charge;
- propagated uncertainties stored in processed excitation-profile outputs and reused in later steps when available.

This uncertainty treatment is intended as a practical processing model for scientific analysis. It should not yet be interpreted as a complete metrological uncertainty budget covering all possible systematic effects.

---

## Limitations

- The calibration model currently assumes a predominantly linear detector response over the selected energy range.
- Dead-time correction relies on metadata extracted from `.mpa` files; missing or corrupted headers may prevent reliable correction.
- The current uncertainty model is simplified and may not include every systematic contribution relevant for a full metrological analysis.
- Peak removal and sigmoid fitting should always be checked visually before final interpretation.
- Input Excel files must follow the expected column structure required by each processing tab.

---

## Author

**Cynthia Forgione**  
Master in Physics and Data Science  
Université de Namur
