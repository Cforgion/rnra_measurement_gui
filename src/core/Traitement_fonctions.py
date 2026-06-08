import os
import numpy as np
import pandas as pd
import math

def reg_lin(x_a, x_b, y_a, y_b, x_voulu):
    a = (y_a - y_b) / (x_a - x_b)
    return a * (x_voulu - x_a) + y_a


def somme_dans_roi(data1, ROI_min, ROI_max):
    Y = data1["y1"].astype(np.float64)

    x_min_lower = math.floor(ROI_min)
    x_min_upper = math.ceil(ROI_min)
    x_max_lower = math.floor(ROI_max)
    x_max_upper = math.ceil(ROI_max)

    if x_min_lower == x_min_upper:
        y_roi_min = Y.iloc[x_min_lower]
    else:
        y_roi_min = reg_lin(
            x_min_lower, x_min_upper,
            Y.iloc[x_min_lower], Y.iloc[x_min_upper],
            ROI_min
        )

    if x_max_lower == x_max_upper:
        y_roi_max = Y.iloc[x_max_lower]
    else:
        y_roi_max = reg_lin(
            x_max_lower, x_max_upper,
            Y.iloc[x_max_lower], Y.iloc[x_max_upper],
            ROI_max
        )

    donnees_filtrees = data1[
        (data1["x1"] >= x_min_upper) & (data1["x1"] <= x_max_lower)
    ]

    somme_y = (
        np.sum(donnees_filtrees["y1"].values, dtype=np.float64)
        + y_roi_min + y_roi_max
    )

    return somme_y


def coups_normal_pour_un_fichier(path1, path2, ROI_min, ROI_max, err_et):
    path1 = path1.replace("\\", "/")
    path2 = path2.replace("\\", "/")

    if not os.path.exists(path1) or not os.path.exists(path2):
        return [None, None, None]

    try:
        with open(path1, 'r') as f:
            first_line1 = f.readline().strip()
            if first_line1.startswith('#'):
                first_line1 = first_line1[1:].strip()
            parts = first_line1.split('=')
            dead_time_factor1 = float(parts[1].strip()) if len(parts) > 1 else 1.0

        with open(path2, 'r') as f:
            first_line2 = f.readline().strip()
            if first_line2.startswith('#'):
                first_line2 = first_line2[1:].strip()
            parts = first_line2.split('=')
            dead_time_factor2 = float(parts[1].strip()) if len(parts) > 1 else 1.0

        data1 = pd.read_csv(
            path1,
            sep=r"\s+",
            header=None,
            names=["x1", "y1"],
            dtype={"x1": np.float64, "y1": np.float64},
            comment="#"
        )

        data2 = pd.read_csv(
            path2,
            sep=r"\s+",
            header=None,
            names=["x2", "y2"],
            dtype={"x2": np.float64, "y2": np.float64},
            comment="#"
        )

    except Exception as e:
        print(f"Error reading files: {e}")
        return [None, None, None]

    # ROI nominale
    somme_y1_0 = somme_dans_roi(data1, ROI_min, ROI_max)

    # variation de ROI liée à l'étalonnage
    delta_e = (err_et / 100.0) * (ROI_max - ROI_min)

    # ROI élargie
    somme_y1_plus = somme_dans_roi(data1, ROI_min - delta_e, ROI_max + delta_e)

    # ROI rétrécie
    roi_min_moins = ROI_min + delta_e
    roi_max_moins = ROI_max - delta_e

    if roi_min_moins < roi_max_moins:
        somme_y1_minus = somme_dans_roi(data1, roi_min_moins, roi_max_moins)
    else:
        somme_y1_minus = somme_y1_0

    # charge
    somme_y2 = data2["y2"].sum()

    # correction temps mort
    N0 = somme_y1_0 * dead_time_factor1
    Nplus = somme_y1_plus * dead_time_factor1
    Nminus = somme_y1_minus * dead_time_factor1
    
    Q = somme_y2 * 0.0001

    coups = N0 / Q if Q > 0 else np.nan

    # statistique sur N
    sigma_stat_N = np.sqrt(N0)

    # contribution étalonnage estimée par variation des bornes
    sigma_cal_N = 0.5 * abs(Nplus - Nminus)

    # statistique sur Q

    # total sur N
    sigma_N = np.sqrt(sigma_stat_N**2 + sigma_cal_N**2)
    sigma_Q = 0.0133 
    # propagation sur R = N/Q
    if N0 > 0 and Q > 0:
        incertitude = coups * np.sqrt((sigma_N / N0)**2+(sigma_Q/ Q)**2)
    else:
        incertitude = np.nan

    print(sigma_N)

    return [coups, incertitude, somme_y2]