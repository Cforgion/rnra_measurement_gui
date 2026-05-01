# USER GUIDE - RNRA data processing and error management

## Table of Contents

- [1. Introduction](#1-introduction)
- [2. Scientific Background](#2-scientific-background)
- [3. Interface Description](#4-interface-description)
- [4. Processing Workflow](#5-processing-workflow)
- [5. Output Files](#6-output-files)
- [6. Methodological Details](#7-methodological-details)
- [7. Code Architecture](#8-Code-Architecture)
- [8. Limitations](#9-limitations)
- [9. References](#10-references)

## 1. Introduction
This tool performs the analysis of hydrogen profiling measurements from the raw MPA file to the excitation curve and final sigmoid fit. In addition to the statistical evaluation of repeatability through ANOVA, the workflow includes the propagation of measurement uncertainty at each processing stage, so that the final result reflects not only random variability but also contributions arising from calibration, dead-time correction, and nonlinear sigmoid fitting.
The uncertainty evaluation is not limited to ANOVA. ANOVA is used to estimate the random component associated with repeated measurements, whereas the full uncertainty budget is obtained by propagating all relevant contributions through the measurement model, including calibration uncertainty, dead-time correction uncertainty, and fit-parameter uncertainty from the sigmoid adjustment. <span style="color:red;">A verifier que c'est bien ce qui est fait ainsi 2 en un budget + ANOVA , c'est ce que je rajoute par rapport a l'année derniere</span>

Voici la traduction en anglais, en gardant un style **user guide / scientific documentation**, fluide et cohérent avec ton texte :

---

## 2. Scientific principle

<span style="color:red;">ADD also a section on the uncertainty budget.</span>

---

### 2.1 Resonant Nuclear Reaction Analysis (RNRA)

Resonant Nuclear Reaction Analysis (RNRA) is an analytical technique used to determine the concentration profile of an element within a material as a function of depth. Its principle is based on a nuclear reaction exhibiting a resonance at a well-defined energy: when the energy of the incident ions matches the resonance energy, the reaction cross-section reaches a maximum. This enables selective probing of a specific depth, by exploiting the relationship between the incident beam energy and the energy loss of ions in matter. The resonance width, which defines the energy range around the resonance where the reaction remains significant, directly determines the depth resolution: the narrower the resonance, the higher the spatial resolution.

In our case, the goal is hydrogen profiling. For this purpose, a TiH₂ pellet is used due to its high hydrogen content, homogeneity, and stability under irradiation. Measurements rely on the interaction between ¹⁵N³⁺ ions and ¹H nuclei via the following nuclear reaction:

**¹⁵N(¹H, αγ)¹²C**

This reaction exhibits a strong resonance at 6.385 MeV (width 1.8 keV, σ_max = 1650 mb, see Fig. 1). At this energy, the interaction probability is maximal, providing excellent selectivity. The reaction proceeds in two steps:

1. Hydrogen interacts with nitrogen-15 to form an excited, short-lived oxygen-16 compound nucleus.
2. This nucleus decays by emitting an alpha particle and an excited carbon-12 nucleus, which subsequently returns to its ground state by emitting a 4.43 MeV gamma ray, which is detected to quantify the reaction.

As ¹⁵N³⁺ ions penetrate matter, they progressively lose energy according to the stopping power S = dE/dx, which depends on both the material and the ion species. By varying the incident beam energy, each energy value can be associated with a specific depth in the sample, allowing depth scanning (see Fig. 2). For incident energies slightly below resonance, few gamma rays are detected. As the energy approaches resonance, the gamma yield increases rapidly until reaching a plateau where the signal stabilizes. The resulting curve has a sigmoidal shape (see Fig. 4b), characteristic of energy-dependent depth probing.

However, this excitation curve does not directly represent the concentration profile. A deconvolution step is required to correct for beam energy loss effects within the sample. This procedure converts the gamma signal variation into an accurate hydrogen depth distribution profile. From the deconvoluted excitation curves, a quantitative hydrogen concentration profile can be extracted (see Louis Dupont’s thesis for a detailed description).

The number of detected events is given by [11,12]:

**N = Q_c · Ω · σ(E_r) · N_t**

where:

* **Q_c**: integrated charge, i.e. the total charge delivered by ions impacting the target. It is obtained by integrating the beam current over irradiation time and is expressed in microcoulombs (µC). Dividing by the ion charge gives the total number of particles incident on the sample; it is a key normalization factor for the detected signal.
* **Ω**: detector solid angle (sr).
* **σ(E_r)**: reaction cross-section at resonance energy (cm²).
* **N_t**: areal target atom density (at/cm²).

RNRA is particularly well suited for light element analysis such as hydrogen. Its main advantages are:

* **Excellent sensitivity** (down to ~10 ppm atomic), enabled by the resonance and its narrow width;
* **High depth resolution**, directly related to the narrow resonance width;
* **High selectivity**, since the 4.43 MeV gamma line is weakly affected by background (natural radioactivity is typically below ~3 MeV);
* **Non-destructive nature**, provided beam-induced hydrogen diffusion remains limited.

However, the method requires:

* a particle accelerator;
* consideration of matrix effects, i.e. all phenomena related to sample composition and structure that may affect measurement accuracy.

---

### 2.2 Analysis of Variance (ANOVA)

To quantify measurement reproducibility and estimate random uncertainty, an ANOVA (ANalysis Of VAriance) test is applied. This statistical test compares the means of multiple groups—in this case, measurements acquired on different days—to determine whether statistically significant differences exist. The dataset consists of five measurements per day over eight acquisition days.

ANOVA is based on the following hypotheses [14]:

* **H₀ (null hypothesis)**: all group means are equal, i.e. no significant difference exists between days.
* **H₁ (alternative hypothesis)**: at least one group mean differs.

The decision to reject or not reject H₀ is based on the **p-value**. This quantity represents the probability of incorrectly rejecting the null hypothesis when it is true (Type I error). For example, a p-value of 0.23 means that rejecting H₀ carries a 23% risk of incorrectly concluding that differences exist between groups.

ANOVA can also be interpreted as a linear regression model with categorical variables:

**ŷ = Σ βᵢ Gᵢ + ε**

where:

* **ŷ** is the model prediction,
* **Gᵢ** indicates membership of observation to group *i*,
* **βᵢ** is the mean of group *i*,
* **ε** is the residual error term.

Residuals are defined as:

**res = y_obs − ŷ**

Before applying ANOVA, three assumptions must be verified:

* **Independence of measurements**, ensured by experimental design;
* **Normality of residuals**, checked using Q-Q plots¹ (see Fig. 6), histograms, or formal tests such as Shapiro–Wilk [16];
* **Homogeneity of variances**, assessed using violin plots (see Fig. 7) or statistical tests such as Levene’s test [17].

If any assumption is violated, classical ANOVA cannot be applied, as it relies on the assumption that the test statistic follows a Fisher–Snedecor distribution [18].

When assumptions are satisfied, the F-statistic follows a Fisher–Snedecor distribution with k−1 and k(n−1) degrees of freedom, where k is the number of groups and n the number of measurements per group (see Fig. 8). This distribution compares inter-group variance to intra-group variance: larger F values indicate stronger evidence of differences between groups. If F exceeds the critical value F_critical, determined by the significance level α, the null hypothesis is rejected.

If normality or homogeneity assumptions are not satisfied, a non-parametric alternative such as the **Kruskal–Wallis test** [19] must be used. This test is based on rank ordering rather than raw values and does not assume a Fisher distribution. It also provides a p-value interpreted in the same way.

ANOVA also allows estimation of **random uncertainty**, an approach previously applied in ion beam measurements [20,21]. Systematic errors are not included in this model. Within-group and between-group variances are used to compute the **Mean Squares (MS)**:

**MS_inter = SS_inter / (k − 1)**
**MS_intra = SS_intra / (k(n − 1))**

From these quantities, two uncertainty contributions are derived:

* **Between-group uncertainty (u_inter):**

u_inter = √((MS_inter − MS_intra) / n)

If MS_inter < MS_intra, inter-group variance is negligible compared to intra-group variance, confirming H₀.

* **Within-group uncertainty (u_intra):**

u_intra = √MS_intra

The **combined uncertainty** is:

**u_c = √(u_inter² + u_intra²)**

The **relative uncertainty** is:

**u_rel = (u_c / ȳ) × 100**

where ȳ is the overall mean.

---

¹ A quantile is a value dividing a dataset into intervals containing equal numbers of observations. Common examples include quartiles and the median.

---

### 2.3 Uncertainty budget

## 3. Interface Description

### 4.1 Conversion Window

This window performs the batch conversion of raw `.mpa` acquisition files into structured `.txt` spectra that can be used in the calibration and processing steps. 
The conversion routine reads the acquisition metadata, computes the dead time correction factor, and exports one text file per ADC channel with a standardized format. 

#### Layout and controls

The **Conversion** tab contains the following elements: 

- **Configuration file (Excel)**  
  - Read‑only text field displaying the path to the global configuration Excel file.  
  - **Browse** button to select the configuration file (e.g. `config.xlsx`).

- **Day root (sample name root)**  
  - Text entry labelled e.g. `day racine samplename` where the user enters the day or sample root, such as `250317`.  
  - This value is used to filter the rows corresponding to a given measurement day in the configuration file.

- **Output folder for .txt files**  
  - Text entry labelled `Folder exit for .txt` displaying the path where converted `.txt` files will be written.  
  - **Browse** button to choose or create this directory.

- **Conversion controls**  
  - **convert .mpa → .txt** button to start the conversion for the selected day.  
  - Progress bar indicating the current file index and total number of files being processed.  
  - Status label showing messages such as “Waiting”, “Conversion in progress…”, “Finished”, or “Finished with errors”.

- **Log window**  
  - Multi‑line text area showing detailed messages, including which folders are used, which files are converted, and any encountered errors.

#### User actions

1. **Load the configuration file** 
   - Click **Browse** in the “config Excel” section.  
   - Select the Excel configuration file used to describe your measurements (sample names, folders, first/last file numbers, etc.).  
   - The selected path appears in the read‑only entry.

2. **Define the day root** 
   - In the **day root** entry, type the day/sample root corresponding to the measurement series you want to convert (for example `250317`).  
   - Internally, the software looks for rows in the configuration file whose sample name starts with this root and retrieves the corresponding `mpafolder` path.

3. **Choose the output folder for `.txt` files** 
   - In **Folder exit for .txt**, click **Browse** and select a base directory in which the converted files will be stored.  
   - The program will create (if necessary) a subfolder named after the day root (e.g. `…/250317/`) and place all `.txt` outputs there.

4. **Launch the conversion** 
   - Click **convert .mpa → .txt**.  
   - The software scans the `mpafolder` corresponding to the selected day in the configuration file, then converts all `.mpa` files found in this folder.  
   - Progress is displayed in the progress bar and status label; detailed messages appear in the log.

4. **Check for errors** 
   - At the end of the process, if errors occurred (missing folder, unreadable `.mpa` file, etc.), they are listed in the log area.  
   - The status label indicates whether the conversion finished successfully or with errors.

#### Output text file structure

For each `.mpa` file and for each ADC channel, one `.txt` file is generated. 

- **File naming**

  - General convention:  
    `filename_ADCname.txt`  
  - `filename`: base name of the original `.mpa` file (without extension).  
  - `ADCname`: ADC channel identifier (`ADC0`, `ADC1`, etc.).

  Example:  
  - Input file: `sample01.mpa` with two ADC channels (`ADC1`, `ADC2`)  
  - Output files:  
    - `sample01_ADC1.txt`  
    - `sample01_ADC2.txt`  

- **File content**

  1. **Header line**  
     - First line, typically containing the dead time factor extracted from the `.mpa` metadata, such as:  
       `Dead time factor = 1.023`  

  2. **Data lines** (one measurement per line)  
     - `Channel`: integer ADC channel index.  
     - `Count`: measured counts in this channel.  

All exported text files are formatted to be directly readable in Python (via `numpy.loadtxt`, `pandas.read_csv`) or in other scientific data processing tools. 

***

### 4.2 Calibration Window

The **Calibration** tab is used to build an energy calibration curve $E = a \cdot C + b$ from one or several spectra in `.txt` format generated by the conversion step. 
The user interactively selects peaks on a displayed spectrum, fits a Gaussian shape to each peak to extract the centroid channel, associates each centroid with a known reference energy, then performs a weighted linear regression. 

#### Layout and controls

The **Calibration** window is organised into three areas: 

- **Left panel – File and peak management**

  - **“Load spectrum”** button  
    - Opens a file dialog to select a spectrum `.txt` file (one ADC channel) produced by the conversion window.  
    - After loading, the filename and dead time factor are displayed.

  - **File information labels**  
    - Label showing the currently loaded spectrum file name.  
    - Label showing the associated dead time factor if present in the header.

  - **Peak selection area**  
    - Instruction label (“Click on the plot to select a peak”).  
    - Label showing the currently selected interval in channels (center and width).  
    - Entry field for the **reference energy (keV)** corresponding to the selected peak.  
    - **Fit Gaussian** button to launch the peak fit for the current selection.  
    - **Reset selection** button to clear the current selection.

  - **Peak list (Treeview)**  
    - Table with one row per identified calibration peak.  
    - Columns:  
      - Index (internal peak number)  
      - **Channel** (fitted centroid)  
      - **Energy (keV)** (reference value entered by the user)  

  - **Peak management buttons**  
    - **Delete selected peak**: removes the highlighted peak from the list and from the internal data.  
    - **Clear all peaks**: removes all peaks and resets the calibration state.

  - **Calibration controls**  
    - **Run calibration** button (enabled when at least two peaks are defined).  
    - Label showing the calibration result or a message such as “Minimum 2 peaks required”.

- **Center panel – Spectrum and fits**

  - Matplotlib figure displaying the loaded spectrum (counts vs. channel).  
  - Tools for zoom, pan, etc. (Matplotlib toolbar).  
  - An interactive **SpanSelector** allowing the user to select a channel interval by clicking and dragging on the plot. 
  - After fitting, vertical lines and Gaussian curves are drawn to show the fitted peaks.

- **Right panel – Detailed results and export**

  - Text area listing:  
    - General information about the loaded spectrum.  
    - Details of each peak fit (centroid, error, sigma, amplitude).  
    - Calibration results (slope, intercept, goodness of fit, relative RMS).  
  - **Export results** button to save the list of peaks and the calibration summary in a text file. 

#### User actions

1. **Load a spectrum** 
   - Click **Load spectrum** and select a `.txt` file produced by the conversion window.  
   - The program reads the header and data, displays the spectrum, and shows the dead time factor if available.  
   - The plot is updated to show counts versus channel index.

2. **Select a peak** 
   - Option A: Click and drag on the spectrum to select a peak region (SpanSelector).  
     - The selected center and approximate half‑width (in channels) are computed automatically.  
   - Option B: Simply click on the spectrum to set an approximate center; an internal rule computes a suitable half‑width depending on the channel.  
   - The current selection is displayed as `center = …, width = …` in the corresponding label.

3. **Associate a reference energy** 
   - In the **Energy (keV)** entry, type the known energy of the selected peak (e.g. a resonance or gamma line).  
   - This value will be used as the calibration reference for this peak.

4. **Fit a Gaussian peak** 
   - Click **Fit Gaussian**.  
   - The program extracts the data around the selected center, performs a Gaussian fit, and returns:  
     - Centroid $C$ (fitted channel),  
     - Sigma (peak width),  
     - Amplitude,  
     - Uncertainty on the centroid.  
   - The peak is added to the Treeview with its centroid and reference energy, and details are appended to the text area.

4. **Repeat for all calibration peaks** 
   - Repeat steps 2–4 for each reference line you want to include in the calibration.  
   - Once at least two peaks are defined, the **Run calibration** button is enabled.

5. **Run the linear calibration** 
   - Click **Run calibration**.  
   - The software performs a (weighted) linear regression $E = a \cdot C + b$ using the centroids and their uncertainties.  
   - It computes:  
     - Slope $a$ and intercept $b$,  
     - Uncertainties on $a$ and $b$,  
     - Coefficient of determination $R^2$,  
     - Global RMS error and relative RMS (in %).  
   - A summary string is displayed in the calibration result label and in the text area.

6. **Update the configuration file (if applicable)** 
   - If the application is used together with the Conversion and Processing tabs, and a global configuration Excel file is defined, the calibration results can be written back into the configuration file for the current group/day.  
   - The corresponding columns (e.g. `slope`, `intercept`, `errorcalib`) are updated for the matching rows, so the processing loop can use them automatically.

7. **Export calibration results (optional)** 
   - Click **Export results** to save:  
     - The list of peaks (index, centroid, sigma, amplitude, energy, centroid error),  
     - The linear calibration summary (slope, intercept, uncertainties, $R^2$, relative RMS).  
   - The export is written to a user‑selected text file.

#### Output and stored parameters

- The main **numerical result** is a linear calibration $E = a \cdot C + b$ with associated uncertainties and quality indicators. 
- These parameters are either stored in memory (for immediate use) or written into the configuration Excel file to be reused by the processing loop. 

***

### 4.3 Processing (Loop, Peak Removal, Sigmoid Fit)

The **Processing** window controls the full data‑processing pipeline, from ROI integration to optional peak removal and final sigmoid fitting of the excitation profiles. 
It uses the configuration Excel file and the calibration parameters to convert profiles from channel space to energy space and to generate processed outputs for further analysis. 

#### Layout and controls

The **Processing / Loop** tab is structured as follows: 

- **Configuration and ROI (left panel)**

  - **Configuration file** section  
    - Read‑only entry showing the path to the configuration Excel file.  
    - **Load Excel configuration file** button.

  - **ROI selection** section  
    - Entry showing or allowing manual edit of the ROI in energy (e.g. `Emin–Emax keV`).  
    - **Choose ROI on a spectrum** button to open an interactive window where the user selects the ROI directly on a reference spectrum (energy vs counts).

  - **Results saving options**  
    - Check box **Save results** to enable/disable saving of processed profiles.  
    - Output folder entry and **Browse** button (enabled only if “Save results” is checked).

  - **Loop execution**  
    - **Process files** (or similar label) button to start the loop over all scenarios described in the configuration file.

- **Carbon build‑up peak removal** 

  - Input fields:  
    - **Energy center (keV)**: resonance energy from which the build‑up peak is removed (default ~6385 keV for the 15N(H, α, γ)12C resonance).  
    - **Search window (keV)**: total energy window around the center where the peak search is performed.  
    - **Removal half‑width (keV)**: half‑width of the interval to be removed once a peak is detected.  
  - **Remove build‑up peak** button to apply the removal to all profiles previously calculated by the loop.

- **Sigmoid fitting** 

  - **Run sigmoid fit on output profiles** button.  
  - Uses either the raw loop output or the “filtered” folder (after peak removal) as input.  
  - Produces sigmoid fits and associated parameters for each profile.

- **Visualization options** 

  - **Display output profile** button to open a file dialog and select an output `.xlsx` or `.png` file.  
  - The selected file is displayed in the Matplotlib figure on the right (profiles or images).

- **Right panel – Plot and detailed log**

  - Matplotlib figure with axes labelled “Energy (keV)” and “NC” or similar.  
  - Toolbar for zoom/pan.  
  - Text area showing detailed log messages (loop progress, errors, fit results, etc.).

#### User actions

##### A. Loop over ROI

1. **Load the configuration file** 
   - In the **Configuration file** section, click **Load Excel configuration file** and select the same Excel file used previously.  
   - The program checks that all required columns are present (sample name, tension folder, data folder, first file, last file, ADC, slope, intercept, calibration error, etc.).

2. **Define the ROI in energy** 
   - Option A – **Manual**: type the ROI in keV in the corresponding entry (e.g. `6400–6600 keV`).  
   - Option B – **Interactive**: click **Choose ROI on a spectrum** to open a dedicated window:  
     - A reference spectrum (converted to energy using the calibration) is displayed.  
     - You can click‑and‑drag to select the energy interval; the selected `Emin` and `Emax` are shown and can be refined numerically.  
     - When validated, the ROI is stored both in energy and in corresponding channel limits.

3. **Choose whether to save results** 
   - If you want to keep all intermediate and final results, check **Save results** and choose an output folder.  
   - If not checked, the program uses an internal temporary directory for the session.

4. **Run the processing loop** 
   - Click **Process files**.  
   - For each scenario (row) in the configuration file, the program:  
     - Reads the relevant `.txt` spectra.  
     - Integrates counts within the selected ROI.  
     - Normalizes by the integrated charge (or other intensity/normalization parameter).  
     - Builds an excitation profile as a function of beam energy.  
   - Results are written to the output folder (one file per scenario, plus summary files if implemented) and messages are displayed in the log field.

##### B. Peak removal (optional)

1. **Set the build‑up energy and windows** 
   - In **Energy center (keV)**, keep the default resonance energy (e.g. 6385 keV) or replace it with the value relevant for your experiment.  
   - Adjust the **search window** and **removal half‑width** if needed (default values are provided in the GUI).

2. **Apply the removal to all profiles** 
   - Ensure the loop has been run at least once (raw profiles exist).  
   - Click **Remove build‑up peak**.  
   - The program scans the output profiles in the selected folder, identifies peaks around the given energy, and removes the corresponding points in the specified interval.  
   - Filtered profiles are saved into a dedicated subfolder (e.g. `filtered`) along with optional diagnostic plots.

##### C. Sigmoid fit

1. **Select the input folder for fitting** 
   - If peak removal was performed, the fitting step uses the **filtered** folder containing cleaned profiles.  
   - Otherwise, it uses the raw output folder of the loop.

2. **Run the sigmoid fits** 
   - Click **Run sigmoid fit on output profiles**.  
   - For each excitation profile, the program fits a sigmoid curve and extracts parameters such as:  
     - Low and high plateau values,  
     - Midpoint energy and width,  
     - Difference between high and low plateau (used to group profiles or compare conditions).  
   - Fit results and diagnostics are saved to the output directory.

##### D. Visualization

1. **Open a processed profile or image** 
   - Click **Display output profile**.  
   - Choose either:  
     - An Excel file (`.xlsx`/`.xls`) containing a profile (columns such as `Energy keV`, `NC`, optionally `uncertainties`), or  
     - An image file (`.png`, `.jpg`, `.jpeg`) generated by the processing pipeline.

2. **Inspect the result** 
   - If an Excel file is selected, the program plots the profile, optionally with error bars, and can overlay the fitted curve if present.  
   - If an image file is selected, it is displayed directly in the plotting area (axes are hidden for a clean display).

#### Output file naming and content (processing)

The exact naming conventions may evolve, but in general the processing step produces: 

- **Loop output files**  
  - Typically one file per scenario/group, containing energy, normalized counts, and optional uncertainties.

- **Filtered profiles** (after peak removal)  
  - Saved in a `filtered` subfolder, with the same or similar naming scheme as the raw outputs.

- **Sigmoid fit outputs**  
  - Files or images summarizing the fit parameters and the quality of the fit for each profile.  

These outputs are then used for further analysis, comparison between samples, and statistical processing (including ANOVA) as described in later sections of the guide. 

***

## 4. Processing Workflow (Overview)

This section summarises the recommended end‑to‑end workflow using the three main windows. 

1. **Configure and convert**  
   - Prepare or update the Excel configuration file describing all measurements (paths, file numbers, ADC, calibration parameters).  
   - Use the **Conversion** window to convert all `.mpa` files for a given day/root into `.txt` spectra.

2. **Calibrate energy**  
   - In the **Calibration** window, load representative spectra and identify several reference peaks.  
   - Fit Gaussian peaks, assign reference energies, and run the linear calibration to obtain $E = a \cdot C + b$.  
   - Store the calibration coefficients in the configuration file.

3. **Process profiles**  
   - In the **Processing** window, load the configuration file.  
   - Define the ROI in energy and run the loop to build excitation profiles for all scenarios.  
   - Optionally, remove the carbon build‑up peak around a given energy and re‑use the cleaned profiles.

4. **Fit and analyse**  
   - Perform sigmoid fits on the final excitation profiles to extract plateau differences and key parameters.  
   - Use the exported Excel/text files and images for further analysis, comparison between conditions, and statistical evaluation (ANOVA, uncertainty propagation, etc.).

***

## 5. Output Files (Overview)

The application generates several categories of output files at different stages. 

- **Converted spectra (`.txt`)**  
  - Location: subfolder of the chosen output directory, named after the day root (e.g. `…/250317/`).  
  - One file per `.mpa` and per ADC channel, with dead time factor in the header and `(channel, count)` pairs in the body.

- **Calibration exports**  
  - Optional text files containing the list of calibration peaks and the fitted linear calibration parameters.  
  - Calibration coefficients may also be written back into the configuration Excel file (columns such as slope, intercept, calibration error).

- **Loop / ROI integration outputs**  
  - Files (often Excel) containing excitation profiles: energy, normalized counts, and uncertainties.  
  - Often organized per sample or per scenario as defined in the configuration file.

- **Filtered profiles (after peak removal)**  
  - Profiles where points in the build‑up peak region have been removed, stored in a dedicated subfolder.  

- **Sigmoid fit results and images**  
  - Numerical summaries of fit parameters (plateau values, midpoint, width, residuals, etc.).  
  - Plots (`.png`/`.jpg`) showing data points and fitted curves for visual inspection.

These outputs can be directly used in subsequent analysis scripts (Python, R, etc.) and in statistical post‑processing such as ANOVA and uncertainty propagation. 




## 6. Methodological Details

### 7.1 Conversion and Dead Time Correction

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

where:

- $t_{\mathrm{real}}$ is the total acquisition time,
- $t_{\mathrm{live}}$ is the effective counting time. 

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

The converted `.txt` files constitute the standard input format for the rest of the application. They are used directly in the calibration window and in the processing loop. [file:1]

The dead time factor stored in the file header is essential because it is applied later to recover an estimate of the true number of detected events inside the selected ROI. Any bias in this factor propagates to the normalized counts and therefore to the excitation profile. 

---

### 7.2 Energy Calibration

#### Input data

The calibration step uses one converted spectrum `.txt` at a time. Each file contains the ADC channel number and the corresponding counts, together with the dead time factor written in the header during the conversion stage. 

The user identifies several known peaks in the spectrum and provides the corresponding reference energies in keV. For each selected peak, the software extracts a local fitting interval around the approximate peak position. 

#### Mathematical transformation

Each selected peak is fitted with a Gaussian-type model including a linear background: 

$$
f(x) = A \exp\left(-\frac{(x-x_0)^2}{2\sigma^2}\right) + b + cx
$$

where:

- $A$ is the peak amplitude,
- $x_0$ is the centroid channel,
- $\sigma$ is the Gaussian width,
- $b$ and $c$ describe the local linear background. 

The fitted centroid $x_0$ is taken as the best estimate of the channel position of the calibration peak, and its uncertainty is extracted from the covariance matrix of the fit. 

Once several peaks have been identified, the software performs a weighted linear regression between centroid channels and reference energies according to: 

$$
E = aC + b
$$

where:

- $E$ is the energy in keV,
- $C$ is the channel number,
- $a$ is the calibration slope,
- $b$ is the calibration intercept. 

The fit is weighted using the inverse squared uncertainty on the centroid positions. The software also computes the uncertainties on $a$ and $b$, as well as a quality indicator such as $R^2$. 

#### Error sources

The calibration uncertainty is influenced by several effects: 

- Inaccurate peak selection by the user.
- Poor Gaussian convergence for weak, broad, or overlapping peaks.
- Limited number of reference peaks.
- Non-linearity of the detector response outside the fitted range.
- Uncertainty on the reference energies themselves, if relevant in the experimental context.

If the selected peaks do not sufficiently constrain the calibration line, the slope and intercept uncertainties increase and the energy conversion becomes less reliable. 

#### Impact on the next step

The calibration coefficients $a$ and $b$ are written into the configuration file and are later used to convert ROI limits expressed in energy into channel limits used in the processing loop. 

Any calibration error therefore propagates directly to the ROI boundaries and affects the integrated counts computed in the next stage. 

---

### 7.3 ROI Integration and Normalization

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
C = \frac{E-b}{a}
$$

where $a$ and $b$ are the slope and intercept determined during calibration. 

For each spectrum, the counts inside the ROI are then integrated. If the ROI limits are not integer channel numbers, the boundary counts are linearly interpolated so that fractional channel limits can be handled consistently. 

The total number of counts in the ROI is then corrected for dead time: 

$$
N = N_{\mathrm{raw}} \times F_{\mathrm{dead}}
$$

The integrated charge is estimated from the dedicated charge channel and scaled by a conversion factor used in the current implementation: 

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

These effects combine to determine the uncertainty associated with each point of the excitation profile. 

#### Impact on the next step

The ROI integration and normalization step produces the excitation profiles used in all subsequent analyses. Each output file contains energy, normalized counts, and associated uncertainties. 

These profiles are the direct input for optional peak removal and for the final sigmoid fitting stage. 

---

### 7.4 Peak Removal and Data Cleaning

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

where $w$ is the chosen half-width. All points located inside this interval are removed from the profile, and the cleaned dataset is saved as a new output file. 

Diagnostic plots comparing raw and filtered profiles are also generated. 

#### Error sources

The peak-removal stage is sensitive to: 

- False peak detection in noisy data.
- Incorrect choice of the target energy or search window.
- Excessive removal width, which may suppress useful physical information.
- Insufficient removal width, which may leave part of the parasitic feature in the data.

Since this step modifies the dataset before fitting, it should be applied with care and preferably validated visually using the generated diagnostic plots. 

#### Impact on the next step

The cleaned profiles are stored separately and become the preferred input for the sigmoid fit when a build-up peak would otherwise bias the result. 

If no peak is removed, the sigmoid fit can be applied directly to the raw loop output instead. 

---

### 7.5 Sigmoid Fitting and Parameter Extraction

#### Input data

The sigmoid fitting step takes as input either the raw excitation profiles from the loop step or the cleaned profiles produced after peak removal. These profiles contain energy, normalized counts, and uncertainties. 

Each profile is treated independently. 

#### Mathematical transformation

The software fits each profile with a sigmoid model of the form: 

$$
y(x) = \frac{L}{1+\exp\left[-k(x-x_0)\right]} + b
$$

where:

- $L$ is the amplitude term,
- $x_0$ is the midpoint energy,
- $k$ is the steepness parameter,
- $b$ is the baseline offset. 

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

The parameters extracted from the sigmoid fit provide a compact description of the excitation profile and can be used to compare samples, group measurements, or perform higher-level statistical analysis. 

In the current workflow, the plateau difference and related fit parameters are among the main quantities retained for interpretation. 

---

### 7.6 Uncertainty Estimation at Each Step

#### Input data

Uncertainty propagation combines information from several stages of the workflow: 

- The uncertainty on peak centroid positions from Gaussian fitting.
- The uncertainty on calibration coefficients.
- The statistical uncertainty on integrated counts.
- The uncertainty associated with charge normalization.
- The uncertainties stored in the processed excitation profiles. 

#### Mathematical transformation

At the calibration stage, the uncertainty on each centroid is extracted from the covariance matrix of the Gaussian fit and used as the weight in the linear energy calibration. 

During ROI integration, the code combines a counting-statistics term and a calibration-related term for the corrected counts $N$. In the current implementation, the statistical term is approximated by: 

$$
\sigma_{\mathrm{stat},N} = \sqrt{N}
$$

and the calibration-related contribution is written as: 

$$
\sigma_{\mathrm{cal},N} = \frac{\varepsilon_{\mathrm{cal}}}{100}\,N
$$

where $\varepsilon_{\mathrm{cal}}$ is the relative calibration error in percent. 

The total uncertainty on $N$ is then combined quadratically: 

$$
\sigma_N = \sqrt{\sigma_{\mathrm{stat},N}^2 + \sigma_{\mathrm{cal},N}^2}
$$

An uncertainty is also associated with the normalized charge term, and the uncertainty on the normalized count $NC=N/Q$ is propagated using the usual relative-error formula: 

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

Uncertainty estimates are essential for judging the quality and comparability of the processed profiles. They also affect the weighting of the sigmoid fit and therefore the stability of the extracted parameters. 

A realistic uncertainty budget is therefore required before any robust statistical comparison between samples can be performed. 
### 7.7 Statistical Comparison Using ANOVA

## 7. Code Architecture (optional)
## 8. Limitations
## 9. References
