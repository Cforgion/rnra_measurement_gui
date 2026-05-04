import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os

# Adapter l'import à ta structure de projet
from core.file_io import convert_mpa_folder  # [file:16]

class MPAConvertTab(ttk.Frame):
    """Onglet pour convertir des fichiers .mpa en .txt"""

    def __init__(self, parent, app_state):
        super().__init__(parent)

        self.app_data = app_state
        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.config_path = tk.StringVar()
        self.config_path = tk.StringVar()      # chemin vers l'Excel minimal
        self.group_root = tk.StringVar()  
        self._build_ui()

    def _build_ui(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # --- Choose Configuration file ---
        config_fram = ttk.LabelFrame(main_frame, text="Configuration file")
        config_fram.pack(fill="x", padx=5, pady=5)

        # Dossier d'entrée
        row1 = ttk.Frame(config_fram)
        row1.pack(fill="x", padx=5, pady=2)
        

        ttk.Label(row1, text="config Excel:").pack(side="left")
        ttk.Entry(row1, 
                  textvariable=self.config_path
                  , width=45, 
                  state ='readonly').pack(side="left", padx=5, fill="x", expand=True)
        ttk.Button(row1, text="Browse", command=self.browse_config).pack(side="left")
        row_grp = ttk.Frame(config_fram)
        row_grp.pack(fill="x", padx=5, pady=2)

        ttk.Label(row_grp, text="day (racine sample_name) :").pack(side="left")
        ttk.Entry(row_grp, textvariable=self.group_root, width=15).pack(
            side="left", padx=5
        )
        ttk.Label(row_grp, text="ex: 250317").pack(side="left")

        # output folder
        row2 = ttk.Frame(config_fram)
        row2.pack(fill="x", padx=5, pady=2)

        ttk.Label(row2, text="Folder exit for .txt :").pack(side="left")
        ttk.Entry(row2, textvariable=self.output_folder, width=45).pack(
            side="left", padx=5, fill="x", expand=True
        )
        ttk.Button(row2, text="Parcourir", command=self.browse_output).pack(side="left")

        # --- Ligne 2 : bouton + progression ---
        run_frame = ttk.LabelFrame(main_frame, text="Conversion")
        run_frame.pack(fill="x", padx=5, pady=5)

        self.run_button = ttk.Button(
            run_frame,
            text="▶ convert .mpa → .txt",
            command=self.run_conversion
        )
        self.run_button.pack(fill="x", padx=5, pady=5)

        # barre de progression
        self.progress = ttk.Progressbar(run_frame, mode="determinate")
        self.progress.pack(fill="x", padx=5, pady=(0, 5))

        self.status_label = ttk.Label(run_frame, text="En attente…", foreground="gray")
        self.status_label.pack(padx=5, pady=(0, 5))

        # --- Ligne 3 : log ---
        log_frame = ttk.LabelFrame(main_frame, text="Journal")
        log_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.log_text = tk.Text(log_frame, height=10, wrap="word")
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        scrollbar.pack(side="right", fill="y", padx=(0, 5), pady=5)

    # --- Callbacks UI ---
    def browse_config(self):
        path = filedialog.askopenfilename(
        title="Choisir le fichier de configuration (Excel de base)",
        filetypes=[("Excel", "*.xlsx *.xls"), ("Tous", "*.*")]
        )
        if path:
            self.config_path.set(path)
            self.app_data["config_path"] = path
            self.log(f"Config chargée : {path}")

    def browse_input(self):
        folder = filedialog.askdirectory(title="Choisir le dossier contenant les .mpa")
        if folder:
            self.input_folder.set(folder)

    def browse_output(self):
        folder = filedialog.askdirectory(title="Choisir le dossier de sortie pour les .txt")
        if folder:
            self.output_folder.set(folder)

    def log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)

    # --- Lancement de la conversion ---
    def run_conversion(self):
        def progress_callback(current, total, filename, status):
            self.progress["maximum"] = total
            self.progress["value"] = current
            msg = f"[{current}/{total}] {filename} : {status}"
            self.status_label.config(text=msg)
            self.log(msg)
            self.update_idletasks()
    
        base = self.output_folder.get().strip()
        group = self.group_root.get().strip()
        config_path = self.app_data.get("config_path")
        self.app_data["group"] = group
        # 1) Vérifications de base
        if not config_path or not os.path.exists(config_path):
            messagebox.showerror("Erreur", "Aucun fichier de configuration chargé.")
            return
    
        if not group:
            messagebox.showwarning(
                "Jour manquant",
                "Entrez la racine du jour (ex: 250317) dans le champ 'day'."
            )
            return
    
        # 2) Lire l'Excel et récupérer le mpa_folder pour ce jour
        import pandas as pd
        try:
            df = pd.read_excel(config_path)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de lire le fichier de config :\n{e}")
            return
    
        # Assurer group_root
        if "group_root" not in df.columns:
            df["group_root"] = df["sample_name"].astype(str).str.split("_").str[0]
    
        mask = df["group_root"].astype(str) == group
        if not mask.any():
            messagebox.showerror(
                "Erreur",
                f"Aucune ligne avec group_root = {group} dans le fichier de config."
            )
            return
    
        # On suppose un seul mpa_folder pour ce jour
        mpa_folders = df.loc[mask, "mpa_folder"].dropna().unique()
        if len(mpa_folders) == 0:
            messagebox.showerror(
                "Erreur",
                f"Aucun mpa_folder défini pour le jour {group}."
            )
            return
        in_dir = mpa_folders[0]
    
        if not os.path.isdir(in_dir):
            messagebox.showerror(
                "Erreur",
                f"Dossier .mpa invalide ou introuvable :\n{in_dir}"
            )
            return
        
        # 3) Préparer le dossier de sortie .txt
        if not base:
            base = self.app_data["temp_folder"]
        
        #base = self.output_folder.get()     
        out_dir =os.path.join(base,str(group))
        os.makedirs(out_dir, exist_ok=True)
        self.output_folder.set(base)
        self.app_data["output_folder"] = out_dir
        
        # 4) Conversion
        self.log(f"Début conversion (jour {group}) : {in_dir} → {out_dir}")
        self.status_label.config(text="Conversion en cours…", foreground="blue")
        self.run_button.config(state="disabled")
        self.progress["value"] = 0
    
        results = convert_mpa_folder(in_dir, out_dir, progress_callback=progress_callback)
        self.app_data["conversion_results"] = results
    
        # Résumé
        if results["success"]:
            self.status_label.config(
                text=f"Terminé : {results['converted']} fichier(s) converti(s)",
                foreground="green"
            )
            self.log("Conversion terminée.")
        else:
            self.status_label.config(text="Terminé avec erreurs", foreground="red")
            self.log("Conversion terminée avec erreurs.")
        for err in results["errors"]:
            self.log(f"ERREUR : {err}")
    
        # 5) Mise à jour du config : data_folder pour ce jour
        try:
            # relecture ou réutilisation de df
            if "data_folder" not in df.columns:
                df["data_folder"] = ""
    
            df.loc[mask, "data_folder"] = out_dir
            df.to_excel(config_path, index=False)
            self.log(
                f"Config mis à jour : data_folder = {out_dir} pour jour {group}."
            )
        except Exception as e:
            self.log(f"Erreur mise à jour config : {e}")
    
        self.run_button.config(state="normal")
