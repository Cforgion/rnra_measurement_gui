# RNRA data processing and error management

## Description

This project provides a graphical user interface for processing RNRA (Resonant Nuclear Reaction Analysis) data, from raw acquisition files to final excitation profiles and fitted parameters.  
It automates the conversion of `.mpa` files, energy calibration, ROI integration, optional peak removal and sigmoid fitting, while tracking uncertainties at each step. 

The tool has been developed in the context of thin-layer analysis and depth profiling using the 15N nuclear resonance, with a focus on reproducible data reduction and quantitative uncertainty estimation. 

## Scientific context

The application is designed for experiments based on **Resonant Nuclear Reaction Analysis (RNRA)**, where the measured yield as a function of beam energy is used to infer material composition or depth distributions.   
The data reduction pipeline includes: 

- Extraction of spectra from raw acquisition files and correction for detector dead time. 
- **Energy calibration** by Gaussian peak fitting and linear regression. 
- Construction of excitation profiles via ROI integration and charge normalization. 
- **Optional build-up peak removal** in a given energy interval. 
- **Sigmoid fitting** of the excitation profiles to extract plateau differences and shape parameters. 

Future versions can include statistical comparison between samples using ANOVA and additional hypothesis testing.

## Features

- Batch conversion of `.mpa` acquisition files to structured `.txt` spectra. 
- Automatic extraction of live time and real time, and computation of dead time correction factors. 
- Interactive energy calibration:
  - Peak selection on spectra,
  - Gaussian peak fitting,
  - Linear calibration \(E = aC + b\) with uncertainty estimation. 
- ROI integration and normalization by integrated charge to build excitation profiles. 
- Optional removal of build-up peaks around a given energy and generation of diagnostic plots. 
- Sigmoid fitting of excitation profiles and export of fit parameters and figures. 
- Central configuration via Excel files (paths, file ranges, ADC channels, calibration parameters). 
- Uncertainty estimation at several stages (counts, calibration, normalization). 

## Installation

### Prerequisites

- Python 3.10+
- Recommended environment: virtualenv or conda

Required libraries are listed in `requirements.txt` and include at least:

- `numpy`, `scipy`
- `pandas`
- `matplotlib`
- `tkinter` (usually provided with the Python standard distribution) 

Install the dependencies with:

```bash
pip install -r requirements.txt
```

### Clone the project

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
```

(Replace `<your-username>` and `<your-repo>` with the actual GitHub path.)

## Usage

### Launch the GUI

From the project root:

```bash
python main.py
```

This opens the main window with three main tabs: **Conversion**, **Calibration** and **Processing**. 

### Typical workflow

1. **Prepare the configuration Excel file**  
   - Define sample names, measurement folders, file ranges, ADC channels, and (optionally) initial calibration parameters. 

2. **Convert acquisition files (.mpa → .txt)**  
   - Using the **Conversion** tab, select the configuration file, choose the day/sample root and output folder, then run the conversion. 

3. **Calibrate energy**  
   - In the **Calibration** tab, load representative `.txt` spectra, select peaks, fit Gaussians and run the linear calibration.  
   - Save calibration coefficients back to the configuration file if desired. 

4. **Build excitation profiles**  
   - In the **Processing** tab, load the configuration file, define the ROI in energy and run the loop to integrate counts and normalize by charge. 

5. **Optional: remove build-up peaks**  
   - Still in the **Processing** tab, specify the resonance energy and removal window, then run the peak-removal routine on the loop outputs. 

6. **Fit sigmoid curves and export results**  
   - Apply sigmoid fitting to the raw or cleaned profiles and export the numerical parameters and figures for further analysis. 

## Project structure

The exact structure may evolve, but a typical layout is:

```text
rnra_gui/
├── main.py                 # Entry point for the GUI
├── core/
│   ├── file_io.py          # .mpa → .txt conversion and dead-time extraction
│   ├── calibration.py      # Spectrum loading, Gaussian peak fit, linear calibration
│   ├── Loop_fonction.py    # ROI loop, energy conversion, profile construction
│   ├── Transform_functions.py # Peak removal and sigmoid fitting
│   ├── Traitement_fonctions.py # ROI integration and uncertainty handling
│   └── etallonnage.py      # Additional calibration utilities
├── ui/
│   ├── conversion_tab.py   # Conversion tab (Tkinter)
│   ├── calibration_tab.py  # Calibration tab (Tkinter)
│   └── Loop_tab.py         # Processing / loop tab (Tkinter)
├── temp/                   # Temporary working directory (created at runtime)
├── data/                   # Example input data (optional)
└── results/                # Output profiles, fits and figures
```

[Structure inferred from the current code base: file names and roles may be adapted as the project evolves.] 

## Example outputs

Typical outputs include:

- Text spectra with dead time factor and `(channel, count)` pairs. 
- Excel files with excitation profiles (`Energy keV`, `NC`, `uncertainties`). 
- Cleaned profiles after peak removal, stored in a dedicated subfolder. 
- Sigmoid fit result files (parameters, \(R^2\)) and `.png` figures showing data and fitted curves. 

You can insert example figures here (e.g. an excitation profile and its sigmoid fit).

## Limitations

- The current workflow assumes a predominantly linear detector response in the calibration range. 
- Dead time correction relies on metadata extracted from `.mpa` files; missing or corrupted headers can prevent accurate correction. 
- The uncertainty model is simplified and may not yet include all systematic effects relevant for a full metrological analysis. 
- Peak removal parameters and sigmoid fits should always be validated visually before quantitative interpretation. 

## Author

Cynthia Forgione  
Master in Physics & Data – Université de Namur