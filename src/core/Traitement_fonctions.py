import os
import numpy as np
import pandas as pd
import math

# regression linéaire pour traiter les données avec une nouvelle ROI (appelé dans boucle)
def reg_lin(x_a, x_b, y_a, y_b, x_voulu):
    a = (y_a - y_b) / (x_a - x_b)
    return a * (x_voulu - x_a) + y_a


def coups_normal_pour_un_fichier(path1, path2, ROI_min, ROI_max, err_et):
    path1 = path1.replace("\\", "/")
    path2 = path2.replace("\\", "/")

    if not os.path.exists(path1) or not os.path.exists(path2):
        # print(f"One of the files {path1} or {path2} does not exist.")
        return [None, None]

    try:
        # Lire la première ligne du fichier pour récupérer le dead time factor
        with open(path1, 'r') as f:
            first_line1 = f.readline().strip()
            if first_line1.startswith('#'):
                first_line1 = first_line1[1:].strip()  # enlever le '#'
            # Extraction du facteur numérique
            parts = first_line1.split('=')
            if len(parts) > 1:
                dead_time_factor1 = float(parts[1].strip())
            else:
                dead_time_factor1 = None  # ou 0 si tu veux une valeur par défaut
        #print (dead_time_factor1)
        with open(path2, 'r') as f:
            first_line2 = f.readline().strip()
            if first_line2.startswith('#'):
                first_line2 = first_line2[1:].strip()
            parts = first_line2.split('=')
            if len(parts) > 1:
                dead_time_factor2 = float(parts[1].strip())
            else:
                dead_time_factor2 = None
        data1 = pd.read_csv(
            path1,
            sep=r"\s+",
            header=None,
            names=["x1", "y1"],
            dtype={"x1": np.float64, "y1": np.float64},
            comment='#'
        )
        data2 = pd.read_csv(
            path2,
            sep=r"\s+",
            header=None,
            names=["x2", "y2"],
            dtype={"x2": np.float64, "y2": np.float64},
            comment='#'
        )
    except Exception as e:
        print(f"Error reading files: {e}")
        return [None, None]

    # Print the first few rows to ensure data is read correctly
    # print(f"First few rows of {path2}:\n", data2.head())

    # Valeurs entières
    x_min_lower = math.floor(ROI_min)
    x_min_upper = math.ceil(ROI_min)
    x_max_lower = math.floor(ROI_max)
    x_max_upper = math.ceil(ROI_max)

    # Sélectionner les colonnes
    X = data1["x1"].astype(np.float64)
    Y = data1["y1"].astype(np.float64)

    if x_min_lower == x_min_upper:
        y_roi_min = Y.iloc[x_min_lower]
    # in the case the channel is not an integer, then we make a linear regression in order to reach out the value corresponding to the non-integer channel
    else:
        y_roi_min = reg_lin(
            x_min_lower, x_min_upper, Y.iloc[x_min_lower], Y.iloc[x_min_upper], ROI_min
        )

    if x_max_lower == x_max_upper:
        y_roi_max = Y.iloc[x_max_lower]
    # in the case the channel is not an integer, then we make a linear regression in order to reach out the value corresponding to the non-integer channel
    else:
        y_roi_max = reg_lin(
            x_max_lower, x_max_upper, Y.iloc[x_max_lower], Y.iloc[x_max_upper], ROI_max
        )

    # print("Valeur y pour le canal min ", ROI_min, ":", y_roi_min)
    # print("Valeur y pour le canal max ", ROI_max, ":", y_roi_max)

    # Filtrer les lignes où la colonne 1 est comprise entre la valeur de début et la valeur de fin
    donnees_filtrees = data1[
        (data1["x1"] >= x_min_upper) & (data1["x1"] <= x_max_lower)
    ]

    # Somme des valeurs de ACD0
    somme_y1 = (
        np.sum(donnees_filtrees["y1"].values, dtype=np.float64) + y_roi_min + y_roi_max
    )
   
    # Somme des valeurs de ACD3
    somme_y2 = data2["y2"].sum()
    
    # correction dead time
    N = somme_y1 * dead_time_factor1

    # Charge intégrée (µC)
    Q = somme_y2 * 0.0001

    # valeur normalisée
    coups = N / Q

    # --- Incertitudes ---

    # statistique sur N (Poisson)
    sigma_stat_N = np.sqrt(N)

    # incertitude due à l’étalonnage/ROI (err_et → sur N)
    sigma_cal_N = (err_et/100)*N

    # incertitude totale sur N
    sigma_N = np.sqrt(sigma_stat_N**2 + sigma_cal_N**2)

    # incertitude sur Q (rel_err_charge est la fraction relative)
    sigma_Q = np.sqrt(Q)*0.0001

    # propagation pour R = N / Q
    if N > 0 and Q > 0:
        incertitude = coups*np.sqrt((sigma_N/N)**2 + (sigma_Q/Q)**2)
    else:
        incertitude = np.nan

    return [coups, incertitude, somme_y2]

