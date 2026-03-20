import os
import subprocess

BASE_DIR = r"C:\Desenvolvimento\Clone-repositorios-git\repos"

def extrair_commits(repo_path):
    try:
        result = subprocess.check_output(
            ["git", "log", "--pretty=format:%H|%an|%ad|%s", "--date=iso"],
            cwd=repo_path,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )

        return result.split("\n")

    except:
        return []

def main():
    todos_commits = []

    for repo in os.listdir(BASE_DIR):
        caminho_repo = os.path.join(BASE_DIR, repo)

        if os.path.isdir(caminho_repo):
            print(f"Extraindo commits de {repo}")
            commits = extrair_commits(caminho_repo)
            todos_commits.extend(commits)

    print(f"\nTotal de commits encontrados: {len(todos_commits)}")

if __name__ == "__main__":
    main()