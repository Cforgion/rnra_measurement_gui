"""
Conversion MPA → TXT
Utilise directement function_bob qui fonctionne
"""

import numpy as np
import os


def convert_mpa_folder(input_folder, output_folder, progress_callback=None):
    """
    Convertit tous les .mpa d'un dossier.
    C'est juste un wrapper autour de function_bob.
    
    Parameters
    ----------
    input_folder : str
        Dossier contenant les .mpa
    output_folder : str
        Dossier de sortie
    progress_callback : callable, optional
        callback(current, total, filename, status)
    
    Returns
    -------
    dict : résultats
    """
    
    # Créer dossier de sortie
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Liste des fichiers
    mpa_files = sorted([f for f in os.listdir(input_folder)
                        if f.lower().endswith('.mpa')])
    
    if not mpa_files:
        return {
            'success': False,
            'converted': 0,
            'errors': ['Aucun fichier .mpa trouvé'],
            'files_data': []
        }
    
    results = {
        'success': True,
        'converted': 0,
        'errors': [],
        'files_data': []
    }
    
    # === TON CODE function_bob EXACT ===
    for file_idx, filename in enumerate(mpa_files):
        i = 0
        file_path = os.path.join(input_folder, filename)
        
        try:
            # Ouvrir le fichier
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                lines = file.readlines()
            
            # Extraction dead times pour tous les ADC
            deadtime_factors = {}
            
            for adc_num in ['0', '1', '2', '3']:
                adc_to_find = f"[ADC{adc_num}]"
                livetime = None
                realtime = None
                in_adc_section = False
                
                for line in lines:
                    line = line.strip()
                    if line == adc_to_find:
                        in_adc_section = True
                        continue
                    elif in_adc_section and line.startswith("[") and line.endswith("]"):
                        break
                    if in_adc_section:
                        if line.startswith("livetime="):
                            try:
                                livetime = float(line.split('=')[1])
                            except ValueError:
                                pass
                        if line.startswith("realtime="):
                            try:
                                realtime = float(line.split('=')[1])
                            except ValueError:
                                pass
                
                if realtime is not None and livetime is not None and livetime != 0:
                    deadtime_factors[f"ADC{adc_num}"] = realtime / livetime
                else:
                    deadtime_factors[f"ADC{adc_num}"] = 1.0
            
            # Trouver où commencent les données
            int_line = None
            for idx, line in enumerate(lines):
                if line.startswith("[DATA"):
                    int_line = idx
                    break
            
            if int_line is None:
                results['errors'].append(f"{filename}: Section [DATA introuvable")
                if progress_callback:
                    progress_callback(file_idx + 1, len(mpa_files), filename, 'ERREUR')
                continue
            
            datas = lines[int_line:]
            
            # Traiter les données (TON CODE EXACT)
            file_data = {
                'fichier_base': os.path.splitext(filename)[0],
                'mpa_source': file_path,
                'adcs_found': []
            }
            
            while i < len(datas) - 1:
                if datas[i].startswith("[DATA"):
                    ADC, channel = datas[i].split(',')
                    ADC = ADC[1:]  # Enlever le [
                    channel = int(channel[:-3])  # Enlever ]\n
                    
                    data = np.zeros((channel, 2))
                    data[:, 1] = list(map(float, datas[i+1:channel+1+i]))
                    data[:, 0] = np.arange(channel)
                    
                    # Nom du fichier de sortie
                    adc_num = ADC.split('ADC')[-1]
                    adc_name = f"ADC{adc_num}"
                    base_name = os.path.splitext(filename)[0]
                    
                    # Format: 250317001_ADC0.txt
                    output_filename = f"{base_name}_{adc_name}.txt"
                    output_path = os.path.join(output_folder, output_filename)
                    
                    # Dead time
                    deadtime = deadtime_factors.get(adc_name, 1.0)
                    
                    # Sauvegarder
                    np.savetxt(output_path, data, fmt='%d',
                              header=f"Dead time factor = {deadtime:.5f}")
                    
                    # Stocker les infos
                    file_data['adcs_found'].append(adc_name)
                    file_data[f'chemin_{adc_name}'] = output_path
                    file_data[f'deadtime_{adc_name}'] = deadtime
                
                i += 1
            
            results['converted'] += 1
            results['files_data'].append(file_data)
            
            if progress_callback:
                progress_callback(file_idx + 1, len(mpa_files), filename, 'OK')
        
        except Exception as e:
            results['errors'].append(f"{filename}: {str(e)}")
            if progress_callback:
                progress_callback(file_idx + 1, len(mpa_files), filename, 'ERREUR')
    
    return results


# Alias pour compatibilité
def batch_convert_folder(input_folder, output_folder, adc_list=None, 
                         group_name='', progress_callback=None):
    """
    Alias pour garder la compatibilité.
    adc_list et group_name sont ignorés.
    """
    return convert_mpa_folder(input_folder, output_folder, progress_callback)
