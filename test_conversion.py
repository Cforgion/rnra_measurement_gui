"""
Test de la conversion MPA → TXT avec debug
"""

from src.core.file_io import batch_convert_folder
import os

# === CHEMINS ===
input_folder = r"C:\Users\forgi\OneDrive - Université de Namur\MASTER 1\projet MA1\Code\Donnée Brute\250317"
output_folder = r"C:\Users\forgi\OneDrive - Université de Namur\MASTER 2\Memoire\rnra_gui\data\temp"

# DEBUG : Vérifications avant conversion
print("=== DEBUG ===")
print(f"Dossier input existe ? {os.path.exists(input_folder)}")
print(f"Dossier output existe ? {os.path.exists(output_folder)}")

if os.path.exists(input_folder):
    mpa_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.mpa')]
    print(f"Fichiers .mpa trouvés : {len(mpa_files)}")
    if mpa_files:
        print(f"Premier fichier : {mpa_files[0]}")
else:
    print("ERREUR : Le dossier input n'existe pas !")
    print(f"Chemin : {input_folder}")
    exit(1)

print("\n=== CONVERSION ===")

# Fonction callback
def print_progress(current, total, filename, status):
    print(f"[{current}/{total}] {filename} ... {status}")

# Lancer la conversion
results = batch_convert_folder(
    input_folder,
    output_folder,
    adc_list=['ADC0', 'ADC3'],
    group_name='250317',
    progress_callback=print_progress
)

# Afficher les résultats
print("\n=== RÉSULTATS ===")
print(f"Succès : {results['success']}")
print(f"Fichiers convertis : {results['converted']}")
print(f"Erreurs : {len(results['errors'])}")

if results['errors']:
    print("\nDétail des erreurs :")
    for error in results['errors']:
        print(f"  - {error}")

# Vérifier ce qui a été créé
if os.path.exists(output_folder):
    output_files = os.listdir(output_folder)
    print(f"\nFichiers dans temp/ : {len(output_files)}")
    if output_files:
        print("Exemples :")
        for f in output_files[:5]:
            print(f"  - {f}")
else:
    print("\nLe dossier temp/ n'a pas été créé !")
