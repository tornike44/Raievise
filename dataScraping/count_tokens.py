import os
import tiktoken

folder = "data/programmes/txt"

model_name = "gpt-4o"
encoding = tiktoken.encoding_for_model(model_name)

total_tokens = 0

for root, dirs, files in os.walk(folder):
    for file in files:
        if file.lower().endswith(".txt"):
            file_path = os.path.join(root, file)
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
            tokens = encoding.encode(text)
            num_tokens = len(tokens)
            print(f"{file_path}: {num_tokens} tokens")
            total_tokens += num_tokens

print("Nombre total de tokens :", total_tokens)
