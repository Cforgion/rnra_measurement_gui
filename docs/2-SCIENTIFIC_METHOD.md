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
- assumes **five values per group** via a hard-coded `n_per_group = 5`; 
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

> “The current version builds a global uncertainty budget from relative contributions provided by the calibration, excitation-curve and sigmoid-fit stages, and combines them in quadrature.”

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

This section peut rester proche de ta version actuelle, mais en ajustant quelques formulations pour correspondre aux fichiers réellement produits:

- `.txt` spectra with “Dead time factor = …” and two numeric columns; 
- calibration result exports (if implemented in the GUI), including peaks, coefficients and quality metrics; 
- excitation-profile Excel files with columns “numero_fichier”, “N/C”, “incertitudes”, “Energie(keV)”; 
- cleaned profiles suffixed `_cleaned.xlsx` plus PNG plots of removed peaks; 
- sigmoid fit results in `fit_results.xlsx`, per-profile Excel `fits_data/*.xlsx` and PNG images with data + fitted curve; 
- ANOVA diagnostic plots (histogram, boxplot, violin plot, Q‑Q plots). 

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

If you mention “relative RMS error”, it must correspond to the residual RMS computed in your calibration quality script and stored as `rel_rms_pct` in the app state. 

### 6.3 ROI Integration, Normalization and Point Uncertainty

The key difference with ta version initiale est que:

- la ROI est définie en **canaux** (c\_min, c\_max); 
- l’intégration se fait sur les canaux de l’ADC gamma, avec interpolation linéaire si les bornes ne sont pas entières; 
- la charge est prise sur le canal ADCDATA3 et convertie en microcoulombs par un facteur \(10^{-4}\). 

Pour chaque fichier:

1. Read the dead-time factor from the header of the ADC spectrum file.
2. Integrate counts within the channel ROI with linear interpolation at edges when needed.
3. Sum charge counts on the charge file and multiply by \(10^{-4}\) to obtain the integrated charge \(Q\). 
4. Apply dead-time correction:

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

Tu peux conserver ton texte explicatif mais il doit suivre exactement cette structure de propagation, qui est celle réellement utilisée.

### 6.4 Peak Removal and Data Cleaning

`Transform_functions.py` implémente la suppression du pic de “carbon build‑up” et la génération de graphiques: 

- pour chaque fichier Excel contenant une courbe excitation:
  - tri des points par énergie croissante;
  - sélection d’une fenêtre \([E_\text{center} - \text{window}, E_\text{center} + \text{window}]\);
  - détection des pics dans `N/C` dans cette fenêtre (`find_peaks`);
  - sélection du pic le plus proche de \(E_\text{center}\);
  - suppression des points dans \([E_\text{pic} - \text{halfwidth}, E_\text{pic} + \text{halfwidth}]\);
  - sauvegarde du fichier nettoyé et d’une figure montrant données brutes et filtrées. 

Tu peux garder l’idée de “peak removal par fenêtre en énergie” en précisant que la méthode repose sur `find_peaks`, un choix de fenêtre autour de 6385 keV par défaut, et la suppression d’un intervalle fixe autour du pic détecté.

### 6.5 Sigmoid Fitting and Parameter Extraction

`fit_to_profile` dans `Transform_functions.py` prend les fichiers Excel (nettoyés ou non), lit les colonnes “Energie(keV)”, “N/C”, “incertitudes”, nettoie les valeurs non finies, puis: 

- construit un masque pour garder seulement les points valides;
- ordonne les points par énergie si besoin;
- définit un jeu de paramètres initiaux \(p_0 = [L, x_0, k, b]\);
- appelle `curve_fit` avec:
  - modèle sigmoïde \(y(x) = L / (1 + \exp(-k(x - x_0))) + b\);
  - `sigma=y_error`, `absolute_sigma=True`, méthode `dogbox`, bornes appropriées; 
- obtient les paramètres ajustés et la matrice de covariance;
- calcule le plateau effectif `Real_height = L - b`;
- calcule \(R^2\);
- calcule une quantité `Ucc_tot = sqrt(perr[0] + perr[3])` comme mesure d’incertitude globale liée à \(L\) et \(b\); 
- construit un DataFrame de résultats avec:
  - nom du fichier;
  - \(L\), \(b\), \(x_0\), \(k\);
  - `diff_height` (hauteur du plateau);
  - `sigma_tot` (`Ucc_tot`);
  - un champ `group` (issu de `assign_group`), utilisé ensuite pour ANOVA. 
- sauvegarde les courbes (données + fit) dans des Excel séparés et des PNG. 

Le texte doit dire que la contribution “sigmoid” du budget d’incertitude se base sur ces paramètres et sur cette quantité `Ucc_tot`, résumée ensuite en un pourcentage dans l’interface avant d’être passée à `compute_uncertainty_budget`. 

### 6.6 Construction of the Uncertainty Budget

`core/uncertainty.py` ne refait pas la propagation analytique, mais assemble des contributions relatives déjà calculées en amont: 

- `calibration_result` doit contenir soit:
  - un champ `rel_rms_pct` pour la calibration globale; soit
  - un dictionnaire par groupe, chacun avec son `rel_rms_pct`; 
- `excitation_info` est un dictionnaire avec `value_pct` (par exemple une moyenne des \(u(NC)/NC\) en %);
- `sigmoid_info` est un dictionnaire avec `value_pct` (par exemple l’incertitude moyenne sur la hauteur de plateau, en %). 

Pour chaque source, la fonction:

1. convertit `value_pct` en standard uncertainty relative \(u_\text{rel} = \text{value\_pct} / 100\);
2. stocke une ligne avec la source, la valeur, l’incertitude et une sensibilité de 1.0;
3. définit la “contribution” comme \(|u_\text{rel}|\);
4. calcule l’incertitude combinée:

\[
u_c = \sqrt{\sum_i (\text{contribution}_i)^2}
\]

Ce bloc doit remplacer toute phrase laissant penser que le code applique “un modèle complet avec coefficients de sensibilité explicites sur toutes les grandeurs”. Le texte doit dire clairement que:

> “The current implementation of the uncertainty budget combines relative contributions provided by each stage (calibration, excitation profiles, sigmoid fit) as independent standard uncertainties and computes the combined uncertainty as the square root of the sum of squares.” 

### 6.7 Statistical Comparison Using ANOVA

Cette section doit aligner exactement les formules sur celles de `ANOVA.py`, comme détaillé en 2.2. 

Tu peux garder tout l’habillage sur:
- test F;
- hypothèses;
- vérification via Q‑Q plots, histogrammes, boxplots, violin plots;
- recours éventuel à Kruskal–Wallis;

mais il faut préciser que:

- la fonction actuelle **ne calcule pas** Kruskal–Wallis elle‑même (tu peux dire que ceci est une perspective ou reste à implémenter si ce n’est pas encore fait dans le GUI); 
- l’incertitude de type ANOVA est construite avec `n_per_group = 5` fixé en dur et doit donc être utilisée avec prudence pour d’autres tailles d’échantillons. 

---

## 7. Code Architecture

Les parties de cette section qui décrivent `core/calibration.py`, `core/Loop_fonction.py`, `core/Transform_functions.py`, `core/file_io.py`, `core/ANOVA.py` et `core/uncertainty.py` doivent être ajustées comme suit: 

- `core/file_io.py`: conversion `.mpa` → `.txt` avec extraction de dead time; 
- `core/calibration.py`: lecture de spectres, fit gaussien + fond linéaire, régression linéaire pondérée; 
- `core/Loop_fonction.py`: boucle de traitement avec ROI en canaux, utilisation de fichiers Excel de tension/énergie, intégration et normalisation, export Excel; 
- `core/Traitement_fonctions.py`: intégration ROI et calcul d’incertitudes point par point; 
- `core/Transform_functions.py`: nettoyage de pics locaux et fit sigmoïde + extraction de paramètres; 
- `core/uncertainty.py`: agrégation des contributions relatives et calcul d’une incertitude combinée; 
- `core/ANOVA.py`: ANOVA à un facteur, estimation d’\(u_\text{total}\) et \(u_\text{rel}(\%)\), tracés diagnostics. 

Il faut supprimer ou reformuler tout passage qui affirme que `core/uncertainty.py` “calcule un budget complet avec tous les coefficients de sensibilité explicitement dérivés du modèle” : le code actuel suppose que ces contributions ont déjà été numérisées par les étapes précédentes. 

---

## 8. Limitations

Ta section Limitations est globalement bonne; il suffit de l’aligner avec ce que le code fait réellement. Les points importants à garder ou préciser: 

- la calibration suppose un modèle linéaire et des pics bien résolus;
- le dead-time est basé sur les métadonnées `livetime`/`realtime` des `.mpa`;
- l’incertitude sur les profils et sur les fits sigmoïdes n’intègre pas tous les biais possibles (dérive de courant, instabilités, inhomogénéités);
- le budget global combine les contributions comme indépendantes, ce qui n’est pas toujours strictement vrai;
- `n_per_group = 5` dans ANOVA limite la généricité de la méthode de décomposition de variance;
- les fichiers Excel d’entrée doivent correspondre exactement au format attendu.

---

## 9. References

The reference list can remain as in your draft, or be completed, since it is independent from the code. 
