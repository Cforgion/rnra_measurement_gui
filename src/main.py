"""
GUI RNRA - Point d'entrée principal
Application de traitement de données RNRA
"""

import tkinter as tk
from tkinter import ttk
import os

# Imports des tabs
from gui.conversion_tab import MPAConvertTab
from gui.calibration_tab import CalibrationTab
from gui.Loop_tab import loop_tab
from gui.ANOVA_tab import anova_tab

class RNRAApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("RNRA Data Analysis - Université de Namur")
        self.geometry("1200x800")
        
        # État partagé entre tous les tabs
        self.app_state = {
            'temp_folder': os.path.join(os.path.dirname(__file__), '..', 'data', 'temp'),
            'output_folder': None,
            'group_name': None,
            'conversion_results': None,
            'calibration_results': None,
            'config_path' : None, 
            'group' : None,
        }
        
        # Créer dossier temp si nécessaire
        os.makedirs(self.app_state['temp_folder'], exist_ok=True)
        
        # Style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Notebook (tabs)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Création des tabs
        self.tab0 = MPAConvertTab(self.notebook, self.app_state)
        self.notebook.add(self.tab0, text="0. Conversion MPA → TXT")
        
        self.tab1 = CalibrationTab(self.notebook, self.app_state)
        self.notebook.add(self.tab1, text="1. Étalonnage")
        
        self.tab2 = loop_tab(self.notebook, self.app_state)
        self.notebook.add(self.tab2, text="2. Traitement")
        
        self.tab3 = anova_tab(self.notebook, self.app_state)
        self.notebook.add(self.tab3, text="3. ANOVA")
        
        # références croisées entre onglets
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        
        # Menu
        self._create_menu()
        
        # Status bar
        self.status_bar = ttk.Label(self, text="Prêt", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

    def on_tab_changed(self, event):
        current_tab = event.widget.select()
        tab_widget = event.widget.nametowidget(current_tab)

        if tab_widget == self.tab2:
            self.tab2.refresh_from_app_state()

    
    def _create_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # Menu Fichier
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="Nouveau projet", command=self.new_project)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.quit)
        
        # Menu Aide
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Aide", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_help)
        help_menu.add_command(label="À propos", command=self.show_about)
    
    def new_project(self):
        self.app_state['output_folder'] = None
        self.app_state['conversion_results'] = None
        self.app_state['calibration_results'] = None
        self.app_state['config_path'] = None
        self.app_state['group'] = None
    
        if hasattr(self.tab2, "config_path_var"):
            self.tab2.config_path = None
            self.tab2.config_path_var.set("")
        if hasattr(self.tab2, "output_dir_var"):
            self.tab2.output_dir_var.set(self.tab2.temp_dir)
    
        self.status_bar.config(text="Nouveau projet créé")

    def show_help(self):
        from tkinter import messagebox
        messagebox.showinfo(
            "Documentation",
            "GUI RNRA - Traitement de données\n"
            "Tab 0 : Conversion fichiers MPA → TXT\n"
            "Tab 1 : Étalonnage (calibration énergie)\n"
            "Tab 2 : Traintement des fichiers de mesures dans un boucle\n"
             "\t - Somme des nombre de coups dans la ROI et normalise par la charge intégrée \n"
             "\t - suppression du pics de carbon build-up \n"
             "\t - Fit par une courbe sigmoïde pour extraire les paramètres de la courbe \n"
             "\t - Export des résultats dans un fichier Excel  reprennant les paramètres de la sigmoïde et l'appartenance à un groupe de mesure\n"
             "Tab 4 : ANOVA sur les paramètres extraits de la sigmoïde"
        )
    
    def show_about(self):
        from tkinter import messagebox
        messagebox.showinfo(
            "À propos",
            "RNRA Data Analysis GUI\n\n"
            "Version 0.1.0\n"
            "Développé pour l'analyse de données RNRA pour le profilage de l'hydrogène\n"
            "Université de Namur - 2026\n"
            "Auteur: Cynthia Forgione"
        )

    def on_tab_changed(self, event):
        current_tab = event.widget.select()
        tab_widget = event.widget.nametowidget(current_tab)

        if tab_widget == self.tab2:
            self.tab2.refresh_from_app_state()


if __name__ == '__main__':
    app = RNRAApp()
    app.mainloop()
