import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import os
from xml.parsers.expat import model
from matplotlib.figure import Figure
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.widgets import SpanSelector
from tkinter.scrolledtext import ScrolledText
from scipy import stats
import seaborn as sns
import statsmodels.api as sm
from statsmodels.formula.api import ols

import pingouin as pg

# ✅ AJOUTER CECI AVANT LES IMPORTS LOCAUX
import sys

from scipy import stats
# Remonter au dossier parent (src) puis accéder à utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class anova_tab(ttk.Frame):
    def __init__(self, parent, app_state):
        super().__init__(parent)
        self.app_state = app_state
        self.temp_dir = os.path.join(os.path.dirname(__file__), "..","temp")
        os.makedirs(self.temp_dir, exist_ok=True)
        self.temp_dir = os.path.abspath(self.temp_dir)
        self.config_path = self.app_state.get("config_path", None)
        self.config_path_var = tk.StringVar(value=self.config_path or "")
        self.qqtot = tk.BooleanVar(value=False)
        self.qqgroup = tk.BooleanVar(value=False)
        self.histo = tk.BooleanVar(value=False)
        self.boxplot = tk.BooleanVar(value=False)
        self.violinplot = tk.BooleanVar(value=False)
        self.group_col = tk.StringVar(value="group")
        self.val_col = tk.StringVar(value="value_name (from loop then diff_height)")
        self.save_var = tk.BooleanVar(value=False)
        self.output_dir_var = tk.StringVar(value=self.temp_dir)
        self.data = None
        
        self.setup_ui()
    def setup_ui(self):
        # Frame diviser en 2"
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Gauche
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side='left', fill='y', padx=5)
        
        # Boucle_frame 
        boucle_Frame = ttk.LabelFrame(left_frame, text="Analyse Statistique ANOVA")
        boucle_Frame.pack(fill='x', pady=5)
        #Frame de chargement des fichier 
        files_frame = ttk.LabelFrame(boucle_Frame, text="1. Charger les fichiers")
        files_frame.pack(fill='x', pady=5) 
        ttk.Entry(files_frame,
                  textvariable =self.config_path_var,
                  state ="readonly",
                  width = 50
                  ). pack(side = 'left', fill ='x', expand =True, padx = 5 ,pady = 5)
               
        ttk.Button(files_frame, text="Charger le fichier excel à analyser",
                   command=self.load_config).pack(side = 'left', padx=5, pady=5)
        
        norm_frame = ttk.LabelFrame(boucle_Frame, text ='2. plot normalisation visual test')
        norm_frame.pack(fill='x', pady=5)
        ttk.Checkbutton(
            norm_frame,
            text ="QQ plot global",
            variable =self.qqtot,
            command =self.update_options
        ).pack(anchor='w', padx=5, pady=2)
        ttk.Checkbutton(
            norm_frame,
            text ="QQ plot by group",
            variable =self.qqgroup,
            command =self.update_options
        ).pack(anchor='w', padx=5, pady=2)
        
        homo_frame = ttk.LabelFrame(boucle_Frame, text ='3. plot homogeneity visual test')
        homo_frame.pack(fill='x', pady=5)
        ttk.Checkbutton(
            homo_frame,
            text ="Histogram of residuals by group",
            variable =self.histo,
            command =self.update_options
        ).pack(anchor='w', padx=5, pady=2)
        ttk.Checkbutton(
            homo_frame,
            text ="Box plot of residuals by group",
            variable =self.boxplot,
            command =self.update_options
        ).pack(anchor='w', padx=5, pady=2)
        ttk.Checkbutton(
            homo_frame,
            text ="violin plot of residuals by group",
            variable =self.violinplot,
            command =self.update_options
        ).pack(anchor='w', padx=5, pady=2)
        
        col_frame = ttk.LabelFrame(boucle_Frame, text = '4. columns selection')
        col_frame.pack(fill='x', pady=5)
        
        self.group_combo = ttk.Combobox(col_frame, textvariable=self.group_col)
        self.group_combo.pack(fill='x', padx=5, pady=2)

        self.val_combo = ttk.Combobox(col_frame, textvariable=self.val_col)
        self.val_combo.pack(fill='x', padx=5, pady=2)
        
        out_frame = ttk.LabelFrame(boucle_Frame, text="5. Sauvegarde des résultats")
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
        
        ttk.Button(boucle_Frame, text="▶ Lancer ANOVA",
           command=self.anova).pack(fill='x', padx=10, pady=8) 
        
        vis_frame = ttk.LabelFrame(boucle_Frame,text =" Option de visualisation des plots choisi")
        vis_frame.pack(fill='x', pady=5)
        
        ttk.Button(
            vis_frame,
            text ="Afficher un plot choisi",
            command =self.load_result_file,
        ).pack(anchor='w', padx =5, pady = 2)

        
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side='right', fill='both', expand=True)
        
        # Figure Matplotlib
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("residuals")
        self.ax.set_ylabel("groups")
        self.ax.set_title("plot")
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        toolbar = NavigationToolbar2Tk(self.canvas, right_frame)
        
        results_frame = ttk.LabelFrame(boucle_Frame, text="Détails")
        results_frame.pack(fill='both', expand=True, pady=5)
        # ScrolledText pour afficher les résultats du fit
        self.results_text = tk.Text(results_frame, width=35, wrap=tk.WORD)
        scollbar = ttk.Scrollbar(results_frame, command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scollbar.set)

        self.results_text.pack(side='left', fill='both', expand=True, padx=(5,0), pady=5)
        scollbar.pack(side='right', fill='y', padx=(0,5), pady=5)
        
        #self.refresh_from_app_state()
        
    def on_ignore_group_checkbox(self, event):
        self.ignore_group_text.SetEditable(self.check_ignore_group.GetValue())
    
    def load_result_file(self):
        """Permet de visualiser une image de résultat (plots ANOVA)"""

        initial_dir = self.output_dir_var.get() if self.output_dir_var.get() else os.getcwd()

        filename = filedialog.askopenfilename(
            title="Choisir une image de résultat",
            initialdir=initial_dir,
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg"),
                ("All files", "*.*"),
            ],
        )

        if not filename:
            return

        try:
            
            img = plt.imread(filename)

            self.ax.clear()
            self.ax.imshow(img)
            self.ax.axis("off")
            self.ax.set_title(f"{os.path.basename(filename)}")

            self.canvas.draw()

            self.log(f"🖼️ Image chargée : {filename}")

        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"Impossible de lire l'image :\n{e}",
            )
      
    def log(self, message):
        self.results_text.insert(tk.END, message + "\n")
        self.results_text.see(tk.END)
    
    def load_config(self):
        filename = filedialog.askopenfilename(
        title="Choisir le fichier Excel de configuration",
        filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if not filename:
            return

        self.config_path = filename
        self.config_path_var.set(filename)
        self.app_state["config_path"] = filename
        
        try:
            # 🔥 LECTURE DU FICHIER
            self.data = pd.read_excel(filename)
            cols = list(self.data.columns)
            self.group_combo['values'] = cols
            self.val_combo['values'] = cols

            # ✅ log
            self.log(f"📂 Fichier chargé : {filename}")
            self.log(f"📊 Colonnes détectées : {list(self.data.columns)}")

            # (optionnel mais très utile 👇)
            # mettre à jour les colonnes automatiquement
            if len(self.data.columns) >= 2:
                self.group_col.set(self.data.columns[0])
                self.val_col.set(self.data.columns[1])

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lecture Excel :\n{e}")
    
    def on_toggle_save(self):
        "Active ou désactive les champs de sauvegarde en fonction de l'état du checkbox"
        if self.save_var.get():
            self.out_entry.config(state="normal")
            self.out_button.config(state="normal")
        else:
            self.out_entry.config(state="disabled")
            self.out_button.config(state="disabled")
    
    def anova(self):
        if self.data is None:
            self.log("❌ Aucun fichier chargé")
            return

        try:
            val_col = self.val_col.get()
            group_col = self.group_col.get()
            data = self.data.copy()

            data[val_col] = pd.to_numeric(data[val_col], errors="coerce")
            avant = len(data)
            data = data.dropna(subset=[val_col, group_col])
            apres = len(data)

            if avant != apres:
                self.log(f"⚠️ {avant - apres} lignes supprimées (NaN ou non-numériques)")

            if data.empty:
                self.log("❌ Aucune donnée valide après nettoyage")
                return

            data_clean = data[[val_col, group_col]].copy()
            data_clean.columns = ["value", "group"]
            model = ols("value ~ C(group)", data=data_clean).fit()
            anova_table = sm.stats.anova_lm(model, typ=2)
            residus = model.resid

            self.log("✅ ANOVA calculée")
            self.log(str(anova_table))

            factor_row = "C(group)"
            if factor_row not in anova_table.index:
                raise KeyError(f"Aucune ligne dans anova_table ne correspond à '{factor_row}'")

            ss_inter = anova_table.loc[factor_row, "sum_sq"]
            df_inter = anova_table.loc[factor_row, "df"]
            ms_inter = ss_inter / df_inter

            cm_resid = (
                anova_table.loc["Residual", "mean_sq"]
                if "mean_sq" in anova_table.columns
                else anova_table.loc["Residual", "sum_sq"] / anova_table.loc["Residual", "df"]
            )

            n_per_group = data_clean.groupby("group").size().mean()
            ms_intra = cm_resid
            u_intra = np.sqrt(ms_intra)

            if ms_inter > ms_intra:
                u_inter = np.sqrt((ms_inter - ms_intra) / n_per_group)
            else:
                u_inter = 0.0

            u_total = np.sqrt(u_intra**2 + u_inter**2)
            y_mean = data_clean["value"].mean()
            u_rel = u_total / y_mean if y_mean != 0 else np.nan
            u_rel_percent = 100 * u_rel

            shapiro = stats.shapiro(residus)
            p_shapiro = shapiro.pvalue

            jb = stats.jarque_bera(residus)
            stat_bera = jb.statistic
            p_bera = jb.pvalue

            self.log(f"Shapiro p-value = {p_shapiro:.4f}")
            self.log(f"Jarque-Bera p-value = {p_bera:.4f}")
            self.log(f"Incertitude inter-groupes (u_inter) : {u_inter:.4g}")
            self.log(f"Incertitude intra-groupes (u_intra) : {u_intra:.4g}")
            self.log(f"Incertitude totale (u_total) : {u_total:.4g}")
            self.log(f"Incertitude relative (%) : {u_rel_percent:.2f}%")
            # 🔹 Groupes pour tests non paramétriques
            groupes = [group[val_col].values for _, group in data.groupby(group_col)]
    
            # 🔹 Choix du test
            if p_shapiro > 0.05 and p_bera > 0.05:
                self.log("✅ ANOVA paramétrique valide")
                result = anova_table
            else:
                self.log("⚠️ Non normal → Kruskal-Wallis")
                stat_kruskal, p_kruskal = stats.kruskal(*groupes)
                result = (stat_kruskal, p_kruskal)
                self.log(f"Kruskal stat={stat_kruskal:.4f}, p={p_kruskal:.4f}")

            # 🔹 Sauvegarde
            if self.save_var.get():
                path = os.path.join(self.output_dir_var.get(), "anova_results.txt")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(str(result))
                    f.write("\n\n")
                    f.write(f"Incertitude inter-groupes (u_inter) : {u_inter:.4g}\n")
                    f.write(f"Incertitude intra-groupes (u_intra) : {u_intra:.4g}\n")
                    f.write(f"Incertitude totale (u_total) : {u_total:.4g}\n")
                    f.write(f"Incertitude relative (%) : {u_rel_percent:.2f}%\n")
                self.log(f"💾 Résultats sauvegardés : {path}")

            # =========================
            # 📊 PLOTS
            # =========================

            # QQ plot global
            if self.qqtot.get():
                pg.qqplot(residus, dist="norm", confidence=0.95,alpha=0.7, color="blue")
                plt.title("Q-Q plot global")
                if self.save_var.get():
                    path = os.path.join(self.output_dir_var.get(), "qqplot_global.png")
                    plt.savefig(path)
                    self.log(f"📐 Sauvegardé : {path}")
                plt.show(block=False)

            # QQ plot par groupe
            if self.qqgroup.get():
                data["residu"] = residus
                groupes_uniques = data[group_col].unique()
                n = len(groupes_uniques)
                n_cols = 3
                n_rows = int(np.ceil(n / n_cols))

                fig, axes = plt.subplots(n_rows, n_cols, figsize=(5*n_cols, 5*n_rows))
                axes = axes.flatten()

                for i, g in enumerate(groupes_uniques):
                    resid = data[data[group_col] == g]["residu"]
                    pg.qqplot(resid, dist="norm", confidence=0.95, ax=axes[i], alpha=0.6, color="blue")
                    axes[i].set_title(str(g))

                for j in range(i+1, len(axes)):
                    fig.delaxes(axes[j])

                if self.save_var.get():
                    path = os.path.join(self.output_dir_var.get(), "qqplot_group.png")
                    plt.savefig(path)
                    self.log(f"📐 Sauvegardé : {path}")

                plt.show(block=False)

            # Boxplot
            if self.boxplot.get():
                plt.figure()
                sns.boxplot(x=data[group_col], y=residus)
                plt.title("Boxplot des résidus")

                if self.save_var.get():
                    path = os.path.join(self.output_dir_var.get(), "boxplot.png")
                    plt.savefig(path)
                    self.log(f"📦 Sauvegardé : {path}")

                plt.show(block=False)

            # Histogramme
            if self.histo.get():
                plt.figure()
                plt.hist(residus, bins=20)
                plt.title("Histogramme des résidus")

                if self.save_var.get():
                    path = os.path.join(self.output_dir_var.get(), "histogram.png")
                    plt.savefig(path)
                    self.log(f"📊 Sauvegardé : {path}")

                plt.show(block=False)

            # Violinplot
            if self.violinplot.get():
                plt.figure()
                sns.violinplot(x=data[group_col], y=residus)
                plt.title("Violinplot des résidus")

                if self.save_var.get():
                    path = os.path.join(self.output_dir_var.get(), "violinplot.png")
                    plt.savefig(path)
                    self.log(f"🎻 Sauvegardé : {path}")

                plt.show(block=False)

            return result

        except Exception as e:
            self.log(f"❌ Erreur ANOVA : {e}") 
    
    def choose_output_dir(self):
        """Ouvre une boîte de dialogue pour choisir le dossier de sauvegarde"""
        directory = filedialog.askdirectory(title="Choisir un dossier de sauvegarde")
        if directory:
            self.output_dir_var.set(directory)
       
    def update_options(self):
        self.options = {
        "qqtot": self.qqtot.get(),
        "qqgroup": self.qqgroup.get(),
        "histo": self.histo.get(),
        "boxplot": self.boxplot.get(),
        "violinplot": self.violinplot.get(),
        "save": self.save_var.get()
    }