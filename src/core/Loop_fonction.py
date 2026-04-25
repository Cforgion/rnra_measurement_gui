import os
import numpy as np
import pandas as pd
import core.Traitement_fonctions as fonc



def energy_conversion(V, Y25=False):
    """
    Converts a voltage (kV) to energy (keV) according to a physical model
    that differs depending on the sample type (Y25 or not).

    Parameters
    ----------
    V : float
        Measured voltage (in kV).
    Y25 : bool, optional
        Indicates if the Y25 model should be used. Default is False.

    Returns
    -------
    float
        Converted energy in keV.
    """
    V = np.float64(V)
    if Y25:
        B = np.float64(36)
        Mr = np.float64(15 / 27)
        return (B * Mr) + (3 + Mr) * (np.float64(1.0054) * V - np.float64(1.44))
    else:
        B = np.float64(36)
        Mr = np.float64(15 / 28)
        return (B * Mr) + (3 + Mr) * (np.float64(1.0076) * V - np.float64(1.56))

import os
import numpy as np
import pandas as pd
import core.Traitement_fonctions as fonc


def extraire_donnée_excel(folder_path, col_voltage="Tension terminale (kV)",
                          col_energie="Energie (keV)", log_callback=None):
    """
    Lit les fichiers Excel du dossier et extrait les colonnes voltage ET énergie.
    L'énergie est lue directement depuis l'Excel (déjà calculée), plus besoin
    de energy_conversion().

    Retourne un dict :
        {
          "NomFichier_1": {"V": [v1, v2, ...], "E": [e1, e2, ...]},
          "NomFichier_2": {"V": [...],          "E": [...]},
          ...
        }
    Les suffixes _1, _2 … correspondent aux blocs séparés détectés dans
    chaque fichier (séparation sur répétition de valeur dans la colonne voltage).
    """
    def log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(msg)

    fichiers_xlsx = sorted(
        [f for f in os.listdir(folder_path) if f.lower().endswith(".xlsx")]
    )

    if not fichiers_xlsx:
        log("❌ Aucun fichier Excel trouvé dans le dossier.")
        return {}

    dict_resultats = {}

    for fichier in fichiers_xlsx:
        log(f"📂 Traitement du fichier : {fichier}")
        chemin = os.path.join(folder_path, fichier)

        try:
            xls = pd.ExcelFile(chemin)
            feuille = "Sheet1" if "Sheet1" in xls.sheet_names else xls.sheet_names[0]
            log(f"📄 Feuille lue : {feuille}")

            df = pd.read_excel(xls, sheet_name=feuille, header=None)

            # Supprimer les lignes contenant "K ="
            df = df[
                ~df.apply(
                    lambda row: row.astype(str).str.contains("K =", na=False).any(),
                    axis=1,
                )
            ].reset_index(drop=True)

            # La première ligne restante est le header
            header = df.iloc[0].astype(str).str.strip().tolist()
            log(f"🔍 Headers détectés : {header}")
            data = df.iloc[1:].reset_index(drop=True)
            data.columns = header

            # Vérifier que les colonnes existent
            if col_voltage not in header:
                log(f"⚠️ Colonne '{col_voltage}' introuvable dans {fichier}. Ignoré.")
                continue
            if col_energie not in header:
                log(f"⚠️ Colonne '{col_energie}' introuvable dans {fichier}. Ignoré.")
                continue

            # Extraire et convertir en numérique
            V_series = pd.to_numeric(data[col_voltage], errors="coerce")
            E_series = pd.to_numeric(data[col_energie], errors="coerce")

            # Combiner dans un DataFrame propre et supprimer les NaN
            df_clean = pd.DataFrame({"V": V_series, "E": E_series}).dropna()

            if df_clean.empty:
                log(f"⚠️ Aucune donnée valide dans {fichier}.")
                continue

            log(f"🔍 {len(df_clean)} lignes valides extraites.")

            # ── Séparation en blocs sur répétition du voltage ──────────
            blocs_V = []
            blocs_E = []
            bloc_V_courant = []
            bloc_E_courant = []
            prev_V = None

            for _, row in df_clean.iterrows():
                v, e = row["V"], row["E"]
                # Nouveau bloc si la valeur de voltage se répète
                if prev_V is not None and v == prev_V:
                    if bloc_V_courant:
                        blocs_V.append(bloc_V_courant)
                        blocs_E.append(bloc_E_courant)
                        bloc_V_courant = []
                        bloc_E_courant = []
                bloc_V_courant.append(v)
                bloc_E_courant.append(e)
                prev_V = v

            # Dernier bloc
            if bloc_V_courant:
                blocs_V.append(bloc_V_courant)
                blocs_E.append(bloc_E_courant)

            # Stocker avec suffixe _1, _2, ...
            base = fichier.replace(".xlsx", "").replace(".xls", "")
            for i, (bV, bE) in enumerate(zip(blocs_V, blocs_E)):
                cle = f"{base}_{i + 1}"
                dict_resultats[cle] = {"V": bV, "E": bE}
                log(f"  🔑 Bloc '{cle}' : {len(bV)} points  "
                    f"E={bE[0]:.1f}→{bE[-1]:.1f} keV")

        except Exception as e:
            log(f"❌ Erreur lors du traitement de {fichier} : {e}")

    return dict_resultats


# ---------------------------------------------------------------------------
# Fonctions utilitaires conservées (utilisées ailleurs)
# ---------------------------------------------------------------------------

def validate_input(input_str, input_type=float, log_callback=None):
    def log(msg):
        if log_callback:
            log_callback(msg)
        else:
            print(msg)
    try:
        return input_type(input_str)
    except ValueError:
        log(f"Valeur invalide : {input_str}. Attendu : {input_type.__name__}.")
        return None


def find_channel(energy, slope, intercept):
    energy = np.float64(energy)
    slope = np.float64(slope)
    intercept = np.float64(intercept)
    return (energy - intercept) / slope


# ---------------------------------------------------------------------------
# Boucle principale
# ---------------------------------------------------------------------------

def Boucle_sans_variation(data_entry, path_exit, c_min, c_max, log_callback=None):
    """
    Boucle de traitement des fichiers MPA.

    Parameters
    ----------
    data_entry : list[dict] | pd.DataFrame
        Scénarios de configuration (un par ligne).
    path_exit : str
        Dossier de sortie pour les fichiers Excel de résultats.
    c_min, c_max : float
        Bornes de la ROI en canaux.
    log_callback : callable, optional
        Fonction de log (ex : self.log dans l'onglet tkinter).
    """
    def log(msg):
        if log_callback:
            log_callback(str(msg))
        else:
            print(msg)

    # Normalisation de data_entry en DataFrame
    if isinstance(data_entry, list):
        data_entry = pd.DataFrame(data_entry)
    elif isinstance(data_entry, dict):
        data_entry = pd.DataFrame([data_entry])
    elif not isinstance(data_entry, pd.DataFrame):
        raise TypeError(
            f"data_entry doit être un DataFrame, list ou dict, pas {type(data_entry)}"
        )

    data_entry.columns = data_entry.columns.astype(str).str.strip().str.lower()

    # Conversion des colonnes numériques
    for col in ["slope", "intercept"]:
        data_entry[col] = pd.to_numeric(data_entry[col], errors="coerce").astype(np.float64)

    for ind in data_entry.index:

        sample_name  = data_entry["sample_name"][ind]
        file_init    = int(data_entry["first_file"][ind])
        file_fin     = int(data_entry["last_file"][ind])
        url_dossier  = data_entry["data_folder"][ind]
        numero_file  = str(data_entry["file_number"][ind])   # préfixe string
        slope_mod    = data_entry["slope"][ind]
        terme_ind    = data_entry["intercept"][ind]
        ADC_n        = data_entry["adc"][ind]
        url_tension  = data_entry["tension_folder"][ind]
        error_cal    = data_entry["erreur_calib"][ind]

        log(f"\n🔹 Traitement de : {sample_name}")

        # ── Lecture du fichier Excel de tensions/énergies ───────────────
        dict_data = extraire_donnée_excel(
            url_tension,
            col_voltage="Tension terminale (kV)",
            col_energie="Energie (keV)",
            log_callback=log,
        )

        # Récupérer le bloc correspondant au sample
        bloc = dict_data.get(sample_name)
        if not bloc:
            log(f"⚠️ Données non trouvées pour '{sample_name}'. "
                f"Clés disponibles : {list(dict_data.keys())}")
            continue

        E_list = bloc["E"]   # ✅ énergies directement depuis l'Excel
        V_list = bloc["V"]   # voltages (conservés si besoin de debug)

        log(f"  📊 {len(E_list)} points d'énergie chargés "
            f"({E_list[0]:.1f} → {E_list[-1]:.1f} keV)")

        # Ordre d'itération des fichiers
        if file_init > file_fin:
            file_init, file_fin = file_fin, file_init

        start = file_init
        stop  = file_fin + 1
        step  = 1

        liste_coups       = []
        liste_incertitude = []
        liste_fichier_num = []
        liste_energie     = []

        for i in range(start, stop, step):
            num_en_str = str(i).zfill(3)
            ADC_file        = f"{numero_file}{num_en_str}_ADCDATA0.txt"
            charge_file     = f"{numero_file}{num_en_str}_ADCDATA3.txt"
            chemin_ROI      = os.path.join(url_dossier, ADC_file)
            chemin_charge   = os.path.join(url_dossier, charge_file)

            if not os.path.exists(chemin_ROI) or not os.path.exists(chemin_charge):
                log(f"  ⚠️ Fichier manquant : {ADC_file} ou {charge_file}. Ignoré.")
                continue

            try:
                liste_result = fonc.coups_normal_pour_un_fichier(
                    chemin_ROI,
                    chemin_charge,
                    c_min,
                    c_max,
                    error_cal,
                )

                liste_coups.append(liste_result[0])
                liste_incertitude.append(liste_result[1])
                liste_fichier_num.append(i)

                # ✅ Énergie lue directement — plus besoin de energy_conversion()
                index_local = i - start
                E = E_list[index_local] if index_local < len(E_list) else np.nan
                liste_energie.append(E)

            except Exception as e:
                log(f"  ❌ Erreur traitement {ADC_file} : {e}")
                continue

        if not liste_coups:
            log(f"  ⚠️ Aucun fichier traité pour {sample_name}.")
            continue

        # ── Sauvegarde ─────────────────────────────────────────────────
        df_out = pd.DataFrame({
            "numero_fichier": liste_fichier_num,
            "N/C":            liste_coups,
            "incertitudes":   liste_incertitude,
            "Energie(keV)":   liste_energie,
        })

        output_file = os.path.join(path_exit, f"{numero_file}_{ind}.xlsx")
        df_out.to_excel(output_file, sheet_name="resultats", index=True,
                        index_label="indice")
        log(f"  ✅ Fichier sauvegardé : {output_file}")

    log("\n🎯 Boucle terminée.")