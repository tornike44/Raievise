import os
from pdfminer.high_level import extract_text

source_root = "downloads"
target_root = os.path.join("data", "programmes", "txt")

for root, dirs, files in os.walk(source_root):
    for file in files:
        if file.lower().endswith(".pdf"):
            pdf_path = os.path.join(root, file)
            relative_path = os.path.relpath(root, source_root)
            target_dir = os.path.join(target_root, relative_path)
            os.makedirs(target_dir, exist_ok=True)
            txt_filename = os.path.splitext(file)[0] + ".txt"
            txt_path = os.path.join(target_dir, txt_filename)
            try:
                text = extract_text(pdf_path)
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(text)
                print(f"Converti {pdf_path} -> {txt_path}")
            except Exception as e:
                print(f"Erreur lors de la conversion de {pdf_path}: {e}")
