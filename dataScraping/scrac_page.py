import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time

def sanitize_filename(s):
    sanitized = re.sub(r'[^A-Za-z0-9]+', '_', s)
    return sanitized.strip('_')[:100]

def download_file(url, folder, filename):
    os.makedirs(folder, exist_ok=True)
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
    except Exception as e:
        print(f"Erreur lors du téléchargement de {url}: {e}")
        return
    filepath = os.path.join(folder, filename)
    with open(filepath, "wb") as f:
        f.write(resp.content)
    print(f"Téléchargé: {filepath}")

def download_program_documents(program_url, discipline, full_title):
    try:
        resp = requests.get(program_url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"Erreur lors de la récupération de la page programme {program_url}: {e}")
        return
    soup = BeautifulSoup(resp.content, "html.parser")
    links = []
    # Pattern 1 : Bloc "Le programme"
    h2_prog = soup.find("h2", string=lambda s: s and "Le programme" in s)
    if h2_prog:
        rich_div = h2_prog.find_next_sibling("div", class_="rich-text ckeditor-text clearfix")
        if rich_div:
            for a in rich_div.find_all("a", href=True):
                href = a["href"]
                if "/document/" in href and "/download" in href:
                    file_label = a.get_text(strip=True)
                    links.append((urljoin(program_url, href), file_label))
    # Pattern 2 : Bloc "Télécharger les programmes"
    span_dl = soup.find("span", class_="block-title", string=lambda s: s and "Télécharger les programmes" in s)
    if span_dl:
        desc_div = span_dl.find_next_sibling("div", class_="ckeditor-text block-description")
        if desc_div:
            for a in desc_div.find_all("a", href=True):
                href = a["href"]
                if "/document/" in href and "/download" in href:
                    file_label = a.get_text(strip=True)
                    links.append((urljoin(program_url, href), file_label))
    links = list(set(links))
    if not links:
        print(f"Aucun lien de téléchargement trouvé sur {program_url}")
    else:
        folder = os.path.join("downloads", sanitize_filename(discipline))
        for i, (link, file_label) in enumerate(links, start=1):
            file_name = sanitize_filename(file_label)
            if not file_name.lower().endswith(".pdf"):
                file_name += ".pdf"
            print(f"Téléchargement depuis {link} dans {folder} avec nom '{file_name}'")
            download_file(link, folder, file_name)

def download_hardcoded_files():
    cycles = {
        "cycle1": [
            "https://www.education.gouv.fr/sites/default/files/ensel135_annexe1.pdf",
            "https://www.education.gouv.fr/sites/default/files/ensel135_annexe2.pdf"
        ],
        "cycle2": [
            "https://cache.media.education.gouv.fr/file/31/88/5/ensel714_annexe1_1312885.pdf"
        ],
        "cycle3": [
            "https://cache.media.education.gouv.fr/file/31/88/7/ensel714_annexe2_1312887.pdf"
        ],
        "cycle4": [
            "https://cache.media.education.gouv.fr/file/31/89/1/ensel714_annexe3_1312891.pdf"
        ]
    }
    for cycle, urls in cycles.items():
        folder = os.path.join("downloads", cycle)
        for url in urls:
            filename = os.path.basename(url)
            print(f"Téléchargement du fichier {url} dans {folder} sous le nom {filename}")
            download_file(url, folder, filename)

base_url = "https://eduscol.education.fr"
try:
    main_response = requests.get(base_url, timeout=10)
    main_response.raise_for_status()
except Exception as e:
    print(f"Erreur lors de la récupération de la page principale : {e}")
    exit(1)
main_soup = BeautifulSoup(main_response.content, "html.parser")
ul = main_soup.find("ul", class_="main-menu__third-level__list lvl-2")
if not ul:
    print("Liste des disciplines non trouvée sur la page principale.")
    exit(1)
disciplines = []
for li in ul.find_all("li"):
    a = li.find("a", href=True)
    if a:
        discipline_name = a.get_text(strip=True)
        discipline_url = urljoin(base_url, a["href"])
        disciplines.append((discipline_name, discipline_url))
print("=== Liste des disciplines ===")
for disc_name, disc_url in disciplines:
    print(f"Discipline : {disc_name}\nURL       : {disc_url}\n")
print("=" * 40)
for discipline_name, discipline_url in disciplines:
    print(f"\nTraitement de la discipline : {discipline_name}")
    print(f"Page discipline : {discipline_url}")
    try:
        disc_response = requests.get(discipline_url, timeout=10)
        disc_response.raise_for_status()
    except Exception as e:
        print(f"Erreur lors de la récupération de la page de discipline {discipline_url} : {e}")
        continue
    disc_soup = BeautifulSoup(disc_response.content, "html.parser")
    h2_prog_ress = disc_soup.find("h2", class_="block-title", string=lambda s: s and "Programmes et ressources" in s)
    if not h2_prog_ress:
        print("Aucun bloc 'Programmes et ressources' trouvé sur cette page.")
        continue
    program_div = h2_prog_ress.find_next_sibling("div", class_="block-content three-items-per-line")
    if not program_div:
        print("Aucun contenu de programmes trouvé (div 'block-content three-items-per-line').")
        continue
    program_items = program_div.find_all("div", class_="item-block block-folder-item")
    if not program_items:
        print("Aucun item de programme trouvé dans le bloc.")
        continue
    print(f"Programmes trouvés dans la discipline {discipline_name} :")
    for item in program_items:
        a_item = item.find("a", href=True)
        if not a_item:
            continue
        span_title = a_item.find("span", class_="block-title")
        if span_title:
            full_title = span_title.get_text(strip=True)
        else:
            full_title = a_item.get_text(strip=True)
        if " - " not in full_title:
            continue
        title_lower = full_title.lower().strip()
        if title_lower.startswith("programmes et ressources") or re.search(r'-\s*cycles\s+', title_lower):
            process = True
        elif re.search(r'-\s*cycle\s+\d+$', title_lower):
            process = False
        else:
            process = False
        if not process:
            continue
        program_url = urljoin(base_url, a_item["href"])
        print(f"  * Titre complet   : {full_title}")
        print(f"    URL du programme : {program_url}")
        download_program_documents(program_url, discipline_name, full_title)
    print("-" * 40)
    time.sleep(1)

print("\nTéléchargement des fichiers en dur par cycle:")
download_hardcoded_files()
