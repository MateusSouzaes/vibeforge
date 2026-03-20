import os

BASE_DIR = r"C:\Desenvolvimento\Clone-repositorios-git\repos"

# arquivos que queremos analisar
EXTENSOES_VALIDAS = (".rb", ".py", ".js", ".ts", ".md")

# pastas que devemos ignorar (muito importante)
PASTAS_IGNORADAS = ["node_modules", ".git", "dist", "build", "__pycache__"]

def deve_ignorar(path):
    return any(pasta in path for pasta in PASTAS_IGNORADAS)

def read_files():
    textos = []

    for root, dirs, files in os.walk(BASE_DIR):
        if deve_ignorar(root):
            continue

        for file in files:
            if file.endswith(EXTENSOES_VALIDAS):
                caminho = os.path.join(root, file)

                try:
                    with open(caminho, "r", encoding="utf-8") as f:
                        conteudo = f.read()
                        textos.append(conteudo)
                except:
                    pass

    return textos


def chunk_text(texto, tamanho=800):
    return [texto[i:i+tamanho] for i in range(0, len(texto), tamanho)]


def get_chunks():
    textos = read_files()
    chunks = []

    for texto in textos:
        chunks.extend(chunk_text(texto))

    return chunks


if __name__ == "__main__":
    chunks = get_chunks()
    print(f"Total de chunks gerados: {len(chunks)}")