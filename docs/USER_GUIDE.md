# USER GUIDE - RNRA data processing and error management

## Table of Contents

- [1. Introduction](#1-introduction)
- [2. Scientific Background](#2-scientific-background)
- [3. Installation](#3-installation)
- [4. Interface Description](#4-interface-description)
- [5. Processing Workflow](#5-processing-workflow)
- [6. Output Files](#6-output-files)
- [7. Methodological Details](#7-methodological-details)
- [8. Code Architecture](#8-Code-Architecture)
- [9. Limitations](#9-limitations)
- [10. References](#10-references)

## 1. Introduction
This tool performs the analysis of hydrogen profiling measurements from the raw MPA file to the excitation curve and final sigmoid fit. In addition to the statistical evaluation of repeatability through ANOVA, the workflow includes the propagation of measurement uncertainty at each processing stage, so that the final result reflects not only random variability but also contributions arising from calibration, dead-time correction, and nonlinear sigmoid fitting.
The uncertainty evaluation is not limited to ANOVA. ANOVA is used to estimate the random component associated with repeated measurements, whereas the full uncertainty budget is obtained by propagating all relevant contributions through the measurement model, including calibration uncertainty, dead-time correction uncertainty, and fit-parameter uncertainty from the sigmoid adjustment. <span style="color:red;">A verifier que c'est bien ce qui est fait ainsi 2 en un budget + ANOVA , c'est ce que je rajoute par rapport a l'année derniere</span>

## 2. Scientific principle
 <span style="color:red;"> AJOUTER aussi une section sur le budget d'incertitude.</span>
### 2.1 Analyse par Réaction Nucléaire Résonante (RNRA)

La Réaction Nucléaire Résonante (RNRA) est une technique d'analyse qui permet de déterminer le profil de concentration d'un élément dans un matériau en fonction de la profondeur. Son principe repose sur l'exploitation d'une réaction nucléaire présentant une résonance à une énergie bien définie : lorsque l'énergie des ions incidents coïncide avec celle de la résonance, la section efficace de réaction atteint un maximum. Il devient ainsi possible de sonder sélectivement une profondeur précise, en exploitant la relation entre l'énergie du faisceau incident et la perte d'énergie des ions dans la matière. La largeur de la résonance, qui définit la plage d'énergies autour de cette valeur pour laquelle la réaction est significative, conditionne directement la résolution en profondeur : plus elle est étroite, plus la précision spatiale est élevée.

Dans notre cas, l'objectif est le profilage de l'hydrogène. Pour ce faire, nous utilisons une pastille de TiH₂, choisie pour sa teneur élevée en hydrogène, son homogénéité et sa stabilité sous irradiation. Les mesures reposent sur les interactions entre des ions ¹⁵N³⁺ et des noyaux ¹H, via la réaction nucléaire suivante :

**¹⁵N(¹H, αγ)¹²C**

Cette réaction présente une forte résonance à 6,385 MeV (largeur 1,8 keV, σ_max = 1650 mb, voir figure 1). À cette énergie, la probabilité d'interaction est maximale, ce qui confère à la méthode une très bonne sélectivité. La réaction se déroule en deux étapes :

1. L'hydrogène interagit avec l'azote 15 pour former un noyau composé transitoire d'oxygène 16 excité.
2. Ce noyau se désintègre en émettant une particule alpha et un noyau de carbone 12 excité, qui retourne ensuite à son état fondamental en émettant un gamma de 4,43 MeV, lequel est détecté pour quantifier la réaction.

Lors de leur pénétration dans la matière, les ions ¹⁵N³⁺ perdent progressivement de l'énergie selon le pouvoir d'arrêt S = dE/dx, qui dépend à la fois du matériau traversé et de la nature des ions. En faisant varier l'énergie du faisceau incident, il est possible d'associer chaque valeur d'énergie à une profondeur précise dans l'échantillon, permettant ainsi de balayer différentes profondeurs d'analyse (voir figure 2). Pour des énergies incidentes légèrement inférieures à la résonance, peu de gammas sont détectés. Au fur et à mesure que l'énergie s'approche de la résonance, le nombre de gammas émis augmente rapidement, jusqu'à atteindre un plateau où le signal se stabilise. La courbe obtenue présente ainsi une forme sigmoïdale (voir figure 4b), caractéristique de la progression du sondage en énergie.

Toutefois, cette courbe d'excitation ne représente pas directement le profil de concentration. Une étape de déconvolution est nécessaire pour corriger les effets liés à la perte d'énergie du faisceau lors de sa pénétration dans l'échantillon. Cette déconvolution permet de convertir la variation du signal gamma en un profil précis de distribution de l'hydrogène en fonction de la profondeur. À partir des courbes d'excitation déconvoluées, il est ainsi possible d'extraire quantitativement le profil de concentration en hydrogène de l'échantillon analysé (voir le mémoire de Louis Dupont pour une description détaillée de cette démarche).

Le nombre d'événements détectés est donné par [11, 12] :

**N = Q_c · Ω · σ(E_r) · N_t**

où :
- **Q_c** : charge intégrée, c'est-à-dire la quantité totale de charge portée par les ions ayant frappé la cible. Elle est obtenue en intégrant le courant du faisceau sur la durée d'irradiation et s'exprime en microcoulombs (µC). Divisée par la charge de l'ion incident, elle donne directement le nombre total de particules envoyées sur l'échantillon ; il s'agit d'une grandeur essentielle pour normaliser le signal détecté.
- **Ω** : angle solide de détection du détecteur (sr).
- **σ(E_r)** : section efficace à l'énergie de résonance (cm²).
- **N_t** : densité surfacique d'atomes cibles (at/cm²).

La RNRA est particulièrement bien adaptée à l'analyse d'éléments légers comme l'hydrogène. Ses principaux atouts sont :
- une **excellente sensibilité** (jusqu'à 10 ppm atomique), permise par la résonance et sa faible largeur ;
- une **résolution en profondeur optimale**, directement liée à l'étroitesse de la résonance ;
- une **sélectivité élevée**, le gamma émis à 4,43 MeV étant peu sujet aux interférences (la radioactivité naturelle est en général limitée à environ 3 MeV) ;
- un **caractère non destructif**, sous réserve de limiter la diffusion de l'hydrogène induite par le faisceau lors de l'analyse.

En revanche, la méthode requiert :
- un accélérateur de particules ;
- la prise en compte des effets de matrice, c'est-à-dire l'ensemble des phénomènes liés à la composition et à la structure de l'échantillon susceptibles d'affecter la précision de la mesure.

---

### 2.2 Analyse de variance (ANOVA)

Afin de quantifier la reproductibilité des mesures et d'estimer l'incertitude aléatoire associée, un test ANOVA (ANalysis Of VAriance) est mis en œuvre. Ce test statistique permet de comparer les moyennes de plusieurs groupes — dans notre cas, les moyennes des mesures effectuées lors de différentes journées d'acquisition — afin de déterminer si des différences significatives existent entre eux. Le jeu de données considéré comprend cinq mesures par journée, réalisées sur huit journées distinctes.

Le test ANOVA repose sur un système d'hypothèses [14] :
- **H₀** (hypothèse nulle) : toutes les moyennes de groupe sont égales, c'est-à-dire qu'il n'existe pas de différence significative entre les journées.
- **H₁** (hypothèse alternative) : au moins une moyenne de groupe diffère des autres.

La décision d'accepter ou de rejeter H₀ s'appuie sur la **p-valeur** fournie par le test. Cette quantité représente la probabilité de rejeter à tort l'hypothèse nulle lorsqu'elle est vraie (erreur de type I). Par exemple, une p-valeur de 0,23 signifie que, si l'on rejette H₀, on encourt un risque de 23 % de conclure à tort à l'existence d'une différence entre les groupes.

Le test ANOVA peut également être interprété comme une régression linéaire appliquée à des variables catégorielles, selon le modèle [15] :

**ŷ = Σ βᵢGᵢ + ε**

où :
- **ŷ** est la valeur estimée par le modèle,
- **Gᵢ** indique l'appartenance d'une observation au groupe *i*,
- **βᵢ** est la moyenne estimée du groupe *i*,
- **ε** est le terme d'erreur (résidu).

Les résidus sont définis comme l'écart entre la valeur observée et la valeur estimée :

**res = y_réel − ŷ**

Avant d'appliquer le test ANOVA, trois hypothèses fondamentales doivent être vérifiées pour en garantir la validité :
- **Indépendance des mesures** : généralement assurée par la rigueur du protocole expérimental.
- **Normalité des résidus** : vérifiée à l'aide d'outils graphiques tels que le diagramme quantile-quantile (Q-Q plot)¹ (voir figure 6) ou un histogramme, ou encore via des tests formels comme le test de Shapiro-Wilk [16].
- **Homogénéité des variances** entre les groupes : évaluée graphiquement via un violin plot (voir figure 7) ou par des tests statistiques tels que le test de Levene [17].

Si l'une de ces conditions n'est pas satisfaite, le test ANOVA classique ne peut être appliqué, car ces hypothèses permettent de supposer que la statistique de test suit une loi de Fisher-Snedecor [18].

Lorsque les hypothèses sont respectées, la statistique de test F suit une loi de Fisher-Snedecor à k−1 et k(n−1) degrés de liberté, où k est le nombre de groupes et n le nombre de mesures par groupe (voir figure 8). Cette loi permet de comparer la variance intergroupe à la variance intragroupe : plus la valeur de F est élevée, plus les différences entre groupes sont significatives. Si F dépasse la valeur critique F_critique, déterminée en fonction du niveau de signification α et des degrés de liberté, l'hypothèse nulle est rejetée.

Si les hypothèses de normalité ou d'homogénéité des variances ne sont pas respectées, il convient de recourir à un test non paramétrique, tel que le test de **Kruskal-Wallis** [19]. Ce test est fondé sur le classement des observations plutôt que sur leurs valeurs numériques, et ne suppose pas que les données suivent une loi de Fisher. Il fournit également une p-valeur, interprétable de la même manière.

Le test ANOVA permet également d'estimer l'**incertitude de type aléatoire** associée aux mesures, une approche déjà appliquée avec succès dans le cadre d'autres mesures par faisceau d'ions [20, 21]. Les erreurs systématiques ne sont pas prises en compte par ce modèle. Les variances intra- et intergroupes permettent de calculer les **Mean Squares (MS)**, ou moyennes des carrés :

**MS_inter = SS_inter / (k − 1)**

**MS_intra = SS_intra / (k(n − 1))**

À partir de ces grandeurs, deux composantes d'incertitude sont déduites :

- **Incertitude intergroupe (u_inter)** :

  u_inter = √((MS_inter − MS_intra) / n)

  Si MS_inter < MS_intra, la variance intergroupe est négligeable devant la variance intragroupe, ce qui confirme H₀.

- **Incertitude intragroupe (u_intra)** :

  u_intra = √MS_intra

L'**incertitude combinée** sur les mesures est alors :

**u_c = √(u²_inter + u²_intra)**

Et l'**incertitude relative** (exprimée en %) :

**u_rel = (u_c / ȳ) × 100**

où ȳ est la moyenne générale des mesures.

---

¹ Un quantile est une valeur divisant l'ensemble des données en intervalles contenant le même nombre d'observations. Les quantiles les plus courants sont les quartiles et la médiane.

---

### 2.3 Budget d'incertitude

*[Section à compléter]*

Le budget d'incertitude vise à recenser et à quantifier l'ensemble des sources d'incertitude contribuant à l'incertitude totale sur le résultat de mesure. Conformément au GUM (Guide to the Expression of Uncertainty in Measurement) [réf.], les incertitudes sont classées en deux catégories :

- **Type A** : évaluées par des méthodes statistiques à partir d'une série de mesures répétées (par exemple, via l'ANOVA décrite à la section 2.4).
- **Type B** : évaluées par d'autres moyens, tels que des données de calibration, des spécifications constructeur ou des estimations expertes.

Les principales sources d'incertitude identifiées dans notre protocole sont les suivantes :

| Source d'incertitude | Type | Valeur estimée | Distribution |
|---|---|---|---|
| Statistique de comptage (ROI) | A | *à compléter* | Poisson |
| Reproductibilité inter-journées | A | *à compléter* (via ANOVA) | Normale |
| Calibration en énergie | B | *à compléter* | Normale |
| Normalisation par la charge Q_c | B | *à compléter* | Normale |
| Correction du temps mort | B | *à compléter* | Rectangulaire |
| ... | ... | ... | ... |

L'incertitude combinée totale est obtenue par composition quadratique des contributions individuelles, en supposant leur indépendance :

**u_c,total = √(Σ uᵢ²)**

*[Développer ici chaque contribution, son mode d'estimation et sa valeur numérique.]*

## 3. detailed installation
Procedure etape par etape

Here is a cleaned‑up, up‑to‑date English markdown draft for the key “user guide” parts, aligned with your current GUI (Conversion / Calibration / Processing). You can paste these blocks into `USER_GUIDE.md` and adapt the numbering if needed. 

***

## 4. Interface Description

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

5. **Check for errors** 
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

5. **Repeat for all calibration peaks** 
   - Repeat steps 2–4 for each reference line you want to include in the calibration.  
   - Once at least two peaks are defined, the **Run calibration** button is enabled.

6. **Run the linear calibration** 
   - Click **Run calibration**.  
   - The software performs a (weighted) linear regression $E = a \cdot C + b$ using the centroids and their uncertainties.  
   - It computes:  
     - Slope $a$ and intercept $b$,  
     - Uncertainties on $a$ and $b$,  
     - Coefficient of determination $R^2$,  
     - Global RMS error and relative RMS (in %).  
   - A summary string is displayed in the calibration result label and in the text area.

7. **Update the configuration file (if applicable)** 
   - If the application is used together with the Conversion and Processing tabs, and a global configuration Excel file is defined, the calibration results can be written back into the configuration file for the current group/day.  
   - The corresponding columns (e.g. `slope`, `intercept`, `errorcalib`) are updated for the matching rows, so the processing loop can use them automatically.

8. **Export calibration results (optional)** 
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

## 5. Processing Workflow (Overview)

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

## 6. Output Files (Overview)

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




## 7. Methodological Details

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

## 8. Code Architecture (optional)
## 9. Limitations
## 10. References
