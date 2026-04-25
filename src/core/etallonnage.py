import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import numpy as np
from scipy.optimize import curve_fit
from scipy.signal import find_peaks,peak_widths
import os
plot=True
def ouverture_fichier(path):
  

    # Vérifier que le fichier existe
    if not os.path.exists(path):
        raise FileNotFoundError(f"Le fichier n'existe pas : {path}")

    colonne1 = []
    colonne2 = []

    try:
        # Ouvrir le fichier avec gestion des caractères spéciaux
        with open(path, 'r', encoding='utf-8', errors='ignore') as fichier:
            for ligne in fichier:
                valeurs = ligne.strip().split()
                if len(valeurs) < 2:
                    continue  # ignorer les lignes vides ou incomplètes
                try:
                    colonne1.append(int(valeurs[0]))
                    colonne2.append(float(valeurs[1]))
                except ValueError:
                    # ignorer les lignes non numériques
                    continue
    except OSError as e:
        raise OSError(f"Erreur lors de la lecture du fichier '{path}' : {e}")

    return colonne1, colonne2

def gaussienne(x, a, x0, sigma): 
    ''' Juste la fonction gaussienne'''
    return a * np.exp(-(x - x0)**2 / (2 * sigma**2))

def conversion(x,a,b):
    En=(x*a)+b
    return En

def fit_pic_dans_tolerance(x, y, pic_cible, tol, m=1, p=0, plot=True):
    """
    Fit gaussien sur les points autour d'un pic connu
    x, y : données
    pic_cible : position approximative du pic
    tol : tolérance autour de pic_cible
    m, p : coefficients pour conversion (optionnel)
    """
    # Extraire les points dans la tolérance
    masque = (x >= pic_cible - tol) & (x <= pic_cible + tol)
    x_fit = x[masque]
    y_fit = y[masque]

    if len(x_fit) == 0:
        print(f"Aucun point pour le pic autour de {pic_cible} ± {tol}")
        return None

    # Fit gaussien
    popt, pcov = curve_fit(
    gaussienne, x_fit, y_fit,
    p0=[max(y_fit), pic_cible, np.std(x_fit)],
    bounds=([0, x_fit[0], 0], [np.inf, x_fit[-1], np.inf]),
    maxfev=8000
)
    A, xc0, sigma = popt
    perr =np.sqrt( (np.diag(pcov)))
    print(perr)
    err_A, err_xc0, err_sigma = perr

    print(f"Centroid = {xc0:.2f} ± {err_xc0:.2f}")
    print(f"Amplitude = {A:.2f} ± {err_A:.2f}")
    print(f"Sigma = {sigma:.2f} ± {err_sigma:.2f}")
    # Conversion éventuelle
    

    # Affichage
    if plot:
        plt.figure()
        #plt.xlim(1200,1900)
        plt.plot(x, (y), 'b', label="Signal")
        plt.plot(x_fit,(gaussienne(x_fit, *popt)), 'r', label=f'Centroid = {xc0:.2f}, sigma = {sigma:.2f}')
        plt.axvline(x=xc0, color='green', linestyle='--', label='Centroïde')
        plt.legend()
        plt.show()

    return xc0, sigma, A, err_xc0

def centroid_find (positions_connues, tolerances,x0,y0):
    x0 = np.array(x0)
    y0 = np.array(y0)

    # Détection de tous les pics
    indice_pics, _ = find_peaks(y0, height = 400)
    cent=[]
    err_cent =[]
    for cible, tol in zip(positions_connues, tolerances):
        xc, sigma, A,errxc0 = fit_pic_dans_tolerance(x0, y0, cible, tol)
        if xc is not None:
            cent.append(xc)
            err_cent.append(errxc0)
            print(f"✅ Pic autour de {cible} : centroïde = {xc:.2f}, sigma = {sigma:.2f}, amplitude = {A:.2f}")
    return cent , err_cent

def etalonnage_avec_erreur_et_R2(x_mesure, y_theorique, delta_x, x_convert):
    """
    x_mesure : positions mesurées (centroides)
    y_theorique : valeurs théoriques (énergies)
    delta_x : erreurs sur les positions mesurées
    x_convert : points à convertir

    Retourne :
    a, b : coefficients de la régression linéaire y = a*x + b
    err_a, err_b : erreurs sur a et b
    R2 : coefficient de détermination
    y_convert : valeurs converties pour x_convert
    """
    # Conversion en array
    x_mesure = np.array(x_mesure)
    y_theorique = np.array(y_theorique)
    delta_x = np.array(delta_x)
    x_convert = np.array(x_convert)
    
    # Poids = 1 / erreur²
    w = 1 / delta_x**2

    # Régression linéaire pondérée
    p, cov = np.polyfit(x_mesure, y_theorique, 1, cov=True)  # p[0]=a, p[1]=b
    a, b = p
    err_a, err_b = np.sqrt(np.diag(cov))
    
    # Conversion des valeurs
    y_convert = a*x_convert + b
    
    # Calcul du R²
    y_fit = a*x_mesure + b
    ss_res = np.sum((y_theorique - y_fit)**2)
    ss_tot = np.sum((y_theorique - np.mean(y_theorique))**2)
    R2 = 1 - ss_res/ss_tot
    
    return a, b, R2, y_convert, cov

def deltaE_global_from_polyfit(p, cov, a_coef, x_points, sigma_x=None):
    """
    p, cov : résultats de np.polyfit(x_mesure, y_theorique, 1, w=w, cov=True)
             p[0]=a, p[1]=b ; cov is 2x2 covariance matrix for [a,b]
    a_coef : same as p[0] (slope)
    x_points : array of x values (channels) on which to evaluate DeltaE
    sigma_x : array or scalar of sigma(x) (uncertainty on channel positions).
              If None, sigma_x assumed zero.
    Returns a dict with:
      - deltaE_per_x : array ΔE(x)
      - deltaE_rms : RMS of ΔE(x)
      - deltaE_max : maximum ΔE(x)
      - rel_rms_pct : RMS relative error in percent (RMS(ΔE/E) * 100)
      - rel_max_pct : maximum relative error percent
    """
    # covariance info
    var_a = cov[0,0]
    var_b = cov[1,1]
    cov_ab = cov[0,1]

    x = np.array(x_points, dtype=float)
    if sigma_x is None:
        sigma_x = np.zeros_like(x)
    else:
        sigma_x = np.array(sigma_x, dtype=float)
        if sigma_x.size == 1:
            sigma_x = np.full_like(x, float(sigma_x))
    
    # variance for each x
    varE = (x**2) * var_a + var_b + 2.0 * x * cov_ab + (a_coef**2) * (sigma_x**2)
    # numerical safety: varE must be >= 0
    varE = np.maximum(varE, 0.0)
    deltaE = np.sqrt(varE)

    # energies
    E = a_coef * x + p[1]

    # metrics
    deltaE_rms = np.sqrt(np.mean(deltaE**2))
    deltaE_max = np.max(deltaE)

    # relative (avoid division by zero)
    with np.errstate(divide='ignore', invalid='ignore'):
        rel = np.abs(deltaE / E)
        rel = np.where(np.isfinite(rel), rel, 0.0)

    rel_rms_pct = np.sqrt(np.mean(rel**2)) * 100.0
    rel_max_pct = np.max(rel) * 100.0

    return {
        "x": x,
        "E": E,
        "deltaE_per_x": deltaE,
        "deltaE_rms": deltaE_rms,
        "deltaE_max": deltaE_max,
        "rel_rms_pct": rel_rms_pct,
        "rel_max_pct": rel_max_pct,
        "var_a": var_a,
        "var_b": var_b,
        "cov_ab": cov_ab
    }

def calibration_all(file_list, positions_connues_0, positions_connues_2, list_tolerances):
    """
    Perform automatic calibration for multiple data files (ADC0 or ADC2).

    Parameters
    ----------
    file_list : list of str
        Paths to data files.
    positions_connues_0 : list of float
        Approximate peak positions for ADC0.
    positions_connues_2 : list of float
        Approximate peak positions for ADC2.
    list_tolerances : list of float
        Tolerances around each peak position.

    Returns
    -------
    a, b : float
        Calibration coefficients (E = a*x + b)
    delta_E : dict
        Global energy error metrics (RMS, max, etc.)
    energie_convert : list of float
        Canal convert to energie 
    """
    centroid = []
    error_centroid = []

    for i, file in enumerate(file_list):
        x, y = ouverture_fichier(file)

        # Détection du type de fichier (ADC0 ou ADC2)
        if "ADC0" in file:
            positions_connues = positions_connues_0
            adc_type = "ADC0"
        elif "ADC2" in file:
            positions_connues = positions_connues_2
            adc_type = "ADC2"
        else:
            raise ValueError(f"Impossible de déterminer le type ADC dans le nom du fichier : {file}")

        # Sélection des positions et tolérances selon le fichier
        if i == 0:
            pos = positions_connues[:3]  # 3 premiers pics
            tol = list_tolerances[:3]
            Energies_used = Energie[:3]
        elif i == 1:
            pos = [positions_connues[-1]]  # dernier pic uniquement
            tol = [list_tolerances[-1]]
            Energies_used = [Energie[-1]]
        else:
            raise ValueError("Seulement deux fichiers sont attendus (1er et 2e).")

        # Recherche des centroides
        cent, error = centroid_find(pos, tol, x, y)
        centroid.extend(cent)
        error_centroid.extend(error)

        # Affichage d'informations utiles
        print(f"\n📄 Fichier : {os.path.basename(file)} ({adc_type})")
        print(f"  → Positions utilisées : {pos}")
        print(f"  → Tolérances utilisées : {tol}")
        print(f"  → Energies associées   : {Energies_used}")

    # Calibration globale
    print (centroid , Energie)
    a, b, r_squared, energie_convert, covariance_matrix = etalonnage_avec_erreur_et_R2(
        centroid, Energie, error_centroid, x
    )
    
    print(f"\n🔧 Résultats de la calibration :")
    print(f"  slope = {a:.5f}, intercept = {b:.5f}")
    delta_E = deltaE_global_from_polyfit(p=[a, b], cov=covariance_matrix, a_coef=a, x_points=centroid)
    print(f"  → Coefficient de détermination (R²): {r_squared:.5f}")
    print(f"  → RMS relative calibration error: {delta_E['rel_rms_pct']:.3f} %")

    return a, b, delta_E, energie_convert


# --- Exemple d’utilisation ---
Energie = [661.65, 1173.23, 1332.47, 4438]
positions_connues_2 = [210, 370, 420, 1380]   # ADC2
positions_connues_0 = [230, 400, 450, 1500]   # ADC0
tolerances = [20, 20, 20, 40]

