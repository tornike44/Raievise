import os
import json
import time
import anthropic
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv(".env.local")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_KEY")

# Créer le client Anthropic
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Dossier contenant les fichiers de programme
SOURCE_DIR = "workers/llm/data_structured"
OUTPUT_DIR = "workers/llm/output"

# Assurer que le dossier de sortie existe
os.makedirs(OUTPUT_DIR, exist_ok=True)

def analyze_with_claude(file_path, file_name):
    """Envoie le contenu du fichier à Claude pour analyse"""
    print(f"Analysing: {file_path}")

    # Lire le contenu du fichier
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier {file_path}: {e}")
        return None

    # Extraire les informations de base à partir du chemin du fichier
    path_parts = file_path.split('/')

    # Déterminer niveau, classe, filière, etc. à partir du chemin
    niveau = "unknown"
    cycle = "NA"
    classe = "unknown"
    filiere = "unknown"
    matiere = "unknown"

    # Extraire du chemin d'accès
    if "primaire" in file_path:
        niveau = "primaire"
        for part in path_parts:
            if part.startswith("cycle"):
                cycle = part
    elif "college" in file_path:
        niveau = "college"
        for part in path_parts:
            if part in ["5-4-3", "cycle3-6eme"]:
                classe = part
    elif "lycee" in file_path:
        niveau = "lycee"
        for part in path_parts:
            if part in ["seconde", "premiere", "terminale", "cap"]:
                classe = part
            if part in ["general-techno", "generale", "technologique", "professionnel"]:
                filiere = part

    # Trouver la matière (dernier répertoire avant le fichier)
    if len(path_parts) > 1:
        matiere = path_parts[-2]

    # Construire le prompt pour Claude
    prompt = f"""
    Analyse ce programme scolaire français et extrais uniquement la structure et les concepts clés au format JSON:

    {content[:15000]}

    ---

    Voici des informations extraites du chemin du fichier:
    - Niveau: {niveau}
    - Cycle: {cycle}
    - Classe: {classe}
    - Filière: {filiere}
    - Matière: {matiere}

    Ta tâche est de:
    1. Confirmer ou corriger ces métadonnées en te basant sur le contenu du document
    2. Extraire les thèmes principaux et leur description
    3. Pour chaque thème, identifier les chapitres ou axes d'étude
    4. Pour chaque chapitre, identifier les concepts clés et les jalons (s'ils existent)

    Réponds UNIQUEMENT au format JSON suivant:
    ```json
    {{
        "meta": {{
            "niveau": "primaire|college|lycee",
            "cycle": "cycle1|cycle2|cycle3|cycle4|NA",
            "classe": "classe précise",
            "filiere": "generale|technologique|professionnelle|NA",
            "matiere": "nom normalisé de la matière",
            "specialite": "nom de la spécialité ou NA"
        }},
        "description": "Description générale du programme",
        "themes": [
            {{
                "titre": "Titre du thème",
                "description": "Description du thème",
                "chapitres": [
                    {{
                        "titre": "Titre du chapitre",
                        "jalons": ["jalon 1", "jalon 2"],
                        "concepts_cles": ["concept1", "concept2"]
                    }}
                ]
            }}
        ]
    }}
    ```

    IMPORTANT:
    - N'inclus PAS de questions dans ton analyse
    - Concentre-toi uniquement sur la structure et le contenu du programme
    - Assure-toi que le fichier JSON est valide (pas d'erreurs de syntaxe)
    - Extrais uniquement du contenu présent dans le document (ne pas inventer des thèmes non mentionnés)
    """

    try:
        message = client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=4000,
            temperature=0.3,
            system="Tu es un expert en éducation française chargé d'analyser les programmes scolaires officiels.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Extraire le JSON de la réponse
        response_text = message.content[0].text

        # Rechercher le JSON dans la réponse
        import re
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = response_text

        # Parser le JSON
        try:
            parsed_json = json.loads(json_str)
            return parsed_json
        except json.JSONDecodeError as e:
            print(f"Erreur JSON: {e}")
            print(f"JSON brut: {json_str[:500]}")
            return None

    except Exception as e:
        print(f"Erreur API: {e}")
        return None

def process_files():
    """Traite tous les fichiers .txt dans le répertoire source"""
    count = 0

    for root, dirs, files in os.walk(SOURCE_DIR):
        for file in files:
            if file.endswith('.txt'):
                file_path = os.path.join(root, file)

                try:
                    # Analyser avec Claude
                    result = analyze_with_claude(file_path, file)

                    if result:
                        # Créer un nom de fichier de sortie
                        classe_safe = result['meta']['classe'].replace('/', '-')
                        matiere_safe = result['meta']['matiere'].replace('/', '-')
                        niveau_safe = result['meta']['niveau'].replace('/', '-')

                        output_file = os.path.join(
                            OUTPUT_DIR,
                            f"{niveau_safe}_{classe_safe}_{matiere_safe}.json"
                        )

                        # Enregistrer le résultat
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(result, f, ensure_ascii=False, indent=2)

                        print(f"Fichier traité avec succès: {output_file}")

                        # Incrémenter le compteur
                        count += 1

                        # Pause pour éviter de surcharger l'API
                        if count % 5 == 0:
                            print("Pause pour éviter de surcharger l'API...")
                            time.sleep(30)

                except Exception as e:
                    print(f"Erreur lors du traitement de {file_path}: {e}")

if __name__ == "__main__":
    process_files()
    print("Traitement terminé!")