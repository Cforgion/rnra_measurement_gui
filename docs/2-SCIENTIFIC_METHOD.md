# USER GUIDE - RNRA Data Processing and Error Management

## Table of Contents

- [1. Introduction](#1-introduction)
- [2. Scientific Background](#2-scientific-background)
  - [2.1 Resonant Nuclear Reaction Analysis (RNRA)](#21-resonant-nuclear-reaction-analysis-rnra)
  - [2.2 Analysis of Variance (ANOVA)](#22-analysis-of-variance-anova)
  - [2.3 Uncertainty Budget](#23-uncertainty-budget)
- [3. Interface Description](#3-interface-description)
  - [3.1 Conversion Window](#31-conversion-window)
  - [3.2 Calibration Window](#32-calibration-window)
  - [3.3 Processing Window](#33-processing-window)
- [4. Processing Workflow](#4-processing-workflow)
- [5. Output Files](#5-output-files)
- [6. Methodological Details](#6-methodological-details)
  - [6.1 Conversion and Dead Time Correction](#61-conversion-and-dead-time-correction)
  - [6.2 Energy Calibration](#62-energy-calibration)
  - [6.3 ROI Integration and Normalization](#63-roi-integration-and-normalization)
  - [6.4 Peak Removal and Data Cleaning](#64-peak-removal-and-data-cleaning)
  - [6.5 Sigmoid Fitting and Parameter Extraction](#65-sigmoid-fitting-and-parameter-extraction)
  - [6.6 Uncertainty Estimation at Each Step](#66-uncertainty-estimation-at-each-step)
  - [6.7 Statistical Comparison Using ANOVA](#67-statistical-comparison-using-anova)
- [7. Code Architecture](#7-code-architecture)
- [8. Limitations](#8-limitations)
- [9. References](#9-references)

---

## 1. Introduction

This tool performs the analysis of hydrogen profiling measurements from the raw MPA file to the excitation curve and final sigmoid fit. In addition to the statistical evaluation of repeatability through ANOVA, the workflow includes the propagation of measurement uncertainty at each processing stage, so that the final result reflects not only random variability but also contributions arising from calibration, dead-time correction, and nonlinear sigmoid fitting.

The uncertainty evaluation is not limited to ANOVA. ANOVA is used to estimate the random component associated with repeated measurements, whereas the full uncertainty budget is obtained by propagating all relevant contributions through the measurement model, including calibration uncertainty, dead-time correction uncertainty, and fit-parameter uncertainty from the sigmoid adjustment.

---

## 2. Scientific Background

### 2.1 Resonant Nuclear Reaction Analysis (RNRA)

Resonant Nuclear Reaction Analysis (RNRA) is an analytical technique used to determine the concentration profile of an element within a material as a function of depth. Its principle is based on a nuclear reaction exhibiting a resonance at a well-defined energy: when the energy of the incident ions matches the resonance energy, the reaction cross-section reaches a maximum. This enables selective probing of a specific depth, by exploiting the relationship between the incident beam energy and the energy loss of ions in matter. The resonance width, which defines the energy range around the resonance where the reaction remains significant, directly determines the depth resolution: the narrower the resonance, the higher the spatial resolution.

In our case, the goal is hydrogen profiling. For this purpose, a TiH₂ pellet is used due to its high hydrogen content, homogeneity, and stability under irradiation. Measurements rely on the interaction between ¹⁵N³⁺ ions and ¹H nuclei via the following nuclear reaction:

**¹⁵N(¹H, αγ)¹²C**

This reaction exhibits a strong resonance at 6.385 MeV (width 1.8 keV, σ_max = 1650 mb, see Fig. 1). At this energy, the interaction probability is maximal, providing excellent selectivity. The reaction proceeds in two steps:

1. Hydrogen interacts with nitrogen-15 to form an excited, short-lived oxygen-16 compound nucleus.
2. This nucleus decays by emitting an alpha particle and an excited carbon-12 nucleus, which subsequently returns to its ground state by emitting a 4.43 MeV gamma ray, which is detected to quantify the reaction.

As ¹⁵N³⁺ ions penetrate matter, they progressively lose energy according to the stopping power S = dE/dx, which depends on both the material and the ion species. By varying the incident beam energy, each energy value can be associated with a specific depth in the sample, allowing depth scanning (see Fig. 2). For incident energies slightly below resonance, few gamma rays are detected. As the energy approaches resonance, the gamma yield increases rapidly until reaching a plateau where the signal stabilizes. The resulting curve has a sigmoidal shape (see Fig. 4b), characteristic of energy-dependent depth probing.

However, this excitation curve does not directly represent the concentration profile. A deconvolution step is required to correct for beam energy loss effects within the sample. This procedure converts the gamma signal variation into an accurate hydrogen depth distribution profile. From the deconvoluted excitation curves, a quantitative hydrogen concentration profile can be extracted (see Louis Dupont's thesis for a detailed description).

The number of detected events is given by [11,12]:

**N = Q_c · Ω · σ(E_r) · N_t**

where:

- **Q_c**: integrated charge, i.e. the total charge delivered by ions impacting the target. It is obtained by integrating the beam current over irradiation time and is expressed in microcoulombs (µC). Dividing by the ion charge gives the total number of particles incident on the sample; it is a key normalization factor for the detected signal.
- **Ω**: detector solid angle (sr).
- **σ(E_r)**: reaction cross-section at resonance energy (cm²).
- **N_t**: areal target atom density (at/cm²).

RNRA is particularly well suited for light element analysis such as hydrogen. Its main advantages are:

- **Excellent sensitivity** (down to ~10 ppm atomic), enabled by the resonance and its narrow width.
- **High depth resolution**, directly related to the narrow resonance width.
- **High selectivity**, since the 4.43 MeV gamma line is weakly affected by background (natural radioactivity is typically below ~3 MeV).
- **Non-destructive nature**, provided beam-induced hydrogen diffusion remains limited.

However, the method requires:

- a particle accelerator;
- consideration of matrix effects, i.e. all phenomena related to sample composition and structure that may affect measurement accuracy.

---

### 2.2 Analysis of Variance (ANOVA)

To quantify measurement reproducibility and estimate random uncertainty, an ANOVA (ANalysis Of VAriance) test is applied. This statistical test compares the means of multiple groups — in this case, measurements acquired on different days — to determine whether statistically significant differences exist. The dataset consists of five measurements per day over eight acquisition days.

ANOVA is based on the following hypotheses [14]:

- **H₀ (null hypothesis)**: all group means are equal, i.e. no significant difference exists between days.
- **H₁ (alternative hypothesis)**: at least one group mean differs.

The decision to reject or not reject H₀ is based on the **p-value**. This quantity represents the probability of incorrectly rejecting the null hypothesis when it is true (Type I error). For example, a p-value of 0.23 means that rejecting H₀ carries a 23% risk of incorrectly concluding that differences exist between groups.

ANOVA can also be interpreted as a linear regression model with categorical variables:

**ŷ = Σ βᵢ Gᵢ + ε**

where:

- **ŷ** is the model prediction,
- **Gᵢ** indicates membership of observation to group *i*,
- **βᵢ** is the mean of group *i*,
- **ε** is the residual error term.

Residuals are defined as:

**res = y_obs − ŷ**

Before applying ANOVA, three assumptions must be verified:

- **Independence of measurements**, ensured by experimental design.
- **Normality of residuals**, checked using Q-Q plots¹ (see Fig. 6), histograms, or formal tests such as Shapiro–Wilk [16].
- **Homogeneity of variances**, assessed using violin plots (see Fig. 7) or statistical tests such as Levene's test [17].

If any assumption is violated, classical ANOVA cannot be applied, as it relies on the assumption that the test statistic follows a Fisher–Snedecor distribution [18].

When assumptions are satisfied, the F-statistic follows a Fisher–Snedecor distribution with k−1 and k(n−1) degrees of freedom, where k is the number of groups and n the number of measurements per group (see Fig. 8). This distribution compares inter-group variance to intra-group variance: larger F values indicate stronger evidence of differences between groups. If F exceeds the critical value F_critical, determined by the significance level α, the null hypothesis is rejected.

If normality or homogeneity assumptions are not satisfied, a non-parametric alternative such as the **Kruskal–Wallis test** [19] must be used. This test is based on rank ordering rather than raw values and does not assume a Fisher distribution. It also provides a p-value interpreted in the same way.

ANOVA also allows estimation of **random uncertainty**, an approach previously applied in ion beam measurements [20,21]. Systematic errors are not included in this model. Within-group and between-group variances are used to compute the **Mean Squares (MS)**:

**MS_inter = SS_inter / (k − 1)**

**MS_intra = SS_intra / (k(n − 1))**

From these quantities, two uncertainty contributions are derived:

- **Between-group uncertainty (u_inter):**

  u_inter = √((MS_inter − MS_intra) / n)

  If MS_inter < MS_intra, inter-group variance is negligible compared to intra-group variance, confirming H₀.

- **Within-group uncertainty (u_intra):**

  u_intra = √MS_intra

The **combined uncertainty** is:

**u_c = √(u_inter² + u_intra²)**

The **relative uncertainty** is:

**u_rel = (u_c / ȳ) × 100**

where ȳ is the overall mean.

---

¹ A quantile is a value dividing a dataset into intervals containing equal numbers of observations. Common examples include quartiles and the median.

---

### 2.3 Uncertainty Budget

The RNRA data processing chain involves three successive stages, each of which introduces uncertainty contributions that are propagated and combined into a global uncertainty budget. The three stages are: energy calibration, excitation profile construction, and sigmoid fitting.

#### 2.3.1 Energy Calibration

The energy calibration establishes the linear relationship E = a·C + b between the ADC channel C and the energy E. The user selects several reference peaks whose centroids are fitted by a Gaussian model, providing for each peak:

- the centroid position in channels,
- its standard uncertainty,
- the corresponding reference energy.

A weighted linear regression then yields the calibration coefficients a and b, their standard uncertainties u(a) and u(b), and the associated covariance. The application also computes a **relative RMS error** over all calibration points, reflecting the scatter of residuals in energy space and serving as a global quality indicator for the calibration.

For the uncertainty budget, three contributions are distinguished:

- the global calibration uncertainty (relative RMS error),
- the contributions associated with the uncertainties on slope a and intercept b,
- the contributions from the individual centroid uncertainties of each peak, propagated into energy via E = a·C + b.

These contributions are expressed as relative uncertainties and combined in quadrature to obtain a single calibration-related uncertainty term.

#### 2.3.2 Excitation Profiles

Excitation profiles are constructed by integrating, for each beam energy, the number of counts within the selected ROI and normalizing by the integrated charge. For each point on the profile, the application computes an uncertainty on NC = N/Q that accounts for:

- counting statistics,
- charge normalization uncertainty,
- the effect of ROI boundary placement and calibration uncertainty.

From these point-by-point uncertainties, a **mean relative dispersion** ⟨u(NC)/NC⟩ is computed over the excitation profile. This quantity is stored as the excitation-profile contribution to the global budget, expressed as a relative uncertainty in percent.

#### 2.3.3 Sigmoid Fitting

The normalized excitation profiles are fitted with a sigmoid function to extract physical parameters such as the plateau difference, midpoint energy, and steepness. From the point uncertainties and the covariance matrix of the fit, the application estimates the uncertainty on the parameters of interest, in particular on the plateau difference ΔH.

For the uncertainty budget, this stage is summarized by a **mean relative uncertainty** on the sigmoid height, constructed from the ratio of the uncertainty on the height parameter (or a combination of fit parameters) to its fitted value. This sigmoid-fit contribution is expressed in percent and integrated into the global budget.

#### 2.3.4 Global Budget

The full uncertainty budget therefore combines the following independent relative contributions:

- calibration uncertainty (relative RMS error, plus terms from u(a), u(b), and centroid uncertainties),
- mean relative uncertainty from the excitation profiles,
- mean relative uncertainty from the sigmoid fit.

These contributions are treated as independent relative standard uncertainties (Type A and Type B already expressed numerically) and combined in quadrature to yield the overall combined uncertainty on the output quantity. The application presents this budget as a table listing, for each source, its value, standard uncertainty, sensitivity coefficient, and contribution to the total, alongside the resulting combined uncertainty.

> **Note on ANOVA:** The repeatability-related uncertainty estimated from ANOVA (see Section 2.2 and Section 6.7) represents an additional contribution that can be incorporated into the budget when repeated measurements under reproducibility conditions are available. It is treated as an independent term and combined in quadrature with the contributions above.

---

## 3. Interface Description

### 3.1 Conversion Window

This window performs the batch conversion of raw `.mpa` acquisition files into structured `.txt` spectra that can be used in the calibration and processing steps.
The conversion routine reads the acquisition metadata, computes the dead time correction factor, and exports one text file per ADC channel with a standardized format.

#### Layout and controls

The **Conversion** tab contains the following elements:

- **Configuration file (Excel)**
  - Read-only text field displaying the path to the global configuration Excel file.
  - **Browse** button to select the configuration file (e.g. `input_mpa.xlsx`).

- **Day root (sample name root)**
  - Text entry (labelled in the interface as *day racine samplename*) where the user enters the day or sample root, such as `250317`.
  - This value is used to filter the rows corresponding to a given measurement day in the configuration file.

- **Output folder for .txt files**
  - Text entry (labelled in the interface as *Folder exit for .txt*) displaying the path where converted `.txt` files will be written.
  - **Browse** button to choose or create this directory.

- **Conversion controls**
  - **Convert .mpa → .txt** button to start the conversion for the selected day.
  - Progress bar indicating the current file index and total number of files being processed.
  - Status label showing messages such as "Waiting", "Conversion in progress…", "Finished", or "Finished with errors".

- **Log window**
  - Multi-line text area showing detailed messages, including which folders are used, which files are converted, and any encountered errors.

#### User actions

1. **Load the configuration file**
   - Click **Browse** in the "config Excel" section.
   - Select the Excel configuration file used to describe your measurements (sample names, folders, first/last file numbers, etc.).
   - The selected path appears in the read-only entry.

2. **Define the day root**
   - In the **day root** entry, type the day/sample root corresponding to the measurement series you want to convert (for example `250317`).
   - Internally, the software looks for rows in the configuration file whose sample name starts with this root and retrieves the corresponding `mpafolder` path.

3. **Choose the output folder for `.txt` files**
   - Click **Browse** and select a base directory in which the converted files will be stored.
   - The program will create (if necessary) a subfolder named after the day root (e.g. `.../250317/`) and place all `.txt` outputs there.

4. **Launch the conversion**
   - Click **Convert .mpa → .txt**.
   - The software scans the `mpafolder` corresponding to the selected day in the configuration file, then converts all `.mpa` files found in this folder.
   - Progress is displayed in the progress bar and status label; detailed messages appear in the log.

5. **Check for errors**
   - At the end of the process, if errors occurred (missing folder, unreadable `.mpa` file, etc.), they are listed in the log area.
   - The status label indicates whether the conversion finished successfully or with errors.

#### Output text file structure

For each `.mpa` file and for each ADC channel, one `.txt` file is generated.

- **File naming**: `filename_ADCname.txt`

  Example: input file `sample01.mpa` with two ADC channels produces `sample01_ADC1.txt` and `sample01_ADC2.txt`.

- **File content**:
  1. **Header line**: dead time factor extracted from the `.mpa` metadata (e.g. `Dead time factor = 1.023`).
  2. **Data lines**: two columns — `Channel` (integer ADC channel index) and `Count` (measured counts).

All exported text files are formatted to be directly readable in Python (via `numpy.loadtxt`, `pandas.read_csv`) or in other scientific data processing tools.

---

### 3.2 Calibration Window

The **Calibration** tab is used to build an energy calibration curve E = a·C + b from one or several spectra in `.txt` format generated by the conversion step.
The user interactively selects peaks on a displayed spectrum, fits a Gaussian shape to each peak to extract the centroid channel, associates each centroid with a known reference energy, then performs a weighted linear regression.

#### Layout and controls

The **Calibration** window is organised into three areas:

- **Left panel – File and peak management**

  - **Load spectrum** button to select a `.txt` spectrum file produced by the Conversion window. After loading, the filename and dead time factor are displayed.
  - **Peak selection area** with instruction label and display of the currently selected interval in channels.
  - **Energy (keV)** entry field for the reference energy corresponding to the selected peak.
  - **Fit Gaussian** button to launch the peak fit for the current selection.
  - **Reset selection** button to clear the current selection.
  - **Peak list (Treeview)** with columns: Index, Channel (fitted centroid), Energy (keV) (reference value entered by the user).
  - **Delete selected peak** and **Clear all peaks** buttons.
  - **Run calibration** button (enabled when at least two peaks are defined).
  - Calibration result label.

- **Center panel – Spectrum and fits**

  - Matplotlib figure displaying the loaded spectrum (counts vs. channel).
  - Zoom/pan tools (Matplotlib toolbar).
  - An interactive **SpanSelector** allowing the user to select a channel interval by clicking and dragging.
  - After fitting, vertical lines and Gaussian curves are drawn to show the fitted peaks.

- **Right panel – Detailed results and export**

  - Text area listing general spectrum information, peak fit details (centroid, error, sigma, amplitude), and calibration results (slope, intercept, R², relative RMS).
  - **Export results** button to save the list of peaks and the calibration summary in a text file.

#### User actions

1. **Load a spectrum**
   - Click **Load spectrum** and select a `.txt` file produced by the Conversion window.
   - The program reads the header and data, displays the spectrum, and shows the dead time factor if available.

2. **Select a peak**
   - Option A: click and drag on the spectrum (SpanSelector) to select a peak region; the selected center and half-width are computed automatically.
   - Option B: simply click on the spectrum to set an approximate center; an internal rule computes a suitable half-width.
   - The current selection is displayed as `center = ..., width = ...`.

3. **Associate a reference energy**
   - In the **Energy (keV)** entry, type the known energy of the selected peak (e.g. a resonance or gamma line).

4. **Fit a Gaussian peak**
   - Click **Fit Gaussian**.
   - The program performs a Gaussian fit and returns the centroid, sigma, amplitude, and centroid uncertainty.
   - The peak is added to the Treeview and details are appended to the text area.

5. **Repeat for all calibration peaks**
   - Repeat steps 2–4 for each reference line to include in the calibration.
   - Once at least two peaks are defined, the **Run calibration** button is enabled.

6. **Run the linear calibration**
   - Click **Run calibration**.
   - The software performs a weighted linear regression E = a·C + b using the centroids and their uncertainties.
   - Results: slope a, intercept b, their uncertainties, R², and relative RMS (%).

7. **Update the configuration file (optional)**
   - If a global configuration Excel file is defined, calibration results can be written back for the current group/day so the processing loop can use them automatically.

8. **Export calibration results (optional)**
   - Click **Export results** to save the peak list and calibration summary to a standalone text file.

#### Output and stored parameters

The main numerical result is a linear calibration E = a·C + b with associated uncertainties and quality indicators. These parameters are either stored in memory for immediate use or written into the configuration Excel file to be reused by the processing loop.

---

### 3.3 Processing Window

The **Processing** window controls the full data-processing pipeline, from ROI integration to optional peak removal and final sigmoid fitting of the excitation profiles.
It uses the configuration Excel file and the calibration parameters to convert profiles from channel space to energy space and to generate processed outputs for further analysis.

#### Layout and controls

- **Configuration and ROI (left panel)**

  - **Configuration file** section with read-only path display and **Load Excel configuration file** button.
  - **ROI selection** entry showing the ROI in energy (e.g. Emin–Emax keV), with a **Choose ROI on a spectrum** button for interactive selection on a reference spectrum.
  - **Save results** checkbox and output folder entry with **Browse** button (enabled only when saving is active).
  - **Process files** button to start the loop over all scenarios in the configuration file.

- **Carbon build-up peak removal**

  - **Energy center (keV)**: resonance energy of the build-up peak to remove (default ~6385 keV for the ¹⁵N(H, α, γ)¹²C resonance).
  - **Search window (keV)**: total energy window around the center where the peak search is performed.
  - **Removal half-width (keV)**: half-width of the interval to be removed once a peak is detected.
  - **Remove build-up peak** button to apply the removal to all profiles previously calculated by the loop.

- **Sigmoid fitting**

  - **Run sigmoid fit on output profiles** button. Uses either the raw loop output or the `filtered/` folder (after peak removal) as input.

- **Visualization options**

  - **Display output profile** button to open a `.xlsx` or `.png` file, displayed in the Matplotlib figure on the right.

- **Right panel – Plot and detailed log**

  - Matplotlib figure with axes labelled "Energy (keV)" and "NC".
  - Zoom/pan toolbar.
  - Text area showing detailed log messages (loop progress, errors, fit results, etc.).

#### User actions

##### A. Loop over ROI

1. **Load the configuration file**
   - Click **Load Excel configuration file** and select the configuration Excel file.
   - The program checks that all required columns are present (sample name, folders, first/last file numbers, ADC, slope, intercept, calibration error, etc.).

2. **Define the ROI in energy**
   - Option A – Manual: type the ROI in keV in the entry field (e.g. `6400–6600 keV`).
   - Option B – Interactive: click **Choose ROI on a spectrum** to open a dedicated window where you can click-and-drag to select the energy interval on a reference spectrum.

3. **Choose whether to save results**
   - Check **Save results** and choose an output folder to keep all intermediate and final results.
   - If unchecked, the program uses an internal temporary directory for the session.

4. **Run the processing loop**
   - Click **Process files**.
   - For each scenario (row) in the configuration file, the program reads the relevant `.txt` spectra, integrates counts within the selected ROI, normalizes by integrated charge, and builds an excitation profile as a function of beam energy.
   - Results are written to the output folder and messages appear in the log.

##### B. Peak removal (optional)

1. **Set the build-up energy and windows**
   - In **Energy center (keV)**, keep the default resonance energy (e.g. 6385 keV) or replace it with the value relevant for your experiment.
   - Adjust the **search window** and **removal half-width** if needed.

2. **Apply the removal to all profiles**
   - Ensure the loop has been run at least once so that raw profiles exist.
   - Click **Remove build-up peak**.
   - The program identifies and removes peak points in the specified interval for all output profiles.
   - Filtered profiles are saved in a `filtered/` subfolder along with optional diagnostic plots.

##### C. Sigmoid fit

1. **Select the input folder for fitting**
   - If peak removal was performed, the fitting step uses the `filtered/` folder; otherwise it uses the raw loop output.

2. **Run the sigmoid fits**
   - Click **Run sigmoid fit on output profiles**.
   - For each excitation profile, the program fits a sigmoid curve and extracts plateau values, midpoint energy, width, and plateau difference.
   - Fit results and figures are saved to the output directory.

##### D. Visualization

1. **Open a processed profile or image**
   - Click **Display output profile** and select an `.xlsx` or image file.

2. **Inspect the result**
   - Excel files are plotted with optional error bars and fitted curves.
   - Image files are displayed directly in the plotting area (axes hidden for a clean display).

#### Output file naming and content

The processing step produces:

- **Loop output files**: one file per scenario containing energy, normalized counts, and optional uncertainties.
- **Filtered profiles** (after peak removal): saved in a `filtered/` subfolder with the same naming scheme.
- **Sigmoid fit outputs**: numerical summaries of fit parameters and plots (`.png`) showing data and fitted curves.

These outputs are used for further analysis, comparison between samples, and statistical processing (including ANOVA) as described in later sections of this guide.

---

## 4. Processing Workflow

This section summarises the recommended end-to-end workflow using the three main windows.

1. **Configure and convert**
   - Prepare or update the Excel configuration file describing all measurements (paths, file numbers, ADC, calibration parameters).
   - Use the **Conversion** window to convert all `.mpa` files for a given day/root into `.txt` spectra.

2. **Calibrate energy**
   - In the **Calibration** window, load representative spectra and identify several reference peaks.
   - Fit Gaussian peaks, assign reference energies, and run the linear calibration to obtain E = a·C + b.
   - Store the calibration coefficients in the configuration file.

3. **Process profiles**
   - In the **Processing** window, load the configuration file.
   - Define the ROI in energy and run the loop to build excitation profiles for all scenarios.
   - Optionally, remove the carbon build-up peak and re-use the cleaned profiles.

4. **Fit and analyse**
   - Perform sigmoid fits on the final excitation profiles to extract plateau differences and key parameters.
   - Use the exported files for further analysis, comparison between conditions, and statistical evaluation (ANOVA, uncertainty propagation).

---

## 5. Output Files

The application generates several categories of output files at different stages.

- **Converted spectra (`.txt`)**
  - Location: subfolder named after the day root (e.g. `.../250317/`).
  - One file per `.mpa` and per ADC channel, with dead time factor in the header and channel/count pairs in the body.

- **Calibration exports**
  - Optional text files containing calibration peaks and the fitted linear calibration parameters.
  - Calibration coefficients may also be written back into the configuration Excel file.

- **Loop / ROI integration outputs**
  - Files (often Excel) containing excitation profiles: energy, normalized counts, and uncertainties.
  - Organized per sample or scenario as defined in the configuration file.

- **Filtered profiles (after peak removal)**
  - Profiles where parasitic peak points have been removed, stored in a `filtered/` subfolder.

- **Sigmoid fit results and images**
  - Numerical summaries of fit parameters (plateau values, midpoint, width, residuals).
  - Plots (`.png`) showing data points and fitted curves for visual inspection.

These outputs can be directly used in subsequent analysis scripts (Python, R, etc.) and in statistical post-processing such as ANOVA and uncertainty propagation.

---

## 6. Methodological Details

### 6.1 Conversion and Dead Time Correction

#### Input data

The conversion step starts from raw `.mpa` files produced by the acquisition system. These files contain several structured sections associated with the different detector channels, including metadata such as live time and real time for each ADC block.

A typical detector section may contain information of the form:

```text
[ADC1]
livetime = ...
realtime = ...
```

During conversion, the software parses the file to identify each ADC section, extracts the corresponding acquisition metadata, and exports the spectrum as a structured text file containing a header and channel-count pairs.

#### Mathematical transformation

Because the detector cannot record new events while processing a previous one, part of the acquisition time is effectively lost. This effect is described by the **dead time**.

The dead time correction factor is computed from the ratio between real acquisition time and live acquisition time:

$$
F_{\mathrm{dead}} = \frac{t_{\mathrm{real}}}{t_{\mathrm{live}}}
$$

where $t_{\mathrm{real}}$ is the total acquisition time and $t_{\mathrm{live}}$ is the effective counting time.

The corresponding dead-time percentage is:

$$
\mathrm{Dead\ Time}(\%) = \left(F_{\mathrm{dead}} - 1\right)\times 100
$$

This factor is written in the header of the exported `.txt` file and is later reused during the ROI integration step to correct the measured counts.

#### Error sources

Several effects can affect the quality of the dead time estimate:

- Missing or malformed metadata in the original `.mpa` file.
- Invalid or null live-time value, which prevents a meaningful correction factor from being computed.
- Imperfect parsing if the raw acquisition file structure differs from the expected format.

If no valid value can be extracted, the correction cannot be reliably applied and the associated spectrum must be interpreted with caution.

#### Impact on the next step

The converted `.txt` files constitute the standard input format for the rest of the application. They are used directly in the Calibration window and in the Processing loop.

The dead time factor stored in the file header is essential because it is applied later to recover an estimate of the true number of detected events inside the selected ROI. Any bias in this factor propagates to the normalized counts and therefore to the excitation profile.

---

### 6.2 Energy Calibration

#### Input data

The calibration step uses one converted spectrum `.txt` at a time. Each file contains the ADC channel number and the corresponding counts, together with the dead time factor written in the header during the conversion stage.

The user identifies several known peaks in the spectrum and provides the corresponding reference energies in keV. For each selected peak, the software extracts a local fitting interval around the approximate peak position.

#### Mathematical transformation

Each selected peak is fitted with a Gaussian model including a linear background:

$$
f(x) = A \exp\left(-\frac{(x-x_0)^2}{2\sigma^2}\right) + b + cx
$$

where $A$ is the peak amplitude, $x_0$ is the centroid channel, $\sigma$ is the Gaussian width, and $b$ and $c$ describe the local linear background.

The fitted centroid $x_0$ is taken as the best estimate of the channel position of the calibration peak, and its uncertainty is extracted from the covariance matrix of the fit.

Once several peaks have been identified, the software performs a weighted linear regression between centroid channels and reference energies:

$$
E = a \cdot C + b
$$

where $E$ is the energy in keV, $C$ is the channel number, $a$ is the calibration slope, and $b$ is the calibration intercept. The fit is weighted using the inverse squared uncertainty on the centroid positions. The software also computes the uncertainties on $a$ and $b$, as well as the coefficient of determination $R^2$.

#### Error sources

The calibration uncertainty is influenced by several effects:

- Inaccurate peak selection by the user.
- Poor Gaussian convergence for weak, broad, or overlapping peaks.
- Limited number of reference peaks.
- Non-linearity of the detector response outside the fitted range.
- Uncertainty on the reference energies themselves, if relevant in the experimental context.

If the selected peaks do not sufficiently constrain the calibration line, the slope and intercept uncertainties increase and the energy conversion becomes less reliable.

#### Impact on the next step

The calibration coefficients $a$ and $b$ are written into the configuration file and are later used to convert ROI limits expressed in energy into channel limits used in the processing loop. Any calibration error therefore propagates directly to the ROI boundaries and affects the integrated counts computed in the next stage.

---

### 6.3 ROI Integration and Normalization

#### Input data

The ROI integration step uses:

- The converted spectral files generated during the conversion stage.
- The calibration coefficients obtained during the calibration stage.
- The ROI limits selected by the user in energy units.
- The charge-related signal stored in the corresponding ADC channel used for normalization.
- The experimental metadata stored in the configuration Excel file.

For each scenario, the program loops over a set of files and associates them with the corresponding beam or terminal-voltage values extracted from the measurement Excel files.

#### Mathematical transformation

The selected ROI is first converted from energy space to channel space using the linear calibration:

$$
C = \frac{E - b}{a}
$$

where $a$ and $b$ are the slope and intercept determined during calibration.

For each spectrum, the counts inside the ROI are integrated. If the ROI limits are not integer channel numbers, the boundary counts are linearly interpolated so that fractional channel limits can be handled consistently.

The total number of counts in the ROI is then corrected for dead time:

$$
N = N_{\mathrm{raw}} \times F_{\mathrm{dead}}
$$

The integrated charge is estimated from the dedicated charge channel and scaled by a conversion factor:

$$
Q = S_{\mathrm{charge}} \times 10^{-4}
$$

where $S_{\mathrm{charge}}$ is the integrated value of the charge-monitor channel.

The normalized count rate used to build the excitation profile is then:

$$
NC = \frac{N}{Q}
$$

This quantity is stored together with the corresponding beam energy for each file in the loop.

#### Error sources

Several factors contribute to the uncertainty on the normalized counts:

- Calibration uncertainty, which shifts the ROI boundaries.
- Statistical uncertainty on the integrated counts, typically treated as Poissonian.
- Uncertainty on the charge normalization.
- Missing files or incomplete data in the acquisition sequence.
- Interpolation errors at non-integer ROI boundaries.

#### Impact on the next step

The ROI integration and normalization step produces the excitation profiles used in all subsequent analyses. Each output file contains energy, normalized counts, and associated uncertainties. These profiles are the direct input for optional peak removal and for the final sigmoid fitting stage.

---

### 6.4 Peak Removal and Data Cleaning

#### Input data

The peak-removal step uses the excitation profiles generated by the loop step, typically stored as Excel files with columns such as energy, normalized counts, and uncertainties.

The user also defines a target energy, a search window around this energy, and a half-width defining the interval to be removed when an unwanted peak is detected.

#### Mathematical transformation

The program first restricts the profile to a local energy interval around the target energy:

$$
[E_{\mathrm{center}} - \Delta E,\; E_{\mathrm{center}} + \Delta E]
$$

where $E_{\mathrm{center}}$ is the selected resonance energy and $\Delta E$ is the search window.

Within this interval, a peak-detection algorithm is applied to the normalized counts. If one or more local maxima are found, the detected peak closest to the target energy is selected.

A removal interval is then defined around the detected peak energy $E_{\mathrm{peak}}$:

$$
[E_{\mathrm{peak}} - w,\; E_{\mathrm{peak}} + w]
$$

where $w$ is the chosen half-width. All points located inside this interval are removed from the profile, and the cleaned dataset is saved as a new output file. Diagnostic plots comparing raw and filtered profiles are also generated.

#### Error sources

The peak-removal stage is sensitive to:

- False peak detection in noisy data.
- Incorrect choice of the target energy or search window.
- Excessive removal width, which may suppress useful physical information.
- Insufficient removal width, which may leave part of the parasitic feature in the data.

Since this step modifies the dataset before fitting, it should be applied with care and preferably validated visually using the generated diagnostic plots.

#### Impact on the next step

The cleaned profiles are stored separately and become the preferred input for the sigmoid fit when a build-up peak would otherwise bias the result. If no peak is removed, the sigmoid fit can be applied directly to the raw loop output instead.

---

### 6.5 Sigmoid Fitting and Parameter Extraction

#### Input data

The sigmoid fitting step takes as input either the raw excitation profiles from the loop step or the cleaned profiles produced after peak removal. These profiles contain energy, normalized counts, and uncertainties. Each profile is treated independently.

#### Mathematical transformation

The software fits each profile with a sigmoid model of the form:

$$
y(x) = \frac{L}{1+\exp\left[-k(x-x_0)\right]} + b
$$

where $L$ is the amplitude term, $x_0$ is the midpoint energy, $k$ is the steepness parameter, and $b$ is the baseline offset.

From these parameters, the software derives a characteristic height difference between the upper and lower plateaus:

$$
\Delta H = L - b
$$

The fitting routine also computes a goodness-of-fit indicator $R^2$, stores the fitted curve, and exports both numerical and graphical outputs for each processed profile.

#### Error sources

The fit quality depends on:

- The number and distribution of available points.
- The presence of residual parasitic peaks or outliers.
- The estimated uncertainties used as weights in the fit.
- The suitability of the sigmoid model for the considered profile.

Profiles with too few valid points or strongly non-sigmoidal shapes may lead to unstable or non-physical parameters.

#### Impact on the next step

The parameters extracted from the sigmoid fit provide a compact description of the excitation profile and can be used to compare samples, group measurements, or perform higher-level statistical analysis. In the current workflow, the plateau difference and related fit parameters are among the main quantities retained for interpretation.

---

### 6.6 Uncertainty Estimation at Each Step

#### Input data

Uncertainty propagation combines information from several stages of the workflow:

- The uncertainty on peak centroid positions from Gaussian fitting.
- The uncertainty on calibration coefficients.
- The statistical uncertainty on integrated counts.
- The uncertainty associated with charge normalization.
- The uncertainties stored in the processed excitation profiles.

#### Mathematical transformation

At the calibration stage, the uncertainty on each centroid is extracted from the covariance matrix of the Gaussian fit and used as the weight in the linear energy calibration.

During ROI integration, the code combines a counting-statistics term and a calibration-related term for the corrected counts $N$. The statistical term is approximated by:

$$
\sigma_{\mathrm{stat},N} = \sqrt{N}
$$

and the calibration-related contribution is:

$$
\sigma_{\mathrm{cal},N} = \frac{\varepsilon_{\mathrm{cal}}}{100}\,N
$$

where $\varepsilon_{\mathrm{cal}}$ is the relative calibration error in percent.

The total uncertainty on $N$ is combined quadratically:

$$
\sigma_N = \sqrt{\sigma_{\mathrm{stat},N}^2 + \sigma_{\mathrm{cal},N}^2}
$$

An uncertainty is also associated with the charge normalization term. The uncertainty on the normalized count NC = N/Q is propagated using the relative-error formula:

$$
\sigma_{NC} = NC \sqrt{\left(\frac{\sigma_N}{N}\right)^2 + \left(\frac{\sigma_Q}{Q}\right)^2}
$$

These values are stored in the output profiles and may be used later as weights in the sigmoid fit.

#### Error sources

The uncertainty model currently implemented includes the main experimental contributions, but it remains an approximation. Its accuracy depends on:

- The validity of the Poisson approximation for the corrected counts.
- The quality of the calibration error estimate.
- The reliability of the charge normalization factor.
- The assumption that different sources of uncertainty are independent.

Additional systematic effects may still need to be incorporated depending on the final scientific use of the results.

#### Impact on the next step

Uncertainty estimates are essential for judging the quality and comparability of the processed profiles. They also affect the weighting of the sigmoid fit and therefore the stability of the extracted parameters. A realistic uncertainty budget is therefore required before any robust statistical comparison between samples can be performed.

---

### 6.7 Statistical Comparison Using ANOVA

#### Input data

The ANOVA step uses grouped values derived from the sigmoid fitting stage (for example `diff_height` values grouped by measurement day or condition), provided as an Excel file with at least one grouping column and one numerical value column.

#### Mathematical transformation

A one-way ANOVA is used to compare grouped repeated measurements and to estimate a practical repeatability-related uncertainty contribution.

In the current implementation, the selected columns are internally renamed to `value` and `group`, and the model is fitted with:

`value ~ C(group)`

The ANOVA table is computed with `statsmodels`. The factor row is read from `C(group)`, while the residual row is used to estimate the within-group variance.

The implemented quantities are:

- `u_intra = sqrt(MS_residual)`
- `u_inter = sqrt((MS_inter - MS_intra) / n_eff)` when `MS_inter > MS_intra`
- `u_total = sqrt(u_intra² + u_inter²)`
- `u_rel = u_total / mean(value)`

Residual diagnostics currently include Shapiro-Wilk and Jarque-Bera tests, and optional visual inspection through Q-Q plots and residual plots.

If the residual normality assumption is not sufficiently satisfied, a non-parametric alternative (Kruskal–Wallis) is used instead of classical ANOVA.

#### Error sources

This ANOVA-derived uncertainty is a practical indicator of repeatability-related variability, not a complete metrological uncertainty budget. Its interpretation becomes unreliable when:

- the number of repetitions per group is too small,
- residual degrees of freedom are very low,
- group sizes are strongly unbalanced,
- residual diagnostics are not satisfactory.

A practical guideline is: fewer than 3 values per group is not recommended; 3 values per group is acceptable for exploratory use only; 5 or more values per group is preferred for stable interpretation.

#### Impact on the next step

The ANOVA-derived uncertainty term (`u_total`) is one of the contributions to the full uncertainty budget described in Section 2.3. It is combined with the propagated experimental contributions (calibration, dead-time, normalization) to produce the final uncertainty estimate associated with the measurement result.

---

## 7. Code Architecture

### 7.1 Project Structure

The codebase is organized into two main folders. The `core/` folder contains the scientific computation functions used by the interface. The `gui/` folder contains the graphical interface for each tab. The `temp/` directory is used as a temporary storage location for processing outputs when no output folder has been specified by the user; its contents are cleared when the application is closed.

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
│   ├── etallonnage.py
│   └── uncertainty.py
├── gui/
│   ├── conversion_tab.py
│   ├── calibration_tab.py
│   ├── Loop_tab.py
│   └── ANOVA_tab.py
└── temp/
```

---

### 7.2 Module Responsibilities

#### Interface layer (`gui/` and `main.py`)

- **`main.py`**: entry point of the application. Initializes the Tkinter window, manages tab layout and navigation, maintains the global application state (`app_state`), and provides access to the uncertainty budget interface.

- **`gui/conversion_tab.py`**: graphical interface for converting raw `.mpa` files to `.txt` spectra. Handles file and folder selection, progress display, and conversion log.

- **`gui/calibration_tab.py`**: graphical interface for the channel-to-energy calibration. Handles spectrum loading, interactive peak selection, Gaussian fitting, linear calibration computation, and storage of calibration parameters.

- **`gui/Loop_tab.py`**: graphical interface for the main RNRA processing loop. Manages Excel configuration loading, ROI definition, count integration and normalization, carbon build-up peak removal, sigmoid fitting, and profile export.

- **`gui/ANOVA_tab.py`**: graphical interface for the statistical analysis of sigmoid-derived parameters. Supports one-way ANOVA and Kruskal–Wallis testing, with normality and homogeneity diagnostics and optional diagnostic plot generation.

#### Computation layer (`core/`)

- **`core/calibration.py`**: low-level functions for reading spectra, Gaussian peak fitting, and weighted linear regression from channel to energy. Returns calibration coefficients and their uncertainties.

- **`core/etallonnage.py`**: calibration quality evaluation. Computes the global relative RMS error and the uncertainties associated with the calibration coefficients, based on the covariance matrix of the regression.

- **`core/Loop_fonction.py`**: core logic of the RNRA processing loop. Reads measurement files, integrates counts within the selected ROI, normalizes by integrated charge, constructs excitation profiles, and exports results.

- **`core/Transform_functions.py`**: profile post-processing functions. Includes carbon build-up peak removal by energy window, sigmoid fitting of excitation profiles, and extraction of fit parameters.

- **`core/uncertainty.py`**: computes the global uncertainty budget by aggregating contributions from calibration, excitation profiles, and sigmoid fit. Outputs a structured table of contributions and combined uncertainty.

- **`core/file_io.py`**: file reading and writing utilities shared across modules (`.mpa` parsing, `.txt` and Excel import/export).

- **`core/ANOVA.py`**: statistical analysis functions. Implements one-way ANOVA and Kruskal–Wallis testing, variance decomposition, uncertainty estimation (u_intra, u_inter, u_total), and residual diagnostic tests.

---

### 7.3 Data Flow

The application is organized into two principal layers. The `gui/` modules manage the user interface — windows, controls, and visualization — and delegate all scientific computation to the functions defined in `core/`.

The `core/` modules work directly with spectra and result files: they read raw data, perform numerical processing (calibration, ROI integration, sigmoid fitting, uncertainty propagation, statistical analysis), and write or export results to Excel or text files. They then return results and file paths to the calling GUI tab, which updates the global application state (`app_state`) and displays the results on screen.

This separation ensures that the scientific logic remains independent of the interface and can be called, tested, or extended without modifying the GUI code.

---

## 8. Limitations

### 8.1 Calibration

- The calibration model assumes a predominantly linear detector response over the selected energy range. Significant non-linearity outside the calibrated interval will degrade the accuracy of the energy conversion.
- Calibration quality depends on the number and distribution of reference peaks. Too few peaks, or peaks clustered in a narrow channel range, increase the uncertainties on slope and intercept and reduce the reliability of the energy scale.
- Poor Gaussian convergence for weak, broad, or overlapping peaks can introduce systematic errors in the centroid positions used for calibration.

### 8.2 Dead-Time Correction

- Dead-time correction relies on live-time and real-time metadata extracted from `.mpa` files. Missing, null, or corrupted header values prevent a reliable correction factor from being computed, and the corresponding spectrum must be interpreted with caution.
- Imperfect parsing of the raw acquisition file structure — if it deviates from the expected format — may silently produce incorrect metadata extraction.

### 8.3 Uncertainty Model

- The current uncertainty model is simplified and may not include every systematic contribution relevant for a full metrological analysis. In particular, it does not yet cover all possible sources of systematic bias (e.g. beam current drift, detector gain instability, or sample inhomogeneity).
- The Poisson approximation for counting statistics is applied to dead-time-corrected counts, which is a commonly used approximation but not exact.
- Different uncertainty contributions are combined under the assumption of independence, which may not hold in all experimental conditions.

### 8.4 Peak Removal

- The build-up peak removal algorithm relies on local peak detection within a user-defined energy window. False detections can occur in noisy profiles, leading to incorrect removal of physically meaningful data points.
- An excessive removal half-width may suppress part of the excitation profile itself, biasing the subsequent sigmoid fit. An insufficient half-width may leave parasitic features in the data.
- Peak removal results should always be validated visually using the generated diagnostic plots before proceeding to sigmoid fitting.

### 8.5 Sigmoid Fitting

- The sigmoid model assumes a specific functional form for the excitation profile. Profiles that deviate significantly from a standard sigmoid shape (e.g. due to sample inhomogeneity or multiple hydrogen layers) may produce unstable or non-physical fit parameters.
- Profiles with too few valid points after peak removal may not constrain the fit reliably.
- Sigmoid fit results should always be checked visually before final interpretation.

### 8.6 ANOVA and Statistical Analysis

- ANOVA-based uncertainty estimation becomes unreliable for very small datasets. Fewer than 3 repeated values per group is not recommended; 5 or more is preferred for stable estimates.
- The ANOVA model does not account for systematic errors; it estimates only the random component of variability.
- If residual normality or variance homogeneity assumptions are violated and the non-parametric alternative (Kruskal–Wallis) is used, the uncertainty decomposition into inter- and intra-group components is no longer directly applicable.

### 8.7 Input File Format

- All input Excel files must follow the expected column structure required by each processing tab (Conversion, Calibration, Processing, ANOVA). Non-conforming files will cause errors or silent failures in the processing loop.
- The software does not currently perform exhaustive validation of input file content beyond checking for the presence of required column names.

---

## 9. References

*[To be completed.]*