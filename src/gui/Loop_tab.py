import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import os
from matplotlib.figure import Figure
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.widgets import SpanSelector
from tkinter.scrolledtext import ScrolledText

# ✅ AJOUTER CECI AVANT LES IMPORTS LOCAUX
import sys
# Remonter au dossier parent (src) puis accéder à utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.Loop_fonction import Boucle_sans_variation
from core.Transform_functions import remove_peak_by_energy, fit_to_profile



class loop_tab(ttk.Frame):
    """Onglet pour la boucle de traitement des fichiers MPA, extraction des données, et affichage des résultats
    
    """
    def __init__(self, parent, app_state):
        super().__init__(parent)
        self.app_state = app_state
        self.temp_dir = os.path.join(os.path.dirname(__file__), "..","temp")
        self.temp_dir = os.path.abspath(self.temp_dir)
        os.makedirs(self.temp_dir, exist_ok=True)
        self.roi_min = None
        self.roi_max = None
        self.roi_min_e = None
        self.roi_max_e = None
        self.save_var = tk.BooleanVar(value=False)
        self.output_dir_var = tk.StringVar(value=self.temp_dir)
        self.config_path = self.app_state.get("config_path", None)
        self.config_path_var = tk.StringVar(value=self.config_path or "")

        self.roi_var = tk.StringVar(value="ROI non définie")
        self.default_ecenter = 6385.0  # même valeur que dans remove_peak_by_energy
        self.default_window = 200.0
        self.default_half_width = 20.0
        self.ecenter_var = tk.DoubleVar(value=self.default_ecenter)
        self.window_var = tk.DoubleVar(value=self.default_window)
        self.half_width_var = tk.DoubleVar(value=self.default_half_width)

        self.has_boucle =False
        self.has_peak_remove = False
        self.save_cleaned_var = tk.BooleanVar(value=True) 
 
        # Configure l'interface
        self.setup_ui()
    
    def setup_ui(self):
        "configuration de l'interface"
        self.bind_all("<Return>", self._invoke_focused_button)
        # Frame diviser en 2"
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Gauche
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side='left', fill='y', padx=5)
        
        # Boucle_frame 
        boucle_Frame = ttk.LabelFrame(left_frame, text="Boucle de traitement des fichiers MPA")
        boucle_Frame.pack(fill='x', pady=5)
        #Frame de chargement des fichier 
        files_frame = ttk.LabelFrame(boucle_Frame, text="1. Charger les fichiers")
        files_frame.pack(fill='x', pady=5) 
            
        ttk.Entry(files_frame,
                  textvariable =self.config_path_var,
                  state ="readonly",
                  width = 50
                  ). pack(side = 'left', fill ='x', expand =True, padx = 5 ,pady = 5)
               
        ttk.Button(files_frame, text="Charger le fichier excel de configuration",
                   command=self.load_config).pack(side = 'left', padx=5, pady=5)
        

        
        roi_frame = ttk.LabelFrame(boucle_Frame, text="2. Selection de la ROI")
        roi_frame.pack(fill='x', pady=5)

        # Variable liée à l'Entry
        self.roi_var = tk.StringVar(value="ROI non définie")

        # Entry éditable par l'utilisateur
        ttk.Entry(
            roi_frame,
            textvariable=self.roi_var,
            width=50
        ).pack(fill='x', padx=5, pady=5)
        
        # Bouton pour ouvrir la fenêtre de choix de ROI
        ttk.Button(
            roi_frame,
            text="2. Choisir la ROI sur un Spectre",
            command=self.open_roi_window
        ).pack(fill='x', padx=5, pady=5)
        
        out_frame = ttk.LabelFrame(left_frame, text="3. Sauvegarde des résultats")
        out_frame.pack(fill='x', pady=5)
        ttk.Checkbutton(
            out_frame,
            text ="Sauvegarder les résultats",
            variable =self.save_var,
            command =self.on_toggle_save
        ).pack(anchor='w', padx=5, pady=2)
        self.out_entry = ttk.Entry(
            out_frame,
            textvariable=self.output_dir_var,
            width=50,
            state="disabled"
        )
        self.out_entry.pack(side='left', fill='x', expand=True, padx=5)

        self.out_button = ttk.Button(
            out_frame,
            text="Parcourir",
            command=self.choose_output_dir,
            state="disabled"
        )
        self.out_button.pack(side='left', padx=5)

        run_frame = ttk.LabelFrame(boucle_Frame, text="4. Lancer la boucle de traitement")
        run_frame.pack(fill='x', pady=5)
        ttk.Button(run_frame,
                   text ="Traitement des fichiers",
                   command = self.run_loop).pack(fill='x', padx = 5, pady = 5)
        
        
        
        ejec_frame = ttk.LabelFrame(left_frame, text="Suppression du pic de Carbon build-up")
        ejec_frame.pack(fill='x', pady=5)
        ttk.Label(ejec_frame, text="Energie centre (keV) :").grid(row=0, column =0, sticky='w')
        ttk.Entry(ejec_frame, textvariable =self.ecenter_var,width = 10).grid (row =0, column= 1 , sticky='w')
        ttk.Label(ejec_frame, text="Fenêtre de recherche (keV) :").grid(row=1, column=0, sticky="w")
        ttk.Entry(ejec_frame, textvariable=self.window_var, width=10).grid(row=1, column=1, sticky="w")

        ttk.Label(ejec_frame, text="Largeur à supprimer (keV) :").grid(row=2, column=0, sticky="w")
        ttk.Entry(ejec_frame, textvariable=self.half_width_var, width=10).grid(row=2, column=1, sticky="w",)
       
        ttk.Button(ejec_frame,
                   text = "Supprimer le pic build-up",
                   command =self.run_remove_carbon_peak).grid(row = 4, column = 0, columnspan =2 , pady =5)
        
        fit_frame = ttk.LabelFrame(left_frame, text ="Fit Sigmoïde")
        fit_frame.pack(fill='x', pady=5)
        ttk.Button(
            fit_frame,
            text ="Lancer le fit sur les profils de sortie",
            command = self.run_fit).pack(fill='x', padx =5, pady = 2)
        
        
        vis_frame = ttk.LabelFrame(left_frame,text =" Option de visualisation du profil")
        vis_frame.pack(fill='x', pady=5)
        
        

        ttk.Button(
            vis_frame,
            text ="Afficher un profil de sortie choisi",
            command =self.load_result_file,
        ).pack(anchor='w', padx =5, pady = 2)

        
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side='right', fill='both', expand=True)
        
        # Figure Matplotlib
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("Energie (keV)")
        self.ax.set_ylabel("N/C")
        self.ax.set_title("Profil de sortie")
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        toolbar = NavigationToolbar2Tk(self.canvas, right_frame)
        
        results_frame = ttk.LabelFrame(left_frame, text="Détails")
        results_frame.pack(fill='both', expand=True, pady=5)
        # ScrolledText pour afficher les résultats du fit
        self.results_text = tk.Text(results_frame, width=35, wrap=tk.WORD)
        scollbar = ttk.Scrollbar(results_frame, command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scollbar.set)

        self.results_text.pack(side='left', fill='both', expand=True, padx=(5,0), pady=5)
        scollbar.pack(side='right', fill='y', padx=(0,5), pady=5)
        
        self.refresh_from_app_state()
   
    def _invoke_focused_button(self, event=None):
        widget = self.focus_get()
        if isinstance(widget, ttk.Button):
            widget.invoke()
            return "break"



    def parse_roi_energy_from_entry(self):
        """
        Lit self.roi_var (ex: '1000-2000' ou '1000 – 2000 keV'),
        met à jour roi_min_e / roi_max_e (keV) et roi_min / roi_max (canaux).
        """
        text = self.roi_var.get()
        if text == "ROI non définie":
            raise ValueError("ROI non définie")

        # Nettoyage basique
        text = text.replace("keV", "").replace("KEV", "")
        text = text.replace("–", "-")   # tiret long → tiret simple
        text = text.replace(" ", "")

        parts = text.split("-")
        if len(parts) != 2:
            raise ValueError("Format ROI invalide (attendu: emin-emax)")

        try:
            v1 = float(parts[0])
            v2 = float(parts[1])
        except ValueError:
            raise ValueError("Les bornes de la ROI doivent être numériques")

        emin = min(v1, v2)
        emax = max(v1, v2)

        # --- Récupération du spectre comme dans open_roi_window ---
        scenarios = self.charger_config_loop()
        
        if not scenarios:
            raise ValueError("Config invalide pour calculer la ROI")
        sc = scenarios[0]
        data_folder = sc["data_folder"]
        numero_file = sc["file_number"]
        last_file = sc["last_file"]
        slope = sc["slope"]
        intercept = sc["intercept"]

        num_en_str = str(last_file).zfill(3)
        adc0_file = f"{numero_file}{num_en_str}_ADC0.txt"
        chemin_spectre = os.path.join(data_folder, adc0_file)

        data = np.loadtxt(chemin_spectre)
        x = data[:, 0]
        energie = slope * x + intercept

        # Conversion énergie → canaux
        ch_min = np.interp(emin, energie, x)
        ch_max = np.interp(emax, energie, x)

        self.roi_min_e = emin
        self.roi_max_e = emax
        self.roi_min = ch_min
        self.roi_max = ch_max
 
    def log(self, message: str):
        self.results_text.insert("end", message + "\n")
        self.results_text.see("end")  # scroll auto
    
    def set_config_path(self, config_path):
        self.config_path = config_path
        self.app_state["config_path"] = config_path
        self.config_path_var.set(config_path or "")
        self.log(f"Config reçu automatiquement : {config_path}")
    
    def load_result_file(self):
        """Permet de choisir un fichier de résultat pour le visualiser"""
        initial_dir = self.path_exit if getattr(self, "path_exit", "") else os.getcwd()
        filename = filedialog.askopenfilename(
            title="Choisir un fichier de résultat à visualiser",
            initialdir=initial_dir,
            filetypes=[
                ("Excel files", "*.xlsx *.xls"),
                ("Image files", "*.png *.jpg *.jpeg"),
                ("All files", "*.*"),
            ],
        )
        if not filename:
            return
       
        
        # --- CAS EXCEL ---
        if filename.endswith((".xlsx", ".xls")):
            try:
                df = pd.read_excel(filename)

                cols = set(df.columns)
                required = {"Energy", "count", "Energy_fit", "count_fit"}
                # 1) Profil brut: Energie(keV) + N/C (+ incertitudes optionnelles)
                if "Energie(keV)" in cols and "N/C" in cols:
                    energie = df["Energie(keV)"].values
                    nc = df["N/C"].values
                    incertitudes = df["incertitudes"].values if "incertitudes" in cols else None

                    self.ax.clear()
                    self.ax.scatter(energie, nc, color="tab:blue", label="Données")

                    if incertitudes is not None:
                        self.ax.errorbar(
                            energie,
                            nc,
                            yerr=incertitudes,
                            ecolor="red",
                            ls="none",
                            capsize=5,
                            label="Incertitudes",
                        )

                    self.ax.set_xlabel("Energie (keV)")
                    self.ax.set_ylabel("N/C")
                    self.ax.set_ylim(0)
                    self.ax.set_title(f"Profil de sortie : {os.path.basename(filename)}")
                    self.ax.legend()
                    self.canvas.draw()

                # 2) Fichier de fit: Energy / count / Energie_fit / count_fit
                
                elif all(c in cols for c in required):
                    x_data = df["Energy"].values
                    y_data = df["count"].values
                    x_fit = df["Energy_fit"].values
                    y_fit = df["count_fit"].values

                    self.ax.clear()
                    # données expérimentales
                    self.ax.scatter(x_data, y_data, color="tab:blue", label="Données")
                    # courbe de fit
                    self.ax.plot(x_fit, y_fit, color="orange", label="Fit sigmoïde")

                    self.ax.set_xlabel("Energie (keV)")
                    self.ax.set_ylabel("N/µC")
                    self.ax.set_ylim(0)
                    self.ax.set_title(f"Fit sigmoïde : {os.path.basename(filename)}")
                    self.ax.legend()
                    self.canvas.draw()

                else:
                    messagebox.showerror(
                        "Erreur",
                        "Le fichier Excel ne correspond pas à un profil brut "
                        "(colonnes 'Energie(keV)', 'N/C') ni à un fichier de fit "
                        "(colonnes 'Energy', 'count', 'Energy_fit', 'count_fit').",
                    )
                    return

            except Exception as e:
                messagebox.showerror(
                    "Erreur",
                    f"Impossible de lire le fichier de résultat :\n{e}",
                )

        # --- CAS IMAGE ---
        elif filename.endswith((".png", ".jpg", ".jpeg")):
            try:
                img = plt.imread(filename)
                self.ax.clear()
                self.ax.imshow(img)
                self.ax.axis("off")
                self.ax.set_title(f"Image : {os.path.basename(filename)}")
                self.canvas.draw()
            except Exception as e:
                messagebox.showerror(
                    "Erreur",
                    f"Impossible de lire le fichier image :\n{e}",
                )
      
    def load_config(self):
        self.refresh_from_app_state()

        if self.config_path:
            self.config_path_var.set(self.config_path)
            return

        filename = filedialog.askopenfilename(
            title="Choisir le fichier Excel de configuration",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if not filename:
            return

        self.config_path = filename
        self.config_path_var.set(filename)
        self.app_state["config_path"] = filename
        
    def charger_config_loop(self):
        """
        Lit le fichier Excel de configuration et retourne une liste de scénarios
        compatibles avec Boucle_sans_variation().
        """
        if not self.config_path:
            messagebox.showerror("Erreur", "Aucun fichier de configuration chargé.")
            return []

        try:
            df = pd.read_excel(self.config_path)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lire le fichier Excel :\n{e}")
            return []

        # Nettoyage des noms de colonnes
        df.columns = [str(c).strip() for c in df.columns]

        # Harmonisation des noms de colonnes vers le format attendu par la boucle
        rename_map = {
            "tension folder": "tension_folder",
            "data folder": "data_folder",
            "first file": "first_file",
            "last file": "last_file",
            "file number": "file_number",
            "error_calib": "erreur_calib",
            "group_root": "file_number",
        }
        df = df.rename(columns=rename_map)

        required = [
            "sample_name",
            "tension_folder",
            "data_folder",
            "file_number",
            "first_file",
            "last_file",
            "ADC",
            "slope",
            "intercept",
            "erreur_calib",
        ]

        missing = [c for c in required if c not in df.columns]
        if missing:
            messagebox.showerror(
                "Erreur",
                f"Colonnes manquantes dans le fichier de configuration : {missing}"
            )
            return []

        # Conversions de types
        try:
            df["sample_name"] = df["sample_name"].astype(str).str.strip()
            df["tension_folder"] = df["tension_folder"].astype(str).str.strip()
            df["data_folder"] = df["data_folder"].astype(str).str.strip()

            # group_root = 250317, utilisé comme préfixe de nom de fichier
            df["file_number"] = df["file_number"].astype(str).str.strip()

            df["ADC"] = pd.to_numeric(df["ADC"], errors="raise").astype(int)
            df["first_file"] = pd.to_numeric(df["first_file"], errors="raise").astype(int)
            df["last_file"] = pd.to_numeric(df["last_file"], errors="raise").astype(int)
            df["slope"] = pd.to_numeric(df["slope"], errors="raise").astype(float)
            df["intercept"] = pd.to_numeric(df["intercept"], errors="raise").astype(float)
            df["erreur_calib"] = pd.to_numeric(df["erreur_calib"], errors="raise").astype(float)
        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"Impossible de convertir certaines colonnes du fichier Excel :\n{e}"
            )
            return []

        scenarios = []
        for _, row in df.iterrows():
            scenario = {
                "sample_name": row["sample_name"],
                "tension_folder": row["tension_folder"],
                "data_folder": row["data_folder"],
                "file_number": row["file_number"],
                "first_file": row["first_file"],
                "last_file": row["last_file"],
                "ADC": row["ADC"],
                "slope": row["slope"],
                "intercept": row["intercept"],
                "erreur_calib": row["erreur_calib"],
            }
            scenarios.append(scenario)

        return scenarios

    def open_roi_window(self):
        """Ouvre une fenêtre pour choisir la ROI sur un spectre de référence."""
        if not self.config_path:
            messagebox.showwarning(
                "Config manquante",
                "Veuillez d'abord charger un fichier de configuration."
            )
            return

        scenarios = self.charger_config_loop()
        if not scenarios:
            return

        sc = scenarios[0]  # pour l'instant, premier sample

        data_folder = sc["data_folder"]
        numero_file = sc["file_number"]
        last_file = sc["last_file"]
        slope = sc["slope"]
        intercept = sc["intercept"]
        
        num_en_str = str('5').zfill(3)
        adc0_file = f"{numero_file}{num_en_str}_ADCDATA0.txt"
        chemin_spectre = os.path.join(data_folder, adc0_file)

        if not os.path.exists(chemin_spectre):
            messagebox.showerror(
                "Erreur",
                f"Fichier de spectre introuvable :\n{chemin_spectre}"
            )
            return

        try:
            data = np.loadtxt(chemin_spectre)
            x = data[:, 0]
            y = data[:, 1]
        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"Impossible de lire le spectre de référence :\n{e}"
            )
            win.destroy()
            return

        energie = slope * x + intercept

        # Fenêtre modale
        win = tk.Toplevel(self)
        win.title("Choix de la ROI")
        win.grab_set()

        fig = Figure(figsize=(8, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.get_tk_widget().pack(fill="both", expand=True)
        toolbar = NavigationToolbar2Tk(canvas, win)
        toolbar.update()


        ax.plot(energie, y, "o-", markersize=2)
        ax.set_xlabel("Energie (keV)")
        ax.set_ylabel("Counts")
        ax.set_title("Sélection de la ROI")
        canvas.draw()

        roi_local = {"emin": None, "emax": None}
        entry_frame = ttk.Frame(win)
        entry_frame.pack(fill="x",padx = 5 , pady = 5)
        ttk.Label(entry_frame,text='Emin (keV) : ').grid(row = 0,column=0,sticky="w")
        emin_var=tk.StringVar()
        ttk.Entry(entry_frame, textvariable= emin_var,width = 10).grid(row=0,column=1,padx = 5)
        ttk.Label(entry_frame,text='Emax (keV) : ').grid(row=0,column=2,sticky="w")
        emax_var = tk.StringVar()
        ttk.Entry(entry_frame, textvariable= emax_var,width = 10).grid(row=0,column=3,padx = 5)
        
        def apply_manual_roi():
            try:
                emin = float(emin_var.get())
                emax = float(emax_var.get())
            except ValueError:
                messagebox.showwarning("Valeur invalide", "Veuillez entrer des valeurs numériques pour Emin et Emax.")
                return
            if emin >= emax:
                messagebox.showwarning("ROI invalide", "Emin doit être strictement inférieur à Emax.")
                return

            roi_local["emin"] = emin
            roi_local["emax"] = emax

            ax.clear()
            ax.plot(energie, y, "o-", markersize=2)
            ax.axvspan(emin, emax, color="tab:blue", alpha=0.3)
            ax.set_xlabel("Energie (keV)")
            ax.set_ylabel("Counts")
            ax.set_title("Sélection de la ROI")
            canvas.draw()

        ttk.Button(entry_frame, text="Appliquer ROI manuelle", 
                   command=apply_manual_roi).grid(row=0, column=4, padx=5)
        
        def on_select(xmin, xmax):
            if xmin > xmax:
                xmin, xmax = xmax, xmin
            roi_local["emin"] = xmin
            roi_local["emax"] = xmax
    
            # mise à jour des Entry
            emin_var.set(f"{xmin:.1f}")
            emax_var.set(f"{xmax:.1f}")
    
            ax.clear()
            ax.plot(energie, y, "o-", markersize=2)
            ax.axvspan(xmin, xmax, color='tab:blue', alpha=0.3)
            ax.set_xlabel("Energie (keV)")
            ax.set_ylabel("Counts")
            ax.set_title("Sélection de la ROI")
            canvas.draw()
        win.span = SpanSelector(
            ax,
            on_select,
            "horizontal",
            useblit=True,
            props=dict(alpha=0.3, facecolor='tab:blue'),
            interactive=True,
            drag_from_anywhere=True,
        )

        def validate_roi():
            if roi_local["emin"] is None or roi_local["emax"] is None:
                messagebox.showwarning("ROI manquante", "Veuillez d'abord sélectionner une ROI.")
                return
            emin = roi_local["emin"]
            emax = roi_local["emax"]
            self.roi_min_e = emin
            self.roi_max_e = emax 
            
            ch_min = np.interp(emin, energie, x)
            ch_max = np.interp(emax, energie, x)
            
            self.roi_min = ch_min
            self.roi_max = ch_max
            
            self.roi_var.set(f"{self.roi_min_e:.1f} – {self.roi_max_e:.1f} keV")
            win.destroy()

        ttk.Button(win, text="OK", command=validate_roi).pack(pady=5)

    def on_toggle_save(self):
        "Active ou désactive les champs de sauvegarde en fonction de l'état du checkbox"
        if self.save_var.get():
            self.out_entry.config(state="normal")
            self.out_button.config(state="normal")
        else:
            self.out_entry.config(state="disabled")
            self.out_button.config(state="disabled")
    
    def choose_output_dir(self):
        "Ouvre une boîte de dialogue pour choisir le dossier de sauvegarde"
        directory = filedialog.askdirectory(title="Choisir un dossier de sauvegarde")
        if directory:
            self.output_dir_var.set(directory)
    
    def on_select_roi(self, xmin, xmax):
        """Selection de la ROI"""
        if xmin > xmax:
            xmin, xmax = xmax, xmin
            self.roi_min = int(xmin)
            self.roi_max = int(xmax)
            self.roi_label.config(text=f"ROI: {xmin : .1f} - {xmax : .1f} channels")
        elif xmin< xmax : 
            self.roi_min = xmin
            self.roi_max = xmax
            self.roi_label.config(text=f"ROI: {xmin : .1f} - {xmax : .1f} channels")
        else : 
            self.roi_label.config(text=f"ROI non définie")
    
    def run_loop(self):
        scenarios = self.charger_config_loop()
        if not scenarios:
            messagebox.showerror("Erreur", "Aucun scénario chargé.")
            return

        # Dossier de sortie de la BOUCLE
        if self.save_var.get():
            # dossier choisi par l'utilisateur
            output_folder = self.output_dir_var.get()
            if not output_folder:
                messagebox.showerror("Erreur", "Aucun dossier de sortie sélectionné.")
                return
        else:
            # dossier temporaire interne
            output_folder = self.temp_dir

        os.makedirs(output_folder, exist_ok=True)

        self.log(f"Dossier de sortie boucle : {output_folder}")
        self.app_state["output_folder"] = output_folder

        try:
            Boucle_sans_variation(
                data_entry=scenarios,
                path_exit=output_folder,
                c_min=self.roi_min,
                c_max=self.roi_max,
                log_callback=self.log,
            )
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur dans la boucle :\n{e}")
            return

        # important : mettre à jour output_dir_var pour les étapes suivantes
        self.output_dir_var.set(output_folder)
        self.has_boucle = True
        self.update_excitation_uncertainty_in_appstate(output_folder)
        
    def update_excitation_uncertainty_in_appstate(self, folder):
        if not folder or not os.path.isdir(folder):
            return

        vals = []
        for fname in os.listdir(folder):
            if not fname.endswith(".xlsx"):
                continue

            path = os.path.join(folder, fname)
            try:
                df = pd.read_excel(path)
            except Exception:
                continue

            if {"N/C", "incertitudes"}.issubset(df.columns):
                nc = pd.to_numeric(df["N/C"], errors="coerce").to_numpy(dtype=float)
                u = pd.to_numeric(df["incertitudes"], errors="coerce").to_numpy(dtype=float)

                mask = np.isfinite(nc) & np.isfinite(u) & (np.abs(nc) > 1e-12)
                if np.any(mask):
                    vals.extend(np.abs(u[mask] / nc[mask]))

        value_pct = 100.0 * float(np.mean(vals)) if vals else None

        self.app_state["uncertainty_budget"]["excitation_curve"] = {
            "value_pct": value_pct,
            "source": "incertitudes / N/C",
            "comment": "Dispersion moyenne"
        }
    
    def update_sigmoid_uncertainty_in_appstate(self, fit_file):
        if not fit_file or not os.path.exists(fit_file):
            return

        try:
            df = pd.read_excel(fit_file)
        except Exception:
            return

        if not {"diff_height", "sigma_tot"}.issubset(df.columns):
            return

        h = pd.to_numeric(df["diff_height"], errors="coerce").to_numpy(dtype=float)
        s = pd.to_numeric(df["sigma_tot"], errors="coerce").to_numpy(dtype=float)

        mask = np.isfinite(h) & np.isfinite(s) & (np.abs(h) > 1e-12)
        rel = np.abs(s[mask] / h[mask]) if np.any(mask) else []

        value_pct = 100.0 * float(np.mean(rel)) if len(rel) else None

        self.app_state["uncertainty_budget"]["sigmoid_fit"] = {
            "value_pct": value_pct,
            "source": "sigma_tot / diff_height",
            "comment": "Robustesse du fit"
        }
     
    def refresh_from_app_state(self):
        """Synchronise les champs de l'onglet avec l'état partagé."""
        config_path = self.app_state.get("config_path")
        output_folder = self.app_state.get("output_folder")

        if config_path:
            self.config_path = config_path
            self.config_path_var.set(config_path)

        if output_folder:
            self.output_dir_var.set(output_folder)

    def run_remove_carbon_peak(self):
        if not self.has_boucle:
            messagebox.showerror("Erreur", "Lance d'abord la boucle de traitement.")
            return

        base_folder = self.output_dir_var.get()
        if not base_folder or not os.path.isdir(base_folder):
            messagebox.showerror("Erreur", f"Dossier de sortie invalide :\n{base_folder}")
            return

        ecenter = self.ecenter_var.get()
        window = self.window_var.get()
        half_width = self.half_width_var.get()

        outpufolder = os.path.join(base_folder, "filtered")
        imagefolder = os.path.join(outpufolder, "images")

        try:
            remove_peak_by_energy(
                input_folder=base_folder,
                output_folder=outpufolder,
                image_folder=imagefolder,
                log_callback=self.log,
                ecenter=ecenter,
                window=window,
            )
            self.has_peak_remove = True
            self.log(f"Suppression du pic terminée pour tous les profils de {base_folder}")
        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"Une erreur est survenue lors de la suppression du pic de carbon build-up :\n{e}",
            )
            
    def run_fit(self):
        if not self.has_boucle:
            messagebox.showerror("Erreur", "Lance d'abord la boucle de traitement.")
            return

        base_folder = self.output_dir_var.get()
        if not base_folder or not os.path.isdir(base_folder):
            messagebox.showerror("Erreur", f"Dossier de sortie invalide :\n{base_folder}")
            return

        if self.has_peak_remove:
            inputfolder = os.path.join(base_folder, "filtered")
        else:
            inputfolder = base_folder
        
        self.update_sigmoid_uncertainty_in_appstate(os.path.join(inputfolder, "fit_results.xlsx"))
        
        if not os.path.isdir(inputfolder):
            messagebox.showerror("Erreur", f"Dossier d'entrée pour le fit introuvable :\n{inputfolder}")
            return

        outpufolder = os.path.join(inputfolder, "fit_sigmoid")

        try:
            fit_to_profile(
                folder_input=inputfolder,
                output_path=outpufolder,
                log_callback=self.log,
            )
        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"Une erreur est survenue lors du fit sigmoïde :\n{e}",
            )
            
