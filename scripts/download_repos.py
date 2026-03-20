import requests
import os

USERNAME = "akitaonrails"
BASE_DIR = r"C:\Desenvolvimento\Clone-repositorios-git\repos"

os.makedirs(BASE_DIR, exist_ok=True)

repos = requests.get(f"https://api.github.com/users/{USERNAME}/repos").json()

for repo in repos:
    clone_url = repo["clone_url"]
    name = repo["name"]

    path = os.path.join(BASE_DIR, name)

    if not os.path.exists(path):
        print(f"Clonando {name}...")
        os.system(f"git clone {clone_url} {path}")