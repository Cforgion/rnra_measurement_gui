import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

# ✅ AJOUTER CECI AVANT LES IMPORTS LOCAUX
import sys
# Remonter au dossier parent (src) puis accéder à utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.calibration import load_spectrum, fit_gaussian_in_zone, calibrate_linear, gaussienne
from core.etallonnage import deltaE_global_from_polyfit

class CalibrationTab(ttk.Frame):
    """Onglet d'étalonnage pour l'application RNRA"""
    
    def __init__(self, parent,app_state):
        super().__init__(parent)
        
        # Variables
        self.app_state = app_state
        self.spectrum_data = None
        self.channels = None
        self.counts = None
        self.deadtime = None
        self.selected_range = None
        
        # Stockage des pics  identifiés
        self.peaks = []
        
        # Configure l'interface
        self.setup_ui()
    
    def setup_ui(self):
        """Configure l'interface de l'onglet"""
        
        # Frame principale divisée en 2: contrôles à gauche, graphique à droite
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # --- FRAME GAUCHE: Contrôles ---
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side='left', fill='y', padx=5)
        
        # Chargement fichiers
        files_frame = ttk.LabelFrame(left_frame, text="Fichiers")
        files_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(
            files_frame, 
            text="📁 Charger spectre",
            command=self.load_spectrum
        ).pack(fill='x', padx=5, pady=5)
        
        self.file_label = ttk.Label(files_frame, text="Aucun fichier", foreground="gray")
        self.file_label.pack(padx=5, pady=2)
        
        self.deadtime_label = ttk.Label(files_frame, text="", foreground="blue")
        self.deadtime_label.pack(padx=5, pady=2)
        
        # Sélection de zone
        selection_frame = ttk.LabelFrame(left_frame, text="Sélection de pic")
        selection_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Label(selection_frame, text="Cliquez sur le graphique").pack(padx=5, pady=5)
        
        self.range_label = ttk.Label(
            selection_frame, 
            text="Aucun pic sélectionnée",
            foreground="gray"
        )
        self.range_label.pack(padx=5, pady=5)
        
        # Energie de reference
        ttk.Label(
            selection_frame,
            text="Energie(keV)"
        ).pack(padx=5, pady=(10,2))
        self.energy_entry = ttk.Entry(selection_frame, width=15)
        self.energy_entry.pack(padx=5, pady=2)
        # Bouton d'action
        btn_frame = ttk.Frame(selection_frame)
        btn_frame.pack(fill='x', padx=5, pady=5)
        
        self.fit_button = ttk.Button(
            btn_frame,
            text="Fit gaussien",
            command=self.fit_selected_peak,
            state='disabled'
        )
        self.fit_button.pack(side='left', fill='x', expand=True, padx=2)
        
        ttk.Button(
            selection_frame,
            text="🔄 Réinitialiser sélection",
            command=self.reset_selection
        ).pack(fill='x', padx=5, pady=5)
        
        # Liste des pics identifies
        peaks_frame = ttk.LabelFrame(left_frame, text="Pics identifiés")
        peaks_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Treeview pour afficher les pics
        columns =('Canal', 'Energie (keV)')
        self.peaks_tree = ttk.Treeview(
            peaks_frame,
            columns=columns,
            show='tree headings',
            height=6
        )
        self.peaks_tree.heading('#0', text='#')
        self.peaks_tree.column('#0', width=30, stretch=False)
        self.peaks_tree.heading('Canal', text='Canal')
        self.peaks_tree.column('Canal', width=80, stretch=False)
        self.peaks_tree.heading('Energie (keV)', text='Energie (keV)')
        self.peaks_tree.column('Energie (keV)', width=80, stretch=False)
        self.peaks_tree.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Bouton pour gerer les pics
        peaks_btn_frame = ttk.Frame(peaks_frame)
        peaks_btn_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(
            peaks_btn_frame,
            text="❌ Supprimer pic sélectionné",
            command=self.delete_selected_peak
        ).pack(fill='x', padx=2,side ='left', expand=True)
        
        ttk.Button(
            peaks_btn_frame,
            text="❌ Tout supprimer",
            command=self.clear_all_peaks
        ).pack(fill='x', padx=2, side='right', expand=True)
        
        # Calibration
        calib_frame =ttk.LabelFrame(left_frame, text="Calibration")
        calib_frame.pack(fill='x', padx=5, pady=5)
        
        self.calib_button = ttk.Button(
            calib_frame,
            text="🎯 Lancer calibration",
            command=self.perform_calibration,
            state='disabled'
        )
        self.calib_button.pack(fill='x', padx=5, pady=5)
        
        self.calib_result_label = ttk.Label(
            calib_frame,
            text="Minimum 2 pics requis",
            foreground="gray",
            wraplength=220
        )
        self.calib_result_label.pack(padx=5, pady=5)
        
        # ---Frame Centre: Graphique ---
        center_frame = ttk.Frame(main_frame)
        center_frame.pack(side='left', fill='both', expand=True, padx=5)
        
        # figure matplotlib
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.ax.set_xlabel('Canal')
        self.ax.set_ylabel('Coups')
        self.ax.set_title('Spectre RNRA')
        self.ax.grid(True, alpha=0.3)
        
         # Canvas pour afficher le graphique dans Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, center_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Toolbar matplotlib (zoom, pan, etc.)
        toolbar = NavigationToolbar2Tk(self.canvas, center_frame)
        toolbar.update()
        """
        # Sélecteur de zone interactif
        self.span = SpanSelector(
            self.ax,
            self.on_select,
            'horizontal',
            useblit=True,
            props=dict(alpha=0.3, facecolor='red'),
            interactive=True,
            drag_from_anywhere=True
        )
        """
        self.cid_click =self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        
        # --- FRAME DROITE: Fit gaussien ---
        right_frame = ttk.Frame(main_frame, width=300)
        right_frame.pack(side='right', fill='both', padx=5)
        right_frame.pack_propagate(False)
        
        results_frame = ttk.LabelFrame(left_frame, text="Détails")
        results_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # ScrolledText pour afficher les résultats du fit
        self.results_text = tk.Text(results_frame, width=35, wrap=tk.WORD)
        scollbar = ttk.Scrollbar(results_frame, command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scollbar.set)
        
        self.results_text.pack(side='left', fill='both', expand=True, padx=(5,0), pady=5)
        scollbar.pack(side='right', fill='y', padx=(0,5), pady=5)
        
        # Bouton pour exporter les résultats
        ttk.Button(
            right_frame,
            text="💾 Exporter résultats",
            command =self.export_results
        ).pack(fill='x', padx=5, pady=5)

    def compute_half_width(self, center):
        """ Retourne la demi - largeur en fonction de la position du pic ( en cannaux)"""
        if 150<= center <=250 :
            return 38
        elif 300<= center <= 400 :
            return 25
        elif 350<= center <=450 :
            return 25
        elif 1300 <=center <= 1500:
            return 58
        else :
            return 40
    
    def on_click(self, event):
        """ Selectionner un pic pa un clic simple sur le graphique"""
        # ignore les clics en dehors de l'axe
        if event.inaxes != self.ax:
            return

        if self.channels is None or self.counts is None:
            return 
        
        center = float(event.xdata)
        half_width =self.compute_half_width(center)

        self.selected_range={
            "center": center,
            "width": half_width
        }
        text = f"center: {center:.1f}, width: ±{half_width:.1f}"
        self.range_label.config(text=text, foreground="green")
        self.fit_button.config(state='normal')
        
    def load_spectrum(self):
        """Charge et affiche un spectre"""
        filename = filedialog.askopenfilename(
            title="Sélectionner un spectre",
            filetypes=[
                ("Fichiers texte", "*.txt"),
                ("Tous les fichiers", "*.*")
            ]
        )
        
        if filename:
            result = load_spectrum(filename)
            
            if result['success']:
                self.channels = result['channels']
                self.counts = result['counts']
                self.deadtime = result.get('deadtime', 1.0)
                
                # Affiche le spectre
                self.plot_spectrum()
                
                # Update labels
                basename = os.path.basename(filename)
                self.file_label.config(text=basename, foreground="green")
                # Update labels
                basename = os.path.basename(filename)
                self.file_label.config(text=basename, foreground="green")
                self.results_text.insert(tk.END, f"✓ Spectre chargé: {basename}\n")
                self.results_text.insert(tk.END, f"  Nombre de canaux: {len(self.channels)}\n\n")
              
                if self.deadtime != 1.0:
                    self.deadtime_label.config(text=f"Dead time: {self.deadtime:.4f}")
                
                self.results_text.insert(tk.END, f"✓ Spectre chargé: {basename}\n")
                self.results_text.insert(tk.END, f"  Canaux: {len(self.channels)}\n")
                self.results_text.insert(tk.END, f"  Dead time: {self.deadtime:.4f}\n\n")
                self.results_text.see(tk.END)    
                
            else:
                messagebox.showerror("Erreur", f"Erreur de chargement:\n{result['error']}")
 
    def plot_spectrum(self):
        """Affiche le spectre et les pics identifiés"""
        self.ax.clear()
        
        if self.channels is not None and self.counts is not None:
            # Spectre
            self.ax.plot(
                self.channels, 
                self.counts, 
                'b-', 
                linewidth=0.8,
                label='Spectre',
                alpha=0.7
            )
            
            # Pics identifiés
            for i, peak in enumerate(self.peaks):
                fit_res = peak['fit_result']
                center = fit_res['centroid']
                sigma = fit_res['sigma']
                energy = peak['energy']
                 # Marque le centre
                self.ax.axvline(
                    center, 
                    color='green', 
                    linestyle='--', 
                    alpha=0.5,
                    label=f"Pic {i+1}: {energy} keV" if i < 3 else ""
                )
                
                # Affiche le fit gaussien
                x_fit = np.linspace(center - 3*sigma, center + 3*sigma, 200)
                y_fit = gaussienne(x_fit, fit_res['amplitude'], center, sigma,fit_res['b'],fit_res['c'])
                self.ax.plot(x_fit, y_fit, 'r-', linewidth=1.5, alpha=0.6)
            
            self.ax.set_xlabel('Canal')
            self.ax.set_ylabel('Coups')
            self.ax.set_title('Spectre RNRA - Étalonnage')
            self.ax.grid(True, alpha=0.3)
            if self.peaks:
                self.ax.legend(fontsize=8, loc='best')
        self.canvas.draw()
                     
    def on_select(self, xmin, xmax):
        """Callback quand une zone est sélectionnée"""
        if self.channels is None:
            return
        
        center = (xmin + xmax) / 2
        width = (xmax - xmin)/2
        
        self.selected_range = {'center':center, 'width':width}
        self.range_label.config(
            text=f"center: {center:.1f}, width: ±{width:.1f}",
            foreground="green"
        )
        self.fit_button.config(state='normal')
    
    def reset_selection(self):
        """Réinitialise la sélection"""
        self.selected_range = None
        self.range_label.config(text="Aucune pic sélectionnée", foreground="gray")
        self.fit_button.config(state='disabled')
        self.energy_entry.delete(0, tk.END)
    
    def fit_selected_peak(self):
        """Effectue un fit gaussien sur le pic sélectionnée."""
        if self.selected_range is None:
            messagebox.showwarning("Attention", "Sélectionnez d'abord un pic")
            return

        # Lire l'énergie de référence entrée par l'utilisateur
        energy_str = self.energy_entry.get().strip()
        if not energy_str:
            messagebox.showwarning("Attention", "Entrez l'énergie de référence (keV)")
            return

        try:
            energy = float(energy_str)
        except ValueError:
            messagebox.showerror("Erreur", "Énergie invalide")
            return

        # Appel de la fonction de fit importée depuis core.calibration
        result = fit_gaussian_in_zone(
            self.channels,
            self.counts,
            self.selected_range["center"],
            self.selected_range["width"]
        )

        if not result.get("success", False):
            messagebox.showerror("Erreur", f"Fit gaussien échoué:\n{result.get('error', 'Inconnu')}")
            return
        
        centroid = result["centroid"]
        sigma = result.get("sigma", float("nan"))
        amplitude = result.get("amplitude", float("nan"))
        # Essayer plusieurs noms pour l'erreur de centroïde
        centroid_error = result.get("error_centroid", 1.0) 
        # Stocker le pic
        peak_data = {
            "center": self.selected_range["center"],
            "width": self.selected_range["width"],
            "energy": energy,          # énergie saisie par l'utilisateur
            "fit_result": result,      # dict contenant centroid, sigma, amplitude, etc.
        }
        self.peaks.append(peak_data)

        idx = len(self.peaks)

        # Ajout dans le TreeView : canal et énergie
        self.peaks_tree.insert(
            "",
            "end",
            text=str(idx),
            values=(
                f"{result['centroid']:.2f}",   # canal (centroïde)
                f"{energy:.2f}",               # énergie du pic (PAS result['energy'])
            )
        )

        # Afficher des détails dans la zone de texte à droite
        self.results_text.insert(
            tk.END,
            (
                f"Pic {idx} :\n"
                f"  Canal  = {result['centroid']:.3f} ± {centroid_error:.3f}\n"
                f"  Énergie= {energy:.3f} keV\n"
                f"  Sigma  = {result.get('sigma', float('nan')):.3f}\n"
                f"  Amp.   = {result.get('amplitude', float('nan')):.1f}\n\n"
            )
        )
        self.results_text.see(tk.END)

        # Activer le bouton de calibration si assez de pics
        if len(self.peaks) >= 2:
            self.calib_button.config(state="normal")
            self.calib_result_label.config(
                text=f"{len(self.peaks)} pics prêts pour calibration",
                foreground="green"
            )

        # Mettre à jour le graphique
        self.plot_spectrum()

    def delete_selected_peak(self):
        """Supprime le pic sélectionné dans le Treeview et dans self.peaks."""
        selected = self.peaks_tree.selection()
        if not selected:
            return  # rien de sélectionné

        item_id = selected[0]

        # Le texte de la colonne #0 contient l’index affiché (1, 2, 3, ...)
        index_str = self.peaks_tree.item(item_id, "text")
        try:
            idx = int(index_str) - 1  # self.peaks est indexé à partir de 0
        except ValueError:
            # Si jamais le texte n’est pas un entier, on peut fallback sur l’ordre visuel
            idx = self.peaks_tree.index(item_id)

        # Supprimer dans la liste de pics si l’index est valide
        if 0 <= idx < len(self.peaks):
            del self.peaks[idx]

        # Supprimer la ligne du Treeview
        self.peaks_tree.delete(item_id)

        # Re-numéroter les lignes restantes pour garder # cohérent
        for i, iid in enumerate(self.peaks_tree.get_children(), start=1):
            self.peaks_tree.item(iid, text=str(i))

        # Mettre à jour le graphique
        self.plot_spectrum()

    def clear_all_peaks(self):
        """Efface tous les pics identifiés."""
        self.peaks.clear()  # vide la liste
        # supprimer toutes les lignes du Treeview
        for iid in self.peaks_tree.get_children():
            self.peaks_tree.delete(iid)

        # désactiver le bouton de calibration et réinitialiser le label
        self.calib_button.config(state="disabled")
        self.calib_result_label.config(
            text="Minimum 2 pics requis",
            foreground="gray"
        )

        # mettre à jour le graphique
        self.plot_spectrum()

    def perform_calibration(self):
        """Lance la calibration linéaire à partir des pics sélectionnés."""
        if len(self.peaks) < 2:
            messagebox.showwarning(
                "Calibration",
                "Au moins 2 pics sont nécessaires pour la calibration."
            )
            return

        # Extraire les canaux (centroides) et les énergies associées
        channels = []
        energies = []
        errors_centroid =[]
        for peak in self.peaks:
            fit_res = peak["fit_result"]
            channels.append(fit_res["centroid"])
            energies.append(peak["energy"])
            errors_centroid.append(fit_res.get("centroid_error", 1.0))
        channels = np.array(channels, dtype=float)
        energies = np.array(energies, dtype=float)
        errors_centroid = np.array(errors_centroid, dtype=float)
           
        try:
            # adapte à la signature exacte de calibrate_linear
            # exemple: a, b, R2, y_conv, cov = calibrate_linear(channels, energies)
            calib_res = calibrate_linear(channels, energies,errors_centroid)
        except Exception as e:
            messagebox.showerror("Erreur calibration", str(e))
            return

        # Déballage selon ce que renvoie vraiment calibrate_linear
        # Si tu sais que c’est (a, b, R2, yconv, cov) comme dans etalonnageavecerreuretR2 [file:13],
        # alors:
        a = calib_res['a']
        b = calib_res['b']
        R2 = calib_res['R2']
        err_a = calib_res['error_a']
        err_b = calib_res['error_b']
        cov = calib_res.get('covariance')
        
        delta_E =deltaE_global_from_polyfit(
            p =np.array([a,b]),
            cov =cov,
            a_coef =a,
            x_points= channels,
            sigma_x= errors_centroid
        )
        
        deltaE_rms = delta_E["deltaE_rms"]
        rel_rms_pct = delta_E["rel_rms_pct"]
        txt = (
            f"Calibration: E = {a:.5f} ± {err_a:.5f} * canal + {b:.2f} ± {err_b:.2f}\n"
            f"R² = {R2:.4f}\n"
            f"Erreur relative RMS ≈ {rel_rms_pct:.2f} %"
        )
        self.calib_result_label.config(text=txt, foreground="green")

        # Sauvegarde dans l'état global si disponible
        if hasattr(self, "app_state"):
            self.app_state["calibration_results"] = {
                "a": a,
                "b": b,
                "R2": R2,
                "channels": channels,
                "energies": energies,
                "rel_rms_pct": rel_rms_pct,
            }
            self.app_state["uncertainty_budget"]["calibration"] = {
                "value_pct": rel_rms_pct,
                "source": "Calibration linéaire",
                "comment": "Erreur RMS relative"
                    }
    
    def export_results(self):
        """Exporte les pics et, si disponible, le résultat de calibration dans un fichier texte."""
        if not self.peaks:
            messagebox.showwarning(
                "Export",
                "Aucun pic à exporter."
            )
            return
         #1 Choix utilisateur
        filepath = filedialog.asksaveasfilename(
            title="Exporter les résultats",
            defaultextension=".txt",
            filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")]
         )
         
         # 2 si pas de filepath
        if not filepath:
            temp_dir = self.app_state.get('temp_folder', '.') if hasattr(self, "app_state") else "."
            os.makedirs(temp_dir, exist_ok=True)
            filepath = os.path.join(temp_dir, "calibration_results.txt")
        # 3 recupere la calibration    
        calib =None
        if hasattr(self, "app_state"):
            calib = self.app_state.get("calibration_results")
            
        try: 
            with open(filepath, 'w', encoding ="utf-8") as f:
                # pics 
                f.write("Pics identifiés pour l'etalonnage : \n")
                f.write("i\tcanal\tError_centroid \t signma \t amplitude \n")
                channels =[]
                energies =[]
                errors_centroid =[]
                
                for i, peak in enumerate(self.peaks, start=1):
                    fr = peak["fit_result"]
                    canal = fr.get("centroid", float("nan"))
                    error_centroid = fr.get("error_centroid", float("nan"))
                    sigma = fr.get("sigma", float("nan"))
                    amp = fr.get("amplitude", float("nan"))
                    E = peak.get("energy", float("nan"))
                    channels.append(canal)
                    energies.append(E)
                    errors_centroid.append(error_centroid)
                
                f.write(f"{i}\t {canal:3f}\t {error_centroid:.3f}\t {sigma:.3f}\t {amp:.1f}\n")
                f.write("\n")
                
                # calibration
                if calib and calib.get("sucess", False):
                    a = calib.get("a")
                    b = calib.get("b")
                    R2 = calib.get("R2")
                    rel_rms_pct = calib.get("rel_rms_pct")
                    f.write("Résultat de la calibration linéaire : \n")
                    f.write(f"E = {a:.5f} * canal + {b:.2f}\n")
                    f.write(f"R² = {R2:.4f}\n")
                    
                    f.write("Erreur global de l'etalonnage : \n")
                    f.write(f"Erreur relative  = {rel_rms_pct:.2f} % \n")
                
                else: 
                    f.write("Aucun résultat de calibration disponible.\n")
                    
            messagebox.showinfo("Export", f"Résultats exportés dans:\n{filepath}")
    
        except Exception as e:
            messagebox.showerror("Erreur export", str(e))
    
# Test rapide
if __name__ == "__main__":
    # Test load_spectrum
    result = load_spectrum(r"C:\Users\forgi\OneDrive - Université de Namur\MASTER 2\Memoire\251114\24111401XY_ADC0.txt")
    print(result)
    
    # Test fit
    if result['success']:
        fit_result = fit_gaussian_in_zone(
            result['channels'], 
            result['counts'], 
            center_approx=500,  # Adapter à ton pic
            tolerance=50
        )
        print(fit_result)
