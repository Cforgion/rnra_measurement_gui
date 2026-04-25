"""
Calibration (Étalonnage)
Adapté de etallonnage.py avec sélection interactive de zones
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit  
from scipy.signal import find_peaks
import os


def load_spectrum(file_path):
    """
    Charge un fichier spectre .txt (canal, counts).
    Compatible avec format généré par convert_mpa_folder.
    
    Parameters
    ----------
    file_path : str
        Chemin vers fichier .txt
    
    Returns
    -------
    dict : {
        'success': bool,
        'channels': np.array,
        'counts': np.array,
        'deadtime': float (extrait du header si présent),
        'error': str (si échec)
    }
    """
    
    if not os.path.exists(file_path):
        return {'success': False, 'error': 'Fichier introuvable'}
    
    try:
        # Lire le header pour extraire dead time
        deadtime = 1.0
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            first_line = f.readline()
            if 'Dead time factor' in first_line:
                try:
                    deadtime = float(first_line.split('=')[1].strip())
                except:
                    pass
        
        # Charger les données
        data = []
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#') or not line:
                    continue
                
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        data.append([int(parts[0]), float(parts[1])])
                    except ValueError:
                        continue
        
        if not data:
            return {'success': False, 'error': 'Aucune donnée dans le fichier'}
        
        data = np.array(data)
        channels = data[:, 0].astype(int)
        counts = data[:, 1]
        
        return {
            'success': True,
            'channels': channels,
            'counts': counts,
            'deadtime': deadtime
        }
    
    except Exception as e:
        return {'success': False, 'error': str(e)}


def gaussienne(x, a, x0, sigma,b,c):
    """Fonction gaussienne pour fit."""
    return a * np.exp(-(x - x0)**2 / (2 * sigma**2))+b+c*x


def fit_gaussian_in_zone(channels, counts, center_approx, tolerance):
    """
    Fit gaussien autour d'un pic (TON CODE).
    
    Parameters
    ----------
    channels : np.array
        Canaux
    counts : np.array
        Counts
    center_approx : float
        Position approximative du pic
    tolerance : float
        Tolérance autour du pic
    
    Returns
    -------
    dict : {
        'success': bool,
        'centroid': float,
        'sigma': float,
        'amplitude': float,
        'error_centroid': float,
        'error': str (si échec)
    }
    """
    
    try:
        # Extraire la zone d'intérêt
        mask = (channels >= center_approx - tolerance) & (channels <= center_approx + tolerance)
        x_fit = channels[mask]
        y_fit = counts[mask]
        
        if len(x_fit) == 0:
            return {'success': False, 'error': 'Aucun point dans la zone'}
        
        # Paramètres initiaux
        p0 = [np.max(y_fit), center_approx, np.std(x_fit),0,0]
        
        # Fit gaussien
        popt, pcov = curve_fit(
                    gaussienne, x_fit, y_fit, p0=p0,
                    #bounds=([0, x_fit[0], 0], [np.inf, x_fit[-1], np.inf]),
                    maxfev=8000
                )
        
        A, x0, sigma,b,c = popt
        perr = np.sqrt(np.diag(pcov))
        err_A, err_x0, err_sigma,err_b, err_c = perr
        
        return {
            'success': True,
            'centroid': x0,
            'sigma': sigma,
            'amplitude': A,
            'b':b,
            'c':c,
            'error_centroid': err_x0,
            'error_sigma': err_sigma,
            'error_amplitude': err_A,
            'error_b': err_b,
            'error_c':err_c
        }
    
    except Exception as e:
        return {'success': False, 'error': str(e)}


def calibrate_linear(centroids, energies, errors_centroid):
    """
    Calibration linéaire E = a*C + b avec propagation d'erreurs (TON CODE).
    
    Parameters
    ----------
    centroids : list/array
        Positions des centroides (canaux)
    energies : list/array
        Énergies de référence (keV)
    errors_centroid : list/array
        Erreurs sur les centroides
    
    Returns
    -------
    dict : {
        'success': bool,
        'a': float (pente),
        'b': float (intercept),
        'error_a': float,
        'error_b': float,
        'R2': float,
        'covariance': np.array,
        'error': str (si échec)
    }
    """
    
    try:
        centroids = np.array(centroids)
        energies = np.array(energies)
        errors_centroid = np.array(errors_centroid)
        
        # Poids (1/erreur²)
        weights = 1.0 / errors_centroid**2
        
        # Régression linéaire pondérée
        p, cov = np.polyfit(centroids, energies, 1, w=weights, cov=True)
        a, b = p
        error_a, error_b = np.sqrt(np.diag(cov))
        
        # Calcul R²
        y_fit = a * centroids + b
        ss_res = np.sum((energies - y_fit)**2)
        ss_tot = np.sum((energies - np.mean(energies))**2)
        R2 = 1 - (ss_res / ss_tot)
        
        return {
            'success': True,
            'a': a,
            'b': b,
            'error_a': error_a,
            'error_b': error_b,
            'R2': R2,
            'covariance': cov
        }
    
    except Exception as e:
        return {'success': False, 'error': str(e)}


def auto_calibrate_from_files(file_list, positions_approx, tolerances, energies):
    """
    Calibration automatique sur plusieurs fichiers (TON WORKFLOW).
    
    Parameters
    ----------
    file_list : list of str
        Chemins vers fichiers spectres
    positions_approx : list of float
        Positions approximatives des pics (canaux)
    tolerances : list of float
        Tolérances autour de chaque pic
    energies : list of float
        Énergies de référence (keV)
    
    Returns
    -------
    dict : résultats de la calibration
    """
    
    all_centroids = []
    all_errors = []
    all_energies = []
    
    for file_path in file_list:
        # Charger spectre
        spectrum = load_spectrum(file_path)
        if not spectrum['success']:
            return {'success': False, 'error': f"Erreur fichier {file_path}: {spectrum['error']}"}
        
        channels = spectrum['channels']
        counts = spectrum['counts']
        
        # Fit gaussien sur chaque position
        for pos, tol, energy in zip(positions_approx, tolerances, energies):
            result = fit_gaussian_in_zone(channels, counts, pos, tol)
            
            if result['success']:
                all_centroids.append(result['centroid'])
                all_errors.append(result['error_centroid'])
                all_energies.append(energy)
    
    if len(all_centroids) < 2:
        return {'success': False, 'error': 'Pas assez de pics trouvés (minimum 2)'}
    
    # Calibration linéaire
    calib = calibrate_linear(all_centroids, all_energies, all_errors)
    
    if calib['success']:
        calib['centroids'] = all_centroids
        calib['energies'] = all_energies
        calib['errors_centroid'] = all_errors
    
    return calib


def interactive_zone_selection(file_path, callback=None):
    """
    Sélection interactive de zones sur un spectre.
    Affiche le spectre et permet de cliquer pour sélectionner des zones.
    
    Parameters
    ----------
    file_path : str
        Chemin vers fichier spectre
    callback : callable, optional
        Fonction appelée quand une zone est sélectionnée
        callback(center, width)
    
    Returns
    -------
    list : Liste de tuples (center, width) pour chaque zone sélectionnée
    """
    
    # Cette fonction sera utilisée par le GUI avec matplotlib embedded
    # Pour l'instant, on retourne juste la structure
    
    spectrum = load_spectrum(file_path)
    if not spectrum['success']:
        return []
    
    # Le GUI implémentera l'interactivité avec SpanSelector ou clicks
    return {
        'channels': spectrum['channels'],
        'counts': spectrum['counts'],
        'deadtime': spectrum['deadtime']
    }
