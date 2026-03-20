"""
RepoDownloader: Ingestão de Repositórios GitHub

Responsável por:
- Buscar repositórios de um usuário GitHub via API
- Validar repositórios (tamanho, linguagem)
- Clonar repositórios localmente
- Metadados de armazenamento

UC-001: Ingestão de Repositórios GitHub
"""

import subprocess
import requests
import logging
import time
import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class RepoDownloader:
    """
    Responsável por download e ingeste de repositórios GitHub.
    
    Atributos:
        MAX_REPO_SIZE: Tamanho máximo por repositório em bytes (1GB)
        SUPPORTED_LANGUAGES: Linguagens de programação suportadas
        RETRY_ATTEMPTS: Número de tentativas em caso de falha de rede
        GITHUB_API_BASE: URL base da API GitHub v3
    
    Exemplo:
        >>> downloader = RepoDownloader()
        >>> result = downloader.download_repos("akitaonrails", "/data/repos")
        >>> print(result['repos_downloaded'])
        45
    """

    MAX_REPO_SIZE = 1_000_000_000  # 1GB em bytes
    SUPPORTED_LANGUAGES = {"Python", "JavaScript", "Java", "Go", "Rust", "C#"}
    RETRY_ATTEMPTS = 3
    GITHUB_API_BASE = "https://api.github.com"

    def __init__(self) -> None:
        """Inicializa RepoDownloader."""
        logger.info("RepoDownloader initialized")

    def fetch_user_repos(self, username: str, retries: int = 0) -> List[Dict]:
        """
        Busca repositórios de um usuário GitHub via API com tratamento de rate limit (v1.1).
        
        Args:
            username: Nome de usuário GitHub
            retries: Número de tentativas em caso de rate limit (internal)
            
        Returns:
            Lista de dicts com informações do repositório:
            [
                {
                    "name": "repo1",
                    "clone_url": "https://github.com/user/repo1.git",
                    "description": "...",
                    "language": "Python",
                    "stars": 100,
                    "size": 5000,  # em KB
                    "updated_at": "2024-01-15T10:30:00Z"
                },
                ...
            ]
            
        Raises:
            Exception: Se API retorna status != 200 (após retries)
            ValueError: Se username é inválido ou vazio
            
        Exemplo:
            >>> repos = downloader.fetch_user_repos("akitaonrails")
            >>> repos[0]["name"]
            "repo1"
        """
        if not username or not isinstance(username, str):
            raise ValueError(f"Username inválido: {username}")

        url = f"{self.GITHUB_API_BASE}/users/{username}/repos"
        params = {"per_page": 100, "page": 1}

        try:
            logger.debug(f"Fetching repos for user: {username}")
            response = requests.get(url, params=params, timeout=10)

            # Tratamento de rate limit (v1.1 - GithubChat pattern)
            if response.status_code == 429:
                reset_time = int(response.headers.get('x-ratelimit-reset', 0))
                if reset_time > 0:
                    sleep_seconds = max(1, reset_time - int(time.time()))
                    logger.warning(
                        f"GitHub API rate limited. "
                        f"Sleeping {sleep_seconds}s before retry..."
                    )
                    
                    if retries < 3:  # Max 3 retries
                        time.sleep(sleep_seconds + 1)  # +1 seg buffer
                        logger.info(f"Retrying fetch (attempt {retries + 1}/3)...")
                        return self.fetch_user_repos(username, retries=retries + 1)
                    else:
                        raise Exception("Max retries exceeded for rate limit")
                else:
                    raise Exception("Rate limited but x-ratelimit-reset header missing")

            if response.status_code != 200:
                logger.error(
                    f"GitHub API error for user {username}: {response.status_code}"
                )
                raise Exception(
                    f"GitHub API error: {response.status_code} - {response.text}"
                )

            repos = response.json()
            logger.info(f"Found {len(repos)} repositories for user {username}")

            return repos

        except requests.RequestException as e:
            logger.error(f"Network error fetching repos: {e}")
            raise

    def validate_github_url(self, url: str) -> bool:
        """
        Valida se URL é um repositório GitHub válido.
        
        Args:
            url: URL para validar
            
        Returns:
            True se URL é válida, False caso contrário
            
        Exemplo:
            >>> downloader.validate_github_url("https://github.com/user/repo.git")
            True
            >>> downloader.validate_github_url("https://example.com/repo")
            False
        """
        if not url or not isinstance(url, str):
            return False

        # Padrões válidos de URL GitHub
        patterns = [
            r"^https://github\.com/[\w\-\.]+/[\w\-\.]+\.git$",  # https ...git
            r"^https://github\.com/[\w\-\.]+/[\w\-\.]+$",  # https sem .git
            r"^git@github\.com:[\w\-\.]+/[\w\-\.]+\.git$",  # SSH
        ]

        for pattern in patterns:
            if re.match(pattern, url):
                logger.debug(f"URL validated: {url}")
                return True

        logger.debug(f"Invalid GitHub URL: {url}")
        return False

    def extract_repo_name(self, url: str) -> str:
        """
        Extrai nome do repositório de uma URL.
        
        Args:
            url: URL do repositório
            
        Returns:
            Nome do repositório
            
        Raises:
            ValueError: Se URL é inválida
            
        Exemplo:
            >>> downloader.extract_repo_name("https://github.com/user/my-repo.git")
            "my-repo"
        """
        if not self.validate_github_url(url):
            raise ValueError(f"URL GitHub inválida: {url}")

        # Remove .git se presente
        url_clean = url.rstrip(".git")

        # Extrai último segmento (nome do repo)
        repo_name = url_clean.split("/")[-1]

        logger.debug(f"Extracted repo name: {repo_name} from {url}")
        return repo_name

    def clone_repo(self, clone_url: str, dest_path: str, retry: int = 0) -> bool:
        """
        Clona um repositório Git para caminho local com shallow clone (v1.1).
        
        Args:
            clone_url: URL do repositório para clonar
            dest_path: Caminho destino para clone
            retry: Tentativa atual (internal - não usar)
            
        Returns:
            True se clone foi bem-sucedido, False caso contrário
            
        Features v1.1:
            - Shallow clone: --depth 1 (apenas último commit)
            - Post-clone cleanup: Remove .git, node_modules, __pycache__, etc
            
        Exemplo:
            >>> downloader.clone_repo(
            ...     "https://github.com/user/repo.git",
            ...     "/data/repos/repo"
            ... )
            True
        """
        if not self.validate_github_url(clone_url):
            logger.error(f"Invalid URL for cloning: {clone_url}")
            return False

        try:
            repo_name = self.extract_repo_name(clone_url)
            logger.info(f"Cloning repository: {repo_name} to {dest_path}")

            # Garantir que diretório pai existe
            Path(dest_path).parent.mkdir(parents=True, exist_ok=True)

            # git clone com --depth 1 para shallow clone (v1.1)
            # Reduz tempo ~80-90% e espaço ~60-70% para repos grandes
            result = subprocess.run(
                ["git", "clone", "--depth", "1", clone_url, dest_path],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutos timeout
            )

            if result.returncode == 0:
                logger.info(f"Successfully cloned: {repo_name}")
                
                # Cleanup pós-clone (v1.1): Remove diretórios não essenciais
                self._cleanup_post_clone(dest_path)
                
                return True
            else:
                logger.warning(
                    f"Clone failed for {repo_name}: {result.stderr[:200]}"
                )

                # Retry em caso de falha temporária
                if retry < self.RETRY_ATTEMPTS:
                    logger.info(f"Retrying clone... (attempt {retry + 1})")
                    return self.clone_repo(clone_url, dest_path, retry + 1)

                return False

        except subprocess.TimeoutExpired:
            logger.error(f"Clone timeout for {clone_url}")
            return False
        except FileNotFoundError:
            logger.error("Git command not found. Please install git.")
            return False
        except Exception as e:
            logger.error(f"Unexpected error cloning {clone_url}: {e}")
            return False

    def _cleanup_post_clone(self, repo_path: str) -> None:
        """
        Remove diretórios não essenciais após clone (v1.1 optimization).
        
        Reduz storage removendo:
        - .git (histórico completo)
        - node_modules (dependências JavaScript)
        - __pycache__ (bytecode Python)
        - venv/.venv (ambientes virtuais)
        - target (build Rust/Kotlin)
        - Outros diretórios temporários
        
        Args:
            repo_path: Caminho do repositório clonado
            
        Exemplo:
            >>> downloader._cleanup_post_clone("/data/repos/myrepo")
            # Remove ~60-70% do espaço do clone original
        """
        cleanup_dirs = [
            ".git",
            "node_modules",
            "__pycache__",
            ".venv",
            "venv",
            "target",
            ".pytest_cache",
            ".tox",
            "dist",
            "build",
            ".gradle",
            ".m2",
            "vendor",
            ".next",
            "out",
        ]

        for dir_name in cleanup_dirs:
            dir_path = os.path.join(repo_path, dir_name)
            if os.path.isdir(dir_path):
                try:
                    shutil.rmtree(dir_path, ignore_errors=True)
                    logger.debug(f"Cleaned up: {dir_name} at {repo_path}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup {dir_name}: {e}")

    def download_repos(
        self,
        username: str,
        dest_base_path: str,
        language_filter: Optional[str] = None,
        min_stars: int = 0,
        max_repos: Optional[int] = None,
        since_date: Optional[str] = None,
    ) -> Dict:
        """
        Fluxo completo: Buscar e clonar repositórios de um usuário com filtros.
        
        Args:
            username: Nome de usuário GitHub
            dest_base_path: Caminho base para armazenar repositórios
            language_filter: Filtrar por linguagem (opcional)
            min_stars: Mínimo de stars para incluir repositório
            max_repos: Máximo de repositórios a baixar (opcional, ex: 50)
            since_date: Data mínima de atualização (ISO 8601, ex: "2024-01-01")
            
        Returns:
            Dicionário com resumo do download:
            {
                "user": "akitaonrails",
                "repos_downloaded": 45,
                "repos_failed": 2,
                "total_size_gb": 2.5,
                "storage_path": "/data/repos",
                "status": "success",  # ou "partial" ou "failed"
                "timestamp": "2025-03-20T14:30:00Z",
                "filters_applied": {
                    "max_repos": 50,
                    "since_date": "2024-01-01",
                    "language": "Python",
                    "min_stars": 10
                },
                "details": [
                    {"name": "repo1", "status": "success", "size_mb": 50, "updated_at": "2024-03-20"},
                    ...
                ]
            }
            
        Raises:
            ValueError: Se username ou dest_base_path inválidos
            
        Exemplo:
            >>> result = downloader.download_repos(
            ...     "akitaonrails",
            ...     "/data/repos",
            ...     max_repos=50,
            ...     since_date="2024-01-01"
            ... )
            >>> print(f"Downloaded: {result['repos_downloaded']}")
            Downloaded: 45
        """
        if not username:
            raise ValueError("Username não pode estar vazio")

        if not dest_base_path:
            raise ValueError("Destination path não pode estar vazio")

        logger.info(f"Starting download_repos for user: {username}")
        logger.info(f"  destination: {dest_base_path}")
        logger.info(f"  language_filter: {language_filter}")
        logger.info(f"  min_stars: {min_stars}")
        logger.info(f"  max_repos: {max_repos}")
        logger.info(f"  since_date: {since_date}")

        dest_path = Path(dest_base_path)
        dest_path.mkdir(parents=True, exist_ok=True)

        details = []
        repos_downloaded = 0
        repos_failed = 0
        repos_skipped = 0
        total_size_bytes = 0

        try:
            # Buscar repos
            repos = self.fetch_user_repos(username)

            # ===== ORDENAR POR DATA (mais recentes primeiro) =====
            repos = sorted(
                repos,
                key=lambda x: x.get("updated_at", ""),
                reverse=True  # Descendente: mais recentes primeiro
            )
            logger.info(f"Repos ordenados por data (recentes primeiro)")

            # ===== APLICAR FILTROS =====
            filtered_repos = []
            cutoff_date = None
            if since_date:
                try:
                    # Parse date string (ISO 8601)
                    cutoff_date = datetime.fromisoformat(since_date.replace("Z", "+00:00"))
                    logger.info(f"Filtering repos modified since: {since_date}")
                except ValueError:
                    logger.warning(f"Invalid since_date format: {since_date}. Using all repos.")

            repo_count = 0
            for repo in repos:
                repo_name = repo.get("name")

                # Limite máximo de repos
                if max_repos and repo_count >= max_repos:
                    logger.info(f"Reached max_repos limit ({max_repos})")
                    break

                # Filtro de linguagem
                if language_filter and repo.get("language") != language_filter:
                    logger.debug(f"Skipping {repo_name}: language mismatch")
                    repos_skipped += 1
                    continue

                # Filtro de stars mínimas
                if repo.get("stargazers_count", 0) < min_stars:
                    logger.debug(f"Skipping {repo_name}: insufficient stars")
                    repos_skipped += 1
                    continue

                # Filtro de data
                if cutoff_date:
                    try:
                        repo_updated = datetime.fromisoformat(
                            repo.get("updated_at", "").replace("Z", "+00:00")
                        )
                        if repo_updated < cutoff_date:
                            logger.debug(
                                f"Skipping {repo_name}: "
                                f"last updated {repo_updated} < {cutoff_date}"
                            )
                            repos_skipped += 1
                            continue
                    except (ValueError, AttributeError):
                        logger.debug(f"Could not parse date for {repo_name}")

                filtered_repos.append(repo)
                repo_count += 1

            logger.info(f"After filtering: {len(filtered_repos)} repos to process")

            # ===== PROCESSAR REPOS =====
            for repo in filtered_repos:
                repo_name = repo.get("name")

                # Aplicar filtros
                if language_filter and repo.get("language") != language_filter:
                    logger.debug(f"Skipping {repo_name}: language mismatch")
                    continue

                if repo.get("stargazers_count", 0) < min_stars:
                    logger.debug(f"Skipping {repo_name}: insufficient stars")
                    continue

                # Validar tamanho
                repo_size_kb = repo.get("size", 0)
                repo_size_bytes = repo_size_kb * 1024

                if repo_size_bytes > self.MAX_REPO_SIZE:
                    logger.warning(
                        f"Skipping {repo_name}: exceeds max size "
                        f"({repo_size_bytes / 1e9:.2f}GB > 1GB)"
                    )
                    details.append(
                        {
                            "name": repo_name,
                            "status": "skipped_size",
                            "size_mb": repo_size_bytes / 1e6,
                        }
                    )
                    continue

                # Clone
                clone_url = repo.get("clone_url")
                dest_repo_path = dest_path / repo_name

                if self.clone_repo(clone_url, str(dest_repo_path)):
                    repos_downloaded += 1
                    total_size_bytes += repo_size_bytes
                    details.append(
                        {
                            "name": repo_name,
                            "status": "success",
                            "size_mb": repo_size_bytes / 1e6,
                            "clone_url": clone_url,
                            "updated_at": repo.get("updated_at", ""),
                        }
                    )
                else:
                    repos_failed += 1
                    details.append(
                        {
                            "name": repo_name,
                            "status": "failed",
                            "size_mb": repo_size_bytes / 1e6,
                            "updated_at": repo.get("updated_at", ""),
                        }
                    )

            # Determinar status
            total_processed = len(filtered_repos)
            if repos_downloaded == total_processed:
                status = "success"
            elif repos_downloaded > 0:
                status = "partial"
            else:
                status = "failed"

            result = {
                "user": username,
                "repos_downloaded": repos_downloaded,
                "repos_failed": repos_failed,
                "repos_skipped": repos_skipped,
                "total_size_gb": round(total_size_bytes / 1e9, 2),
                "storage_path": str(dest_path),
                "status": status,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "filters_applied": {
                    "max_repos": max_repos,
                    "since_date": since_date,
                    "language": language_filter,
                    "min_stars": min_stars,
                },
                "details": details,
            }

            logger.info(f"Download complete: {status}")
            logger.info(f"  Downloaded: {repos_downloaded}/{total_processed}")
            logger.info(f"  Skipped: {repos_skipped}")
            logger.info(f"  Total size: {result['total_size_gb']}GB")

            return result

        except Exception as e:
            logger.error(f"Error in download_repos: {e}")
            raise
