# RNRA Data Processing and Error Management

## Description

This project provides a graphical user interface for processing RNRA (Resonant Nuclear Reaction Analysis) data, from raw acquisition files to excitation profiles, fitted sigmoid parameters, and statistical analysis.  

The application automates the main data-reduction steps used in hydrogen profiling measurements based on the ¹⁵N nuclear resonance:

- conversion of raw `.mpa` files into structured `.txt` spectra,
- energy calibration by Gaussian peak fitting and linear regression,
- ROI integration in channels and charge normalization,
- optional carbon build-up peak removal,
- sigmoid fitting of excitation profiles,
- statistical analysis through ANOVA,
- construction of a practical global uncertainty budget (using relative contributions from each stage).

The tool was developed in the context of thin-layer analysis and hydrogen depth profiling, with a focus on reproducible data processing and practical uncertainty handling.

---

## Scientific Context

The software is designed for experiments based on **Resonant Nuclear Reaction Analysis (RNRA)**, where the measured gamma yield is studied as a function of beam energy in order to characterize hydrogen distributions in matter. 

The current workflow includes:

- extraction of spectra from raw acquisition files and application of dead-time correction factors stored in text headers;
- energy calibration from identified reference peaks, using Gaussian fits with a local linear background and weighted linear regression \(E = a \cdot C + b\);
- construction of excitation profiles by integrating counts within a selected ROI in channels and normalizing by integrated charge read from a dedicated charge spectrum;
- reading of energy values for each measurement point directly from Excel voltage/energy tables, instead of recomputing them from the linear calibration inside the loop;
- optional filtering of parasitic build-up peaks in excitation profiles, based on peak detection in a user-defined energy window; 
- sigmoid fitting to extract parameters such as plateau difference and shape descriptors, with per-profile fit results stored in Excel and PNG plots; 
- ANOVA-based statistical analysis for repeatability and random uncertainty assessment on grouped scalar quantities (e.g. sigmoid-derived parameters);
- aggregation of calibration, excitation-curve and sigmoid contributions into a combined relative uncertainty using a simple quadrature rule. 

---

## Features

- Batch conversion of `.mpa` acquisition files to `.txt` spectra with dead-time factors in the header.
- Extraction of live time and real time metadata for each ADC section and computation of dead-time correction factors.
- Interactive calibration interface with:
  - spectrum loading from `.txt`,
  - peak selection on spectra,
  - Gaussian peak fitting with linear background,
  - weighted linear calibration \(E = a \cdot C + b\),
  - calibration quality indicators (e.g. \(R^2\) and relative RMS error, depending on the GUI layer).
- ROI integration in channel space and normalization by integrated charge to build excitation profiles, with propagation of a pointwise uncertainty on \(N/Q\).
- Optional removal of build-up peaks in a selected energy range using peak detection and local window removal. 
- Sigmoid fitting of processed excitation profiles with:
  - extraction of fit parameters (\(L\), \(x_0\), \(k\), \(b\)),
  - derived plateau height and a global fit-parameter uncertainty measure,
  - export of numerical results to Excel and figures to PNG. 
- ANOVA analysis module for statistical comparison of grouped data and evaluation of a repeatability-related uncertainty contribution.
- Centralized Excel-based configuration for sample names, folders, file ranges, ADC channels, and paths to voltage/energy tables and calibration-related parameters used in the loop.
- Practical uncertainty handling at several stages of the workflow (conversion, profile construction, sigmoid fit, and global budget), based on the functions implemented in the `core` modules.

---

## ANOVA and Uncertainty Estimation

The ANOVA functionality is used to compare grouped values (for example sigmoid-derived quantities such as `diff_height`) and to estimate a repeatability-related component of measurement variability.

Current implementation details:

- the selected Excel columns for group and value are used to build a one-way ANOVA model of the form `value ~ C(group)` using `statsmodels`;
- the factor row corresponding to the chosen group is explicitly read from the ANOVA table;
- residual diagnostics and plots (histogram, boxplot, violin plot, Q-Q plots) are available via helper functions;
- the code computes:
  - \(MS_\text{intra}\) from the residual mean square,
  - \(MS_\text{inter}\) from the factor line,
  - `u_intra = sqrt(MS_intra)`,
  - `u_inter = sqrt((MS_inter - MS_intra) / n_per_group)` when `MS_inter > MS_intra`, with a **currently fixed** `n_per_group = 5`,
  - `u_total = sqrt(u_intra**2 + u_inter**2)`,
  - `u_rel_percent = 100 * u_total / mean(value)`.

> **Important:** the ANOVA-based uncertainty estimate relies on the assumed group
structure and on the usual ANOVA assumptions (approximate normality and
homoscedasticity of residuals). Users should check the number of repetitions
per group and the diagnostic plots when interpreting the result.

### Important caution

ANOVA-based uncertainty estimation is only meaningful when each group contains enough repeated measurements and the usual ANOVA assumptions (approximate normality and homoscedasticity of residuals) are reasonably satisfied. 

Very small sample sizes (for example 2 values in a group) can produce unstable and unrealistically large uncertainty estimates. For this reason, ANOVA results should always be interpreted together with:

- the number of groups,
- the number of repetitions per group,
- the residual degrees of freedom,
- residual diagnostic tests and plots.

As a practical guideline:

- fewer than 3 values per group: not recommended for quantitative uncertainty estimation;
- 3 values per group: minimum exploratory use;
- 5 or more values per group: preferred for more stable estimates, consistent with the current implementation.

When the number of repetitions is too small, a simpler descriptive approach (standard deviation only, or direct range) is often more appropriate than adding the ANOVA-derived term to the uncertainty budget.

---

## Installation

### Prerequisites

- Python 3.10+
- A virtual environment is strongly recommended (`venv`, `virtualenv`, or `conda`). 

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
- additional standard packages used in the GUI and plotting code (e.g. `wxPython` if present in your environment).

---

## Launch the Application

From the project root (where `main.py` is located), run:

```bash
 cd .\src\
python main.py
```

This opens the GUI with four main tabs:

- **0. Conversion** – batch conversion of `.mpa` files to `.txt` spectra, with dead-time factors. 
- **1. Calibration** – interactive energy calibration from `.txt` spectra. 
- **2. Processing** – ROI integration in channels, charge normalization, optional peak removal, and profile export. 
- **3. ANOVA** – statistical analysis and uncertainty estimation for grouped scalar results. 

> **Note:** Tab labels in the interface may appear in French (`Conversion`, `Étalonnage`, `Traitement`, `ANOVA`). The names above are their English equivalents used throughout this documentation. 

---

## Typical Workflow

1. **Prepare the Excel configuration files**  
   Define sample names, folders, file ranges, ADC channels, calibration-related parameters, and the paths to voltage/energy Excel files used in the processing loop.

2. **Convert raw acquisition files (`.mpa` → `.txt`)**  
   In the **Conversion** tab, select the configuration file (e.g. `input_mpa.xlsx`), choose the day or sample root, define the output folder, and run the conversion. 

3. **Perform the energy calibration**  
   In the **Calibration** tab, load one or more `.txt` spectra, identify calibration peaks, fit Gaussians, and run the linear calibration. Calibration coefficients and quality indicators can be displayed and exported; depending on the GUI workflow, they may also be written back into a configuration file. 

4. **Build excitation profiles**  
   In the **Processing** tab, load the appropriate configuration file, choose ROI bounds in channels, and run the processing loop. The loop reads the corresponding `.txt` ADC and charge files, integrates counts, applies dead-time correction, normalizes by charge, and associates each point with its energy from the voltage/energy Excel tables. Profiles are exported as Excel files. 

5. **Optionally remove build-up peaks**  
   Still in the Processing workflow, use the peak-removal functions to clean parasitic build-up peaks in a selected energy window. Cleaned profiles are saved with `_cleaned` suffix and diagnostic figures are generated. 

6. **Fit sigmoid curves**  
   Apply the sigmoid fit to raw or cleaned excitation profiles to extract plateau height and shape parameters. The code saves a summary Excel file (e.g. `fit_results.xlsx`), per-profile fit data, and PNG figures showing data + fitted curve. 

7. **Run ANOVA analysis and uncertainty budget**  
   In the **ANOVA** tab, load an Excel file containing grouped values (e.g. sigmoid-derived `diff_height`), select the group and value columns, and run the analysis. Use the results together with the uncertainty-budget tool to build an overall combined relative uncertainty. 

---

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
├── data/
│   └── temp/
└── docs/
    ├── 1-USER_GUIDE.md
    └── 2-SCIENTIFIC_METHOD.md
```



---

## Typical Outputs

Depending on the selected workflow, the application can generate:

- `.txt` spectra containing channel/count values and dead-time factor information in the header;
- `.xlsx` files containing excitation profiles with energy, normalized counts (`N/C`), and propagated uncertainties;
- filtered profile files after peak removal (named with `_cleaned` suffix) and corresponding PNG plots; 
- sigmoid fit result files (such as `fit_results.xlsx`) and fit images; 
- Excel files containing grouped sigmoid-derived quantities (e.g. `diff_height` and associated uncertainty) for statistical analysis; 
- ANOVA result text/log outputs and diagnostic plots (histograms, boxplots, violin plots, Q-Q plots);
- a global uncertainty budget (in the GUI) summarizing relative contributions from calibration, excitation curves and sigmoid fits, and the resulting combined uncertainty. 

---

## Uncertainty Handling

The software includes uncertainty handling at several key stages:

- **During ROI integration and normalization**:  
  For each excitation-profile point, the code computes an uncertainty on \(N/Q\) that combines counting statistics on \(N\), a calibration/ROI contribution controlled by a relative parameter, and a term associated with the integrated charge.

- **During calibration**:  
  Linear fit uncertainties and residual scatter can be summarized as a relative RMS calibration contribution and passed to the uncertainty budget.

- **During sigmoid fitting**:  
  The covariance matrix of the fit is used to build a global measure of uncertainty on plateau-related parameters, which is stored as a relative contribution in the budget. 

- **Global budget**:  
  The module `core/uncertainty.py` takes relative contributions from the
  calibration stage and from the sigmoid-fit stage (both expressed in percent),
  converts them to standard relative uncertainties, and combines them in
  quadrature to obtain a combined relative uncertainty. The profile-point
  uncertainties enter the budget through the weighted sigmoid fit and are not
  added again as a separate contribution. 

This uncertainty treatment is intended as a **practical processing model** for scientific analysis. It should not yet be interpreted as a complete metrological uncertainty budget covering all possible systematic effects (e.g. long-term drifts, detector instabilities, sample inhomogeneity). 

---

## Limitations

- The calibration model currently assumes a predominantly linear detector response over the selected energy range.
- Dead-time correction relies on metadata extracted from `.mpa` files; missing, inconsistent or corrupted headers may lead to a default factor of 1.0 and reduce correction accuracy.
- The current uncertainty model is simplified and does not include all potential systematic contributions relevant for a full metrological analysis. 
- Peak removal and sigmoid fitting are sensitive to noisy profiles and to the choice of window parameters; results should always be checked visually. 
- ANOVA-based uncertainty estimation assumes a one-way model and relies on
  the chosen group structure and on the way an effective number of observations
  per group is defined in the current implementation. The method is therefore
  tailored to the experimental designs used during development and may need
  adaptation for more general cases.
- Input Excel files must follow the expected column structure required by each processing tab; otherwise, the processing loop may fail or skip entries.

---

## Author

**Cynthia Forgione**  
Master in Physics and Data Science  
Université de Namur