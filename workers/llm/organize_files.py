import os
import re
import shutil
from pathlib import Path

# Chemins
SOURCE_DIR = "workers/crawler/data/programmes/txt"
TARGET_DIR = "workers/llm/data_structured_fixed"

# Assurez-vous que le dossier cible existe
os.makedirs(TARGET_DIR, exist_ok=True)

def slugify(text):
    text = text.lower()
    text = re.sub(r'[éèêë]', 'e', text)
    text = re.sub(r'[àâä]', 'a', text)
    text = re.sub(r'[îï]', 'i', text)
    text = re.sub(r'[ôö]', 'o', text)
    text = re.sub(r'[ùûü]', 'u', text)
    text = re.sub(r'[ç]', 'c', text)
    text = re.sub(r'_', '-', text)
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'[^a-z0-9-]', '', text)
    text = re.sub(r'-+', '-', text)
    return text

def determine_structure(folder_name, file_name):
    """Détermine la structure basée sur le nom du dossier et du fichier"""
    # Structure par défaut
    structure = {
        "niveau": "unknown",
        "cycle": "unknown",
        "classe": "unknown",
        "filiere": "unknown",
        "matiere": folder_name
    }

    # Gestion des cycles primaires
    if folder_name == "cycle1" or folder_name == "cycle2" or folder_name == "cycle3":
        structure["niveau"] = "primaire"
        structure["cycle"] = folder_name
        structure["classe"] = "all"
    # Gestion du collège (cycle 4)
    elif folder_name == "cycle4":
        structure["niveau"] = "college"
        structure["cycle"] = folder_name
        structure["classe"] = "5-4-3"
    # Gestion des matières au lycée
    else:
        structure["niveau"] = "lycee"
        structure["cycle"] = "na"

        # Déterminer la classe et filière basées sur le nom du fichier
        if "seconde" in file_name.lower():
            structure["classe"] = "seconde"
            if "professionnelle" in file_name.lower():
                structure["filiere"] = "professionnel"
            else:
                structure["filiere"] = "general-techno"
        elif "premiere" in file_name.lower() or "premi_re" in file_name.lower():
            structure["classe"] = "premiere"
            if "technologique" in file_name.lower():
                structure["filiere"] = "technologique"
            elif "generale" in file_name.lower() or "g_n_rale" in file_name.lower():
                structure["filiere"] = "generale"
            elif "professionnelle" in file_name.lower():
                structure["filiere"] = "professionnel"
            else:
                structure["filiere"] = "all"
        elif "terminale" in file_name.lower():
            structure["classe"] = "terminale"
            if "technologique" in file_name.lower():
                structure["filiere"] = "technologique"
            elif "generale" in file_name.lower() or "g_n_rale" in file_name.lower():
                structure["filiere"] = "generale"
            elif "professionnelle" in file_name.lower():
                structure["filiere"] = "professionnel"
            else:
                structure["filiere"] = "all"
        elif "cap" in file_name.lower():
            structure["classe"] = "cap"
            structure["filiere"] = "professionnel"
        # Tenter de déduire le niveau pour les "all"
        elif "baccalaur_at_professionnel" in file_name.lower():
            structure["classe"] = "terminale"
            structure["filiere"] = "professionnel"
        else:
            structure["classe"] = "all"
            structure["filiere"] = "all"

    return structure

def organize_files():
    """Organise les fichiers selon la structure définie"""
    for root, dirs, files in os.walk(SOURCE_DIR):
        for file in files:
            if file.endswith('.txt'):
                # Obtenir les noms de dossier et fichier
                folder_name = os.path.basename(root)

                # Déterminer la structure
                structure = determine_structure(folder_name, file)

                # Construire le chemin cible
                if structure["niveau"] == "primaire":
                    target_path = f"{TARGET_DIR}/{structure['niveau']}/{structure['cycle']}/{slugify(structure['matiere'])}"
                elif structure["niveau"] == "college":
                    target_path = f"{TARGET_DIR}/{structure['niveau']}/{structure['classe']}/{slugify(structure['matiere'])}"
                else:  # lycée
                    target_path = f"{TARGET_DIR}/{structure['niveau']}/{structure['classe']}/{structure['filiere']}/{slugify(structure['matiere'])}"

                # Créer le dossier cible s'il n'existe pas
                os.makedirs(target_path, exist_ok=True)

                # Construire le nom de fichier cible
                target_file = f"{slugify(file.replace('.txt', ''))}.txt"

                # Chemin complet source et cible
                source_file = os.path.join(root, file)
                target_file_path = os.path.join(target_path, target_file)

                # Copier le fichier
                print(f"Copie de {source_file} vers {target_file_path}")
                shutil.copy2(source_file, target_file_path)

if __name__ == "__main__":
    organize_files()
    print("Réorganisation terminée!")