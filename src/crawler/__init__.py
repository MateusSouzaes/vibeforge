"""
Módulo Crawler: Responsável por ingestão de repositórios GitHub

Componentes:
- RepoDownloader: Download e validação de repositórios
- CommitExtractor: Extração de histórico de commits
"""

from .repo_downloader import RepoDownloader

__all__ = ["RepoDownloader"]
