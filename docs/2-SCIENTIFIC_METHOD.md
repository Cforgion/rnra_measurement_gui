# SCIENTIFIC METHOD – RNRA Data Processing and Error Management

## Table of Contents

- [1. Introduction](#1-introduction)
- [2. Scientific Background](#2-scientific-background)
  - [2.1 Resonant Nuclear Reaction Analysis (RNRA)](#21-resonant-nuclear-reaction-analysis-rnra)
  - [2.2 Analysis of Variance (ANOVA)](#22-analysis-of-variance-anova)
  - [2.3 Uncertainty Budget – Concept](#23-uncertainty-budget--concept)
- [3. Interface Description](#3-interface-description)
  - [3.1 Conversion Window](#31-conversion-window)
  - [3.2 Calibration Window](#32-calibration-window)
  - [3.3 Processing Window](#33-processing-window)
  - [3.4 ANOVA Window](#34-anova-window)
- [4. Processing Workflow](#4-processing-workflow)
- [5. Output Files](#5-output-files)
- [6. Methodological Details](#6-methodological-details)
  - [6.1 Conversion and Dead Time Factor](#61-conversion-and-dead-time-factor)
  - [6.2 Energy Calibration](#62-energy-calibration)
  - [6.3 ROI Integration, Normalization and Point Uncertainty](#63-roi-integration-normalization-and-point-uncertainty)
  - [6.4 Peak Removal and Data Cleaning](#64-peak-removal-and-data-cleaning)
  - [6.5 Sigmoid Fitting and Parameter Extraction](#65-sigmoid-fitting-and-parameter-extraction)
  - [6.6 Construction of the Uncertainty Budget](#66-construction-of-the-uncertainty-budget)
  - [6.7 Statistical Comparison Using ANOVA](#67-statistical-comparison-using-anova)
- [7. Code Architecture](#7-code-architecture)
- [8. Limitations](#8-limitations)
- [9. References](#9-references)

---

## 1. Introduction

This document describes the scientific methods implemented in the RNRA data processing tool, from raw MPA files to excitation profiles, optional peak removal, sigmoid fitting, and statistical analysis of grouped results. 

The current implementation already:
- converts `.mpa` acquisitions into text spectra with dead-time information;
- performs a linear energy calibration based on Gaussian peak fits;
- builds excitation profiles by integrating counts inside a ROI and normalizing by collected charge;
- estimates an uncertainty on each normalized point;
- offers post‑processing functions for peak removal, sigmoid fitting, and ANOVA-based repeatability analysis;
- assembles relative contributions into a global uncertainty budget. 

The goal is not to provide a fully exhaustive metrological treatment, but a **consistent and implemented** uncertainty model aligned with the actual code.

---

## 2. Scientific Background

### 2.1 Resonant Nuclear Reaction Analysis (RNRA)

The RNRA part of the document can remain essentially as you wrote it, since it is conceptual and independent of the code. Only minor changes are needed to keep the wording compatible with the current implementation:

- keep the description of the reaction \(^{15}\mathrm{N}(^{1}\mathrm{H}, \alpha\gamma)^{12}\mathrm{C}\), the resonance at 6.385 MeV, the sigmoidal excitation curve, and the use of TiH\(_2\); 
- keep the equation \(N = Q_c \cdot \Omega \cdot \sigma(E_r) \cdot N_t\) as the physical basis for normalizing the counts by charge; 
- you may add that, in the current software, \(\Omega\) and \(\sigma\) enter only implicitly through the proportionality between counts and hydrogen content, while the code explicitly treats \(N\) and \(Q_c\). 

You do not need to change the physics narrative; the important point is that the **implemented normalization \(N/Q\)** matches the idea of normalizing by integrated charge as in the theoretical formula. 

### 2.2 Analysis of Variance (ANOVA)

The conceptual part on ANOVA (groups, \(H_0\), \(H_1\), F‑test, assumptions, possible Kruskal–Wallis alternative) can also be kept largely as written. The only place where the document must be precise is in the **implemented formula** for the uncertainty estimate. 

In the existing code, the ANOVA function:
- fits a one‑way model of the form \(\hat{y} = \sum \beta_i G_i + \varepsilon\);
- retrieves the ANOVA table;
- identifies the line corresponding to the group factor to compute \(MS_\text{inter}\);
- uses the residual mean square as \(MS_\text{intra}\);
- uses an effective number of observations per group defined as the mean group size,
i.e. $n_{eff}=mean(group sizes)$, when computing the inter-group uncertainty term.
- computes: 

\[
u_\text{inter} =
\begin{cases}
\sqrt{\dfrac{MS_\text{inter} - MS_\text{intra}}{n_\text{per group}}} & \text{if } MS_\text{inter} > MS_\text{intra} \\
0 & \text{otherwise}
\end{cases}
\]

\[
u_\text{intra} = \sqrt{MS_\text{intra}}
\]

\[
u_\text{total} = \sqrt{u_\text{intra}^2 + u_\text{inter}^2}
\]

\[
u_\text{rel} = \dfrac{u_\text{total}}{\bar{y}}, \quad u_\text{rel}(\%) = 100 \times u_\text{rel}
\]

This is the formula you can keep in the text, but you should **explicitly mention** that the current implementation fixes \(n_\text{per group} = 5\) and thus assumes five replicates per group. 

### 2.3 Uncertainty Budget – Concept

At a conceptual level, you can keep the structure “calibration → excitation profiles → sigmoid fit”, but the text must reflect that the code does **not** propagate a full analytical model through every parameter. Instead, it:

- computes a **relative RMS calibration error** and stores it as a calibration contribution; 
- computes **pointwise uncertainties** for each normalized excitation point and summarises them into a relative excitation-curve contribution; 
- computes a **relative uncertainty on sigmoid parameters** and summarises it into a sigmoid contribution; 
- combines these relative contributions in quadrature via `compute_uncertainty_budget`. 

You should therefore avoid any sentence suggesting that the code “propagates analytically all contributions at each stage of the full measurement model”. It is safer to say that:

> “The current version builds a global uncertainty budget from relative contributions provided by the calibration stage and by the sigmoid‑fit stage, and combines them in quadrature. The profile‑point uncertainties enter the budget through the sigmoid fitting, where they are used as sigma in the weighted fit and thus propagated to the fitted quantity."

---

## 3. Interface Description

For the windows, the main change is to avoid promising functions that are not clearly backed by the core modules.

### 3.1 Conversion Window

This section can remain as in your draft, with the clarification that:
- the conversion routine `convert_mpa_folder` parses each `.mpa` file, extracts `realtime` and `livetime` for each `[ADCx]` section, computes a dead-time factor `realtime / livetime`, and writes it into the header of each exported text file; 
- any file with missing or malformed `realtime` or `livetime` gets a default factor of 1.0. 

### 3.2 Calibration Window

You can keep the description of interactive peak selection and Gaussian fits, but the **implemented model** is:

\[
y(x) = A \exp\left( -\dfrac{(x - x_0)^2}{2\sigma^2} \right) + b + cx
\]

fitted on a local channel interval around each peak, with weights given by the covariance matrix of the fit, then a linear regression \(E = aC + b\) with weights \(1/\sigma_{x_0}^2\) on the centroids. 

The calibration step provides:
- \(a\), \(b\);
- their standard uncertainties;
- the covariance matrix;
- \(R^2\). 

If you mention “relative RMS error” for calibration, it must reference the logic in your `etallonnage.py`/GUI and the `rel_rms_pct` field used by `uncertainty.py`. 

### 3.3 Processing Window

This is the section where the old text was most out of sync. The actual implemented loop in `Boucle_sans_variation` does: 

- reads a scenario table (`data_entry`) with, for each sample:
  - sample name;
  - first and last file numbers;
  - data folder;
  - file number prefix;
  - ADC index;
  - path to an Excel folder with **voltage/energy tables**;
  - calibration error parameter `erreur_calib`;
- calls `extraire_donnée_excel` to read a set of Excel files from `tension_folder`, extract blocks with columns “Tension terminale (kV)” and “Energie (keV)”, and store them in a dictionary keyed by sample; 
- for each file index, constructs names such as `prefixNNN_ADCDATA0.txt` and `prefixNNN_ADCDATA3.txt` (ADC and charge), checks that both exist, and passes them to `coups_normal_pour_un_fichier` with ROI bounds `c_min`, `c_max` in **channels**; 
- retrieves the energy for each file index from the Excel-derived `E_list`, rather than from the linear calibration formula; 
- builds an output DataFrame with:
  - file number;
  - `N/C` (normalized counts);
  - associated uncertainty;
  - energy in keV;
- saves it to an Excel file in the output directory. 

The text should reflect that the present processing loop **combines**:
- ROI integration in channels;
- dead-time-corrected counts;
- charge normalization;
- externally provided energy points read from Excel. 

You should remove any reference suggesting that the energy of each point is currently computed from `E = aC + b` inside this loop — the code instead reads `E` directly from Excel. 

### 3.4 ANOVA Window

The window description can remain mostly as in your draft, but the method section should explicitly say:

- the current implementation assumes five observations per group when decomposing variance into inter- and intra-group contributions for uncertainty estimation; 
- the ANOVA result provides \(u_\text{total}\) and \(u_\text{rel}(\%)\) for the chosen value column. 

---

## 4. Processing Workflow

A methodologically accurate workflow aligned with the code is:

1. **Conversion**
   - use the conversion window to transform raw `.mpa` files into `.txt` spectra;
   - each text spectrum contains a dead-time factor in the header and channel/count pairs. 

2. **Calibration**
   - choose representative spectra in `.txt` format;
   - select peaks, fit Gaussians with local linear background, assign reference energies;
   - perform a weighted linear fit \(E = aC + b\) and store calibration quality indicators. 

3. **Excitation-profile construction**
   - prepare the processing configuration Excel file with sample names, file ranges, folders and calibration information, plus references to the Excel files containing energy/voltage series; 
   - choose ROI bounds in channel units;
   - run `Boucle_sans_variation` to integrate counts, apply dead-time correction, normalize by charge, and associate each point with the corresponding energy from the Excel table; 
   - export excitation profiles as Excel files. 

4. **Peak removal and sigmoid fitting (optional)**
   - use peak-removal functions to clean parasitic build-up peaks in the excitation profiles; 
   - fit sigmoid curves to the cleaned (or raw) profiles and export fit parameters and plots. 

5. **Uncertainty budget and ANOVA (optional)**
   - compute relative contributions from calibration, excitation profiles and sigmoid fits, then pass them to `compute_uncertainty_budget`; 
   - use ANOVA on grouped scalar results (e.g. fitted plateau differences) to estimate a repeatability-related uncertainty component. 

---

## 5. Output Files

The application can generate the following output files:

-  `.txt` spectra containing a header line of the form “Dead time factor = …” followed by two numeric columns;

- calibration result exports, if implemented in the GUI, including fitted peaks, calibration coefficients, and quality metrics;

- excitation-profile Excel files with the columns numero_fichier, N/C, incertitudes, and Energie(keV);

- cleaned profile files saved with the suffix `_cleaned.xlsx`, together with PNG plots showing the removed peak region;

- sigmoid-fit outputs, including `fit_results.xlsx`, per-profile Excel files in `fits_data/*.xlsx`, and PNG images showing experimental points and the fitted sigmoid curve;

- ANOVA diagnostic plots, such as histograms, boxplots, violin plots, and Q-Q plots, when enabled in the analysis workflow
---

## 6. Methodological Details

### 6.1 Conversion and Dead Time Factor

The conversion section in your document is already close, but should use the explicit code behavior: 

- for each `[ADCx]` section, `livetime` and `realtime` are read;
- the dead-time factor is computed as:

\[
F_\text{dead} = \frac{t_\text{real}}{t_\text{live}}
\]

- if `livetime` is missing or zero, a default factor of 1.0 is used;
- this factor is written as a header line in each exported `.txt` file. 

The text should say that at the stage of profile construction, the code does not re‑compute dead time but reuses this factor from the header to correct the ROI-integrated counts. 

### 6.2 Energy Calibration

Here, tu peux détailler exactement ce que fait `calibration.py`: 

1. Load `.txt` spectrum:
   - read header to get a dead-time factor if present;
   - read two columns: channel and counts. 

2. For each selected peak:
   - select channels in a window \([C_\text{approx} - \Delta, C_\text{approx} + \Delta]\);
   - fit the model

\[
y(x) = A \exp\left( -\frac{(x - x_0)^2}{2\sigma^2} \right) + b + cx
\]

   - extract centroid \(x_0\) and its standard error \(\sigma_{x_0}\). 

3. Perform a weighted linear regression:

\[
E = a C + b
\]

with weights \(w_i = 1/\sigma_{x_{0,i}}^2\), giving \(a\), \(b\), their standard uncertainties, covariance matrix, and \(R^2\). 

If you mention “relative RMS error”, it must correspond to the residual RMS computed in your calibration quality script and stored as `rel_rms_pct`  in the application state before being used by `uncertainty.py`. 

### 6.3 ROI Integration, Normalization and Point Uncertainty

- The key difference with ta version initiale est que:

- The ROI is defined in channels (c_min, c_max).

- Integration is performed on the gamma ADC spectrum, with linear interpolation if the ROI bounds are not integers.

- Charge is read from the ADCDATA3 channel and converted to microcoulombs using a factor of $10^{-4}$



For each file, the implemented processing steps are:

1. Read the dead-time factor from the header of the ADC spectrum file.

2. Integrate counts within the channel ROI, with linear interpolation at the boundaries when required.

3. Sum the charge counts on the charge file and multiply by $10^{-4}$to obtain the integrated charge Q.
4. Apply the dead-time correction:
\[
N = N_\text{ROI} \cdot F_\text{dead}
\]

5. Compute normalized quantity:

\[
\frac{N}{Q}
\]

6. Compute uncertainties as implemented: 

- Poisson statistical term on \(N\):

\[
\sigma_\text{stat}(N) = \sqrt{N}
\]

- calibration/ROI term controlled by `err_et` (relative percentage):

\[
\sigma_\text{cal}(N) = \frac{\text{err\_et}}{100} \cdot N
\]

- total uncertainty on \(N\):

\[
\sigma_N = \sqrt{\sigma_\text{stat}(N)^2 + \sigma_\text{cal}(N)^2}
\]

- uncertainty on \(Q\) (based on \(\sqrt{Q}\) and the same scaling factor as the charge):

\[
\sigma_Q = \sqrt{Q} \times 10^{-4}
\]

- propagated uncertainty on \(R = N/Q\):

\[
u(R) = R \sqrt{\left(\frac{\sigma_N}{N}\right)^2 + \left(\frac{\sigma_Q}{Q}\right)^2}
\]

if \(N > 0\) and \(Q > 0\); otherwise the code returns NaN. 


### 6.4 Peak Removal and Data Cleaning

`Transform_functions.py` implements the removal of the local “carbon build-up” peak and generates the corresponding plots. 

For each Excel file containing an excitation curve, the routine:
  - sorts the data points by increasing energy;
  - selects a window \([E_\text{center} - \text{window}, E_\text{center} + \text{window}]\);
  - detects peaks in the`N/C` data within this window using `find_peaks`;
  - selects the peak closest to \(E_\text{center}\);
  - removes the points in the interval\([E_\text{pic} - \text{halfwidth}, E_\text{pic} + \text{halfwidth}]\);
  - saves the cleaned file and a plot comparing the raw and filtered data.


### 6.5 Sigmoid Fitting and Parameter Extraction

`fit_to_profile` in `Transform_functions.py` processes cleaned or uncleaned excitation-profile Excel files. It reads the columns “Energie(keV)”, “N/C”, “incertitudes”,  removes invalid values, and then performs the following steps.

- build a mask to keep only valid points;
- sort the data by increasing energy if needed;
- define an initial parameter set \(p_0 = [L, x_0, k, b]\);
- call  `curve_fit` with:
  - the sigmoid model \(y(x) = L / (1 + \exp(-k(x - x_0))) + b\);
  - `sigma=y_error`;
  - `absolute_sigma=True`;
  - the `dogbox`method;
  - appropriate parameter bounds; 
- obtain the fitted parameters and the covariance matrix;
- compute the effective plateau height `diif_height = L - b`;
- compute \(R^2\);
- compute the quantity `Ucc_tot = sqrt(perr[0] + perr[3])` as a global uncertainty indicator associated with the parameters 
 \(L\) and \(b\); 
- build a results table containing:
  - file name;
  - \(L\), \(b\), \(x_0\), \(k\);
  - `diff_height` (plateau height);
  - `sigma_tot` (`Ucc_tot`);
  - a `group` fild deriverd from `assign_group`, later used for ANOVA;
- ssave per-profile data-and-fit curves into Excel files and PNG images.



### 6.6 Construction of the Uncertainty Budget

The `core/uncertainty.py` module does not re‑implement a full analytical
propagation through every parameter of the measurement model. Instead, it
assembles **relative standard uncertainties** that have already been computed
upstream and combines them in quadrature. [file:153]

In the current implementation, two main contributions are used:

- a calibration contribution, based on a **relative RMS calibration error**
  (`rel_rms_pct`) computed from the residuals of the linear fit \(E = aC + b\); [file:153]
- a sigmoid‑fit contribution, based on the **relative uncertainty of the
  fitted plateau quantity**, obtained from the covariance matrix of the sigmoid
  fit. [file:149][file:151]

For calibration, `calibration_result` may contain:

- either a single field `rel_rms_pct` for a global calibration;
- or a dictionary of groups, each with its own `rel_rms_pct`. [file:153]

For each available `rel_rms_pct`, the code converts it into a relative
standard uncertainty

\[
u_\text{rel, calib} = \frac{\text{rel\_rms\_pct}}{100}
\]

and adds a row to the budget with sensitivity coefficient equal to 1.0 and
contribution \(|u_\text{rel, calib}|\). [file:153]

For the sigmoid‑fit contribution, the upstream fitting function
`fit_to_profile` produces, for each profile, a **plateau height**
`diff_height = L - b` and a scalar uncertainty `sigma_tot` derived from the
covariance of the parameters \(L\) and \(b\). [file:149] At the GUI level,
`update_sigmoid_uncertainty_in_appstate` computes an average relative
uncertainty

\[
u_\text{rel, sig} = \left\langle \frac{\sigma_\text{tot}}{\text{diff\_height}} \right\rangle
\]

and stores it as a percentage `value_pct`. [file:151] The uncertainty module
then converts

\[
u_\text{rel, sig} = \frac{\text{value\_pct}}{100}
\]

and adds a corresponding row “Fit sigmoïde (…)” with contribution
\(|u_\text{rel, sig}|\). [file:151][file:153]

The combined standard uncertainty is finally computed as

\[
u_c = \sqrt{\sum_i \text{contribution}_i^2}
\]

where the sum runs over all active contributions (calibration and sigmoid
fit). [file:153] In other words, the current implementation **assumes the
listed relative contributions are independent standard uncertainties** and
computes their combined effect as the square root of the sum of squares.

Pointwise uncertainties on the excitation profiles are not added as a
separate term in the final budget. Instead, they enter the uncertainty budget
through the sigmoid fitting step: the profile‑point uncertainties are passed
to `curve_fit` via the `sigma` argument (with `absolute_sigma=True`), and the
resulting covariance matrix of the fitted parameters is used to construct the
sigmoid‑fit contribution. [file:149][file:151]


### 6.7 Statistical Comparison Using ANOVA

The ANOVA module is used to assess whether several groups of scalar results (for example, plateau values from different conditions) can be considered statistically consistent within the experimental repeatability of the measurement chain. 
The implemented procedure is a **one‑way ANOVA**:

- A one‑factor model is fitted to the data in the form \(\hat{y} = \sum \beta_i G_i + \varepsilon\), where \(G_i\) are group indicators and \(\varepsilon\) is the residual term. 
- The ANOVA table is computed, and the mean squares associated with the group factor and the residuals are identified as \(MS_\text{inter}\) and \(MS_\text{intra}\), respectively. 
- An effective number of observations per group is assumed through a fixed parameter \(n_\text{per group} = 5\), consistent with the structure of the datasets used during development. 

From these quantities, the code derives two components of uncertainty:

\[
u_\text{inter} =
\begin{cases}
\sqrt{\dfrac{MS_\text{inter} - MS_\text{intra}}{n_\text{per group}}} & \text{if } MS_\text{inter} > MS_\text{intra} \\
0 & \text{otherwise}
\end{cases}
\]

\[
u_\text{intra} = \sqrt{MS_\text{intra}}
\]

\[
u_\text{total} = \sqrt{u_\text{intra}^2 + u_\text{inter}^2}
\]

\[
u_\text{rel} = \dfrac{u_\text{total}}{\bar{y}}, \quad u_\text{rel}(\%) = 100 \times u_\text{rel}
\]

where \(\bar{y}\) is the overall mean of the considered quantity. 

The module also provides diagnostic plots such as histograms, boxplots, violin plots and Q‑Q plots, which help to visually assess normality, homoscedasticity and the presence of outliers in the residuals. Any non‑normal behavior or strong heteroscedasticity should be taken into account when interpreting the ANOVA‑based uncertainty estimate and may justify the use of non‑parametric methods outside the current implementation. 

---

## 7. Code Architecture

The RNRA processing tool is structured as a set of core modules that implement the main scientific operations, plus a graphical interface that orchestrates them and stores intermediate results in a shared application state. 

- **`core/file_io.py`** handles conversion from raw `.mpa` files to `.txt` spectra. It parses the ADC sections, extracts `livetime` and `realtime`, computes a dead‑time factor, and writes a header line followed by channel/count pairs. 
- **`core/calibration.py`** implements energy‑calibration routines. It reads `.txt` spectra, fits Gaussian peaks with a local linear background, and performs a weighted linear regression \(E = aC + b\), returning calibration coefficients, standard uncertainties, covariance, and quality indicators such as \(R^2\) and a relative RMS error used later in the uncertainty budget. )
- **`core/Loop_fonction.py`** controls the excitation‑profile processing loop. It reads configuration information from Excel, associates each file index with an energy value from external voltage/energy tables, calls ROI‑integration and normalization functions, and exports excitation profiles to Excel files. 
- **`core/Traitement_fonctions.py`** carries out ROI integration on gamma spectra, applies dead‑time correction and charge normalization, and propagates uncertainties from counts, calibration/ROI parameters and charge to obtain pointwise uncertainties on \(N/Q\). 
- **`core/Transform_functions.py`** provides higher‑level transformations, including removal of local build‑up peaks in excitation profiles and sigmoid fitting of processed profiles. It generates cleaned profile files, per‑profile fit data, and plots. It also computes sigmoid‑fit parameters and associated uncertainties (`diff_height`, `sigma_tot`) that feed the uncertainty budget and the ANOVA module. 
- **`core/uncertainty.py`** builds a compact uncertainty budget from relative contributions provided by the calibration and sigmoid‑fit stages. It converts these contributions into relative standard uncertainties and combines them in quadrature to obtain a global combined uncertainty. )
- **`core/ANOVA.py`** performs one‑way ANOVA on grouped results, extracts inter‑ and intra‑group variance components, constructs a total and relative uncertainty, and produces diagnostic plots for checking ANOVA assumptions. 

The graphical interface (Tkinter tabs) connects these modules, manages file selection and configuration, and stores numerical summaries (e.g. calibration RMS, sigmoid‑fit relative uncertainty) in `app_state`, from which the uncertainty budget window retrieves its inputs. 

---

## 8. Limitations

The current implementation should be regarded as a first functional version of the RNRA processing workflow rather than a complete, fully generic metrological framework. Several limitations follow directly from the present code design. 

- **Calibration model.** The energy calibration assumes a strictly linear relation \(E = aC + b\) and well‑resolved Gaussian‑like peaks with a local linear background. Non‑linearities, severe peak overlap, or systematic distortions are not explicitly modeled. 
- **Dead‑time correction.** The dead‑time factor is computed from `livetime` and `realtime` metadata in the `.mpa` files and applied uniformly to ROI‑integrated counts. Any time dependence of the dead time within an acquisition is not explicitly treated. 
- **Profile and fit uncertainties.** The uncertainties on excitation profiles and on sigmoid‑fit parameters are constructed from a combination of Poisson statistics, user‑specified calibration/ROI errors and propagated charge uncertainty. Possible additional sources of bias, such as beam‑current drift, detector gain instabilities or sample inhomogeneity, are not explicitly included. 
- **Independence assumption in the budget.** The global uncertainty budget combines the calibration and sigmoid‑fit contributions as independent standard uncertainties, using the square root of the sum of squares. Correlations between contributions are not modeled, so the combined uncertainty should be interpreted with this simplification in mind. )
- **Fixed group size in ANOVA.** The ANOVA‑based uncertainty decomposition uses a hard‑coded value \(n_\text{per group} = 5\) when deriving the inter‑group component. The method is therefore tailored to datasets with five replicates per group and may not be directly applicable to arbitrary group sizes without code modification. 
- **Input format constraints.** The Excel input files used for configuration, energy/voltage tables and processing must conform closely to the expected column names and structure. Deviations from these formats can lead to runtime errors or incorrect data interpretation. 

These limitations should be explicitly acknowledged when presenting the tool and when interpreting its outputs in a scientific or metrological context.

## 9. References

