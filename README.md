# RNRA Data Processing and Error Management

## Description

This project provides a graphical user interface for processing RNRA (Resonant Nuclear Reaction Analysis) data, from raw acquisition files to excitation profiles, fitted sigmoid parameters, and statistical analysis.

The application automates the main data-reduction steps used in hydrogen profiling measurements based on the \(^{15}\mathrm{N}\) nuclear resonance:
- conversion of raw `.mpa` files into structured `.txt` spectra,
- energy calibration by Gaussian peak fitting and linear regression,
- ROI integration and charge normalization,
- optional carbon build-up peak removal,
- sigmoid fitting of excitation profiles,
- statistical analysis through ANOVA.

The tool was developed in the context of thin-layer analysis and hydrogen depth profiling, with a focus on reproducible data processing and practical uncertainty handling.

## Scientific Context

The software is designed for experiments based on **Resonant Nuclear Reaction Analysis (RNRA)**, where the measured gamma yield is studied as a function of beam energy in order to characterize hydrogen distributions in matter.

The current workflow includes:
- extraction of spectra from raw acquisition files and application of dead-time correction factors;
- energy calibration from identified reference peaks;
- construction of excitation profiles by integrating counts within a selected ROI and normalizing by integrated charge;
- optional filtering of parasitic build-up peaks;
- sigmoid fitting to extract parameters such as plateau difference and shape descriptors;
- ANOVA-based statistical analysis for repeatability and random uncertainty assessment.

## Features

- Batch conversion of `.mpa` acquisition files to `.txt` spectra.
- Automatic extraction of live time and real time metadata, and computation of dead-time correction factors.
- Interactive calibration interface with:
  - peak selection on spectra,
  - Gaussian peak fitting,
  - linear calibration \(E = aC + b\),
  - uncertainty-related calibration outputs.
- ROI integration and normalization by integrated charge to build excitation profiles.
- Optional removal of build-up peaks in a selected energy range.
- Sigmoid fitting of processed excitation profiles with export of numerical results and figures.
- ANOVA analysis tab for statistical comparison of grouped data and evaluation of random variability.
- Centralized Excel-based configuration for paths, file ranges, ADC channels, and calibration parameters.
- Practical uncertainty propagation at several stages of the workflow, including counting statistics, calibration-related contributions, and normalization terms.

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
pip install -r requirements.txt
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

## Launch the application

From the project root, run:

```bash
python main.py
```


This opens the GUI with four tabs:
- **0. Conversion MPA → TXT**
- **1. Étalonnage**
- **2. Traitement**
- **3. ANOVA**

## Typical Workflow

1. **Prepare the Excel configuration file**  
   Define sample names, folders, file ranges, ADC channels, and calibration-related parameters.

2. **Convert raw acquisition files (`.mpa` → `.txt`)**  
   In the **Conversion** tab, select the configuration file, choose the day or sample root, define the output folder, and run the conversion.

3. **Perform the energy calibration**  
   In the **Calibration** tab, load one or more `.txt` spectra, identify calibration peaks, fit Gaussians, and run the linear calibration.  
   Calibration coefficients can then be exported or written back to the configuration file.

4. **Build excitation profiles**  
   In the **Traitement** tab, load the appropriate configuration, define the ROI, and run the processing loop to integrate counts and normalize by charge.

5. **Optionally remove build-up peaks**  
   Use the dedicated controls in the processing tab to remove parasitic peaks in a selected energy window.

6. **Fit sigmoid curves**  
   Apply the sigmoid fit to raw or filtered excitation profiles and export the fitted parameters and figures.

7. **Run ANOVA analysis**  
   In the **ANOVA** tab, load an Excel file containing grouped values (for example sigmoid-derived parameters such as `diff_height`) and run the statistical analysis.

## Project Structure

A typical project structure is:

```text
rnra_measurement_gui/
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
├── temp/
├── data/
└── results/
```

## Typical Outputs

Depending on the selected workflow, the application can generate:
- `.txt` spectra containing channel/count values and dead-time factor information;
- `.xlsx` files containing excitation profiles with energy, normalized counts, and propagated uncertainties;
- filtered profile files after peak removal;
- sigmoid fit result files and corresponding figures;
- Excel files containing grouped sigmoid-derived quantities for further statistical analysis;
- ANOVA result text files and optional diagnostic plots.

## Uncertainty Handling

The software includes uncertainty handling at several key stages of the workflow.

In the current implementation, this mainly includes:
- calibration-related uncertainty contributions used during profile construction;
- counting-statistics contributions;
- uncertainty terms associated with normalization by integrated charge;
- propagated uncertainties stored in processed excitation-profile outputs and reused in later steps when available.

This uncertainty treatment is intended as a practical processing model for scientific analysis. It should not yet be interpreted as a complete metrological uncertainty budget covering all possible systematic effects.

## Limitations

- The calibration model currently assumes a predominantly linear detector response over the selected energy range.
- Dead-time correction relies on metadata extracted from `.mpa` files; missing or corrupted headers may prevent reliable correction.
- The current uncertainty model is simplified and may not include every systematic contribution relevant for a full metrological analysis.
- Peak removal and sigmoid fitting should always be checked visually before final interpretation.
- Input Excel files must follow the expected column structure required by each processing tab.

## Author

**Cynthia Forgione**  
Master in Physics and Data Science  
Université de Namur