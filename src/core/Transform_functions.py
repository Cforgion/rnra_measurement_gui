import os
from xml.parsers.expat import errors
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from scipy.optimize import curve_fit



def remove_peak_by_energy(input_folder, output_folder, image_folder, log_callback = None,  ecenter =6385.0, window = 200.0,selected_groups=None,):
    """
    Removes 'carbon build-up' type peaks from Excel files in the folder.
    Saves the cleaned files and the graphs.
    """
    def log(msg):
        if log_callback:
           log_callback(msg)
        else:
            print(msg)
            
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    if not os.path.exists(image_folder):
        os.makedirs(image_folder)

    files = [f for f in os.listdir(input_folder) if f.endswith(".xlsx")]
    #print(f"files: {files}")

    if selected_groups:
        selected_groups = set(str(g) for g in selected_groups)
        files = [f for f in files if assign_group(f) in selected_groups]
    if not files:
        log("❌ No Excel files found.")
        return
    halfwidth_kev = 20
    emin = ecenter - window
    emax = ecenter + window
    
    # Compteurs pour stats finales
    processed = 0
    errors = 0
    
    for i, filename in enumerate(files):
        file_path = os.path.join(input_folder, filename)
        try:
            df = pd.read_excel(file_path)
            df = df.sort_values("Energie(keV)").reset_index(drop=True)

            # Vérifie que la colonne 'N_per_uC' contient bien des nombres
            df["N/C"] = pd.to_numeric(df["N/C"], errors="coerce")
            energie = df['Energie(keV)'].values
            y= df['N/C'].values
            
            mask_zone = (energie >= emin) & (energie <= emax)
            idx_zone = np.where(mask_zone)[0]
            
            if idx_zone.size == 0 :
                df_clean = df
            else : 
                y_zone = y[idx_zone]
            # Détection des pics dans la colonne 'N_per_uC'
                peaks_local, _ = find_peaks(y_zone)
                if peaks_local.size == 0:
                    df_clean = df
                else:
                   peaks_global = idx_zone[peaks_local]
                   e_peaks=energie[peaks_global]
                   best_idx = np.argmin(np.abs(e_peaks - ecenter))
                   peak_idx = peaks_global[best_idx]
                   energie_pic = energie[peak_idx]
                   
                   mask_keep =~(
                       (energie >= energie_pic-halfwidth_kev)& (energie <= energie_pic+halfwidth_kev)
                   )
                   df_clean = df[mask_keep].copy()

            # Sauvegarde
            cleaned_filename = os.path.splitext(filename)[0] + "_cleaned.xlsx"
            cleaned_path = os.path.join(output_folder, cleaned_filename)
            df_clean.to_excel(cleaned_path, index=False)
            log(f"✅ Processed {filename} - Peak at {energie_pic:.2f} keV removed.")
            # Génération du graphique
            plt.figure()
           # Données brutes
            plt.scatter(df["Energie(keV)"], df["N/C"], label="Point Supprimé", alpha=0.4)

            # Données filtrées
            plt.scatter(
                df_clean["Energie(keV)"],
                df_clean["N/C"],
                color="green",
                label="filtrer",
                alpha=0.6,
            )

            # Axes et titre
            plt.xlabel("Énergie (keV)")
            plt.ylabel("N/C")
            plt.ylim(bottom=0)  # Force l’axe des y à commencer à 0
            plt.title(f"Suppression des pics - {filename}")
            plt.legend()
            image_path = os.path.join(
                image_folder, f"{os.path.splitext(filename)[0]}_peaks.png"
            )
            
            plt.savefig(image_path)
            plt.close()
            processed += 1
            log(f"✅ {filename} traité ({energie_pic:.2f} keV si pic trouvé)")
        

        except Exception as e:
            errors += 1
            log(f"❌ Erreur {filename}: {e}")
            continue
        
    log(f"🎉 Terminaison : {processed} fichiers OK, {errors} erreurs")


def sigmoid(x, L, x0, k, b):
    
    y = L / (1 + np.exp(-k * (x - x0))) + b
    return y


# Définir une fonction pour calculer R^2
def calculate_r2(y_true, y_pred):
    residual_sum_of_squares = np.sum((y_true - y_pred) ** 2)
    total_sum_of_squares = np.sum((y_true - np.mean(y_true)) ** 2)
    r2 = 1 - (residual_sum_of_squares / total_sum_of_squares)
    return r2

def assign_group(file_name: str) -> str:
    """
    Assigne un groupe en prenant la partie avant '_' dans le nom de fichier.
    Exemple : '240429_1.xlsx' -> '240429'
    """
    base = os.path.basename(file_name)      # '240429_1.xlsx'
    stem, _ = os.path.splitext(base)       # '240429_1'
    parts = stem.split("_")                # ['240429', '1']

    if parts and parts[0].isdigit() and len(parts[0]) == 6:
        return parts[0]
    else:
        return "Unknown"


def fit_to_profile(folder_input,output_path,log_callback =None ) :
    if not os.path.exists(output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
    output_file = os.path.join(os.path.dirname(output_path), "fit_results.xlsx")
    base_dir = os.path.dirname(output_path)
    excel_dir = os.path.join(base_dir, "fits_data")
    image_dir = os.path.join(output_path, "fit_images")
    os.makedirs(excel_dir, exist_ok=True)
    os.makedirs(image_dir, exist_ok=True)
    #print("Fichier ciblé :", output_file)
    #print("Existe :", os.path.exists(output_file))
    if os.path.exists(output_file):
        os.remove(output_file)
        
    columns = ["name", "L", "b", "x0", "k", "diff_height", "sigma_tot","group"]
    df_final = pd.DataFrame(columns=columns)
   
    def log(msg):
        if log_callback:
               log_callback(msg)
        else:
            print(msg)
    
    files = [f for f in os.listdir(folder_input) if f.endswith(".xlsx")]
    #print(f"files: {files}")
    ratios      = []   # stocker les ratios au fur et à mesure
    u_mean_list = []
    u_fit_list  = []


    for file in files:
    
        log(f"Processing {file}...")
        base = file[:-5]          # "250317_0_cleaned"
        base = base.removesuffix("_cleaned") 
        excel_name = base+ ".xlsx"
        output_excel = (os.path.join(excel_dir,excel_name))
        columns_ex=["Energy", "count", "Energy_fit", "count_fit"]
        df_plot = pd.DataFrame(columns=columns_ex)
    
        file_path = os.path.join(folder_input, file)
        df = pd.read_excel(file_path)

        x = df['Energie(keV)'].values
        y = df['N/C'].values
        y_error = df['incertitudes'].values

        # ✅ NETTOYAGE CRITIQUE
        y_error = np.nan_to_num(y_error, nan=np.nanmedian(y_error), posinf=1e6, neginf=1e6)

        mask_finite = (
            np.isfinite(x) & np.isfinite(y) & np.isfinite(y_error) & (y > 0)
        )

        if np.sum(mask_finite) < 4:
            log(f"❌ {file}: Données insuffisantes")
            continue
        
        x, y, y_error = x[mask_finite], y[mask_finite], y_error[mask_finite]

        # Tri
        if len(x) >= 2 and x[0] > x[-1]:
            x, y, y_error = x[::-1], y[::-1], y_error[::-1]

        # ✅ p0 sécurisé
        try:
            p0 = [max(y), np.median(x), 0.1, min(y)]
        except:
            log(f"❌ {file}: Impossible de définir p0")
            continue
        
        # curve_fit avec bounds pour stabilité
        try:
            popt, pcov = curve_fit(
                sigmoid, x, y, p0,
                sigma=y_error, absolute_sigma=True,
                method='dogbox', maxfev=10000,
                bounds=([-np.inf, min(x)-10, 0, -np.inf], [np.inf, max(x)+10, np.inf, np.inf])
            )
            
        except Exception as e:
            log(f"❌ {file}: curve_fit échoué {e}")
            continue
        
        
        L,xc, k, b =popt
        
        Real_height = L-b
        
        y_pred =sigmoid(x, *popt)
        r2 = calculate_r2(y, y_pred)
        var_params = np.diag(pcov)
        u_params = np.sqrt(var_params)

        u_L  = u_params[0]
        u_x0 = u_params[1]
        u_k  = u_params[2]
        u_b  = u_params[3]

        u_H_fit_corr = np.sqrt(pcov[0,0] + pcov[3,3] - 2*pcov[0,3])
        
        
        group = assign_group(file)
        df_final.loc[len(df_final.index)]=[
            file, L, b, xc ,k,Real_height,u_H_fit_corr,group
        ]

        # ── Méthode quantiles (indépendante du fit) ─────────────────────────
        q_low  = np.quantile(x, 0.125)   # frontière basse : 1er quartile
        q_high = np.quantile(x, 0.65)   # frontière haute : 3e quartile

        mask_bas  = x < q_low
        mask_haut = x > q_high
        n_bas     = np.sum(mask_bas)
        n_haut    = np.sum(mask_haut)

        if n_haut >= 2 and n_bas >= 2:
            # Moyennes pondérées par les incertitudes
            w_haut = 1.0 / y_error[mask_haut]**2
            w_bas  = 1.0 / y_error[mask_bas]**2

            mu_haut = np.sum(w_haut * y[mask_haut]) / np.sum(w_haut)
            mu_bas  = np.sum(w_bas  * y[mask_bas])  / np.sum(w_bas)

            # Incertitudes sur les moyennes pondérées
            u_mu_haut = np.sqrt(1.0 / np.sum(w_haut))
            u_mu_bas  = np.sqrt(1.0 / np.sum(w_bas))

            H_mean        = mu_haut - mu_bas
            u_H_mean      = np.sqrt(u_mu_haut**2 + u_mu_bas**2)
            u_H_mean_pct  = u_H_mean / H_mean * 100.0

            # H depuis curve_fit (avec correction covariance)
            H_fit        = L - b          # = Real_height
            u_H_fit_corr = np.sqrt(pcov[0,0] + pcov[3,3] - 2*pcov[0,3])
            u_H_fit_pct  = u_H_fit_corr / H_fit * 100.0

            #print(f"\n{'─'*55}")
            #print(f"Fichier : {file}")
            #print(f"Fichier : {file}")
            #print(f"  Quantiles : Q25 = {q_low:.1f} keV  |  Q75 = {q_high:.1f} keV")
            #print(f"  x0_fit = {xc:.1f} keV  (info seulement, non utilisé pour H)")
            #print(f"  Points plateau haut : {n_haut}   |   plateau bas : {n_bas}")
            #print(f"  μ_haut = {mu_haut:.3f}   μ_bas = {mu_bas:.3f}")
            #print(f"  ── Méthode moyennes ──────────────────────────────")
            #print(f"     H        = {H_mean:.3f}  ±  {u_H_mean:.3f}  ({u_H_mean_pct:.2f} %)")
            #print(f"  ── curve_fit (avec correction cov) ───────────────")
            #print(f"     H        = {H_fit:.3f}  ±  {u_H_fit_corr:.3f}  ({u_H_fit_pct:.2f} %)")
            #print(f"  ── Ratio u_fit / u_mean ──────────────────────────")
            #print(f"     facteur  = {u_H_fit_corr / u_H_mean:.2f}x")
            #print(f"{'─'*55}")
            ratios.append(u_H_fit_corr / u_H_mean)
            u_mean_list.append(u_H_mean_pct)
            u_fit_list.append(u_H_fit_pct)
        else:
            print(f"⚠️  {file} : plateaux insuffisants "
                  f"(n_haut={n_haut}, n_bas={n_bas}) — marge réduite à 1/k")
        
        x_fit = np.linspace(min(x), max(x), 500)
        yfit = sigmoid(x_fit, *popt)
        n_data = len(x)
        n_fit = len(x_fit)
        n = max(n_data, n_fit)
        # pad avec NaN
        def pad(arr, n):
            out = np.full(n, np.nan)
            out[:len(arr)] = arr
            return out
        df_plot = pd.DataFrame({
            "Energy": pad(x, n),
            "count": pad(y, n),
            "Energy_fit": pad(x_fit, n),
            "count_fit": pad(yfit, n),
        })
        
        plt.figure()
        plt.errorbar(
        x, y, yerr=y_error, fmt="o", label="Données", color="green"
        )
        plt.plot(x_fit, yfit, label="Ajustement sigmoïde")
        plt.xlabel("15N energy (keV)")
        plt.ylabel("N/µC")
        plt.legend()
        plt.title("Ajustement sigmoïde \nR² = " + str(round(r2, 3)))
        png_name = file[:-5] + ".png"
        png_path = os.path.join(os.path.dirname(output_path), " fit images", png_name)
        os.makedirs(os.path.dirname(png_path), exist_ok=True)
        plt.savefig(png_path)
        log(f'sauvegarde de la figure {png_path} ')
        plt.close()
        df_plot.to_excel(output_excel, index=False)
    df_final.to_excel(output_file, index=False)
    print(f"\n{'═'*55}")
    print(f"SYNTHÈSE GLOBALE ({len(ratios)} fichiers)")
    print(f"  u(H) méthode quantiles : {np.mean(u_mean_list):.3f} %")
    print(f"  u(H) méthode quantiles : {np.median(u_mean_list):.3f} % (médiane)")
    print(f"  u(H) curve_fit corrigé : {np.mean(u_fit_list):.3f} %")
    print(f"  Ratio moyen            : {np.mean(ratios):.2f}×")
    print(f"  Ratio médian           : {np.median(ratios):.2f}×")
    print(f"  Min u(H)               : {np.min(u_mean_list):.3f} %")
    print(f"  Max u(H)               : {np.max(u_mean_list):.3f} %")
    print(f"{'═'*55}")
    log(f"✅ Processing completed.")

