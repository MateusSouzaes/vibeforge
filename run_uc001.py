#!/usr/bin/env python
"""
UC-001: Ingestão de Repositórios GitHub
Script com variáveis de ambiente
"""

import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
import os

# ===== SETUP =====
# Carregar variáveis do .env
load_dotenv()

# Setup logging bonito
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Importar após config
from src.crawler.repo_downloader import RepoDownloader

def main():
    """Executa UC-001 completo com configurações do .env"""
    
    # ===== LER VARIÁVEIS DO .env =====
    username = os.getenv("GITHUB_USERNAME")
    dest_path = os.getenv("REPOS_OUTPUT_PATH", "./data/repos")
    max_repos = os.getenv("MAX_REPOS", None)
    since_date = os.getenv("SINCE_DATE", None)
    
    # Converter max_repos para int se definido
    if max_repos:
        try:
            max_repos = int(max_repos)
        except ValueError:
            logger.warning(f"⚠️ MAX_REPOS inválido: {max_repos}. Ignorando...")
            max_repos = None
    
    # Validar
    if not username:
        logger.error("❌ GITHUB_USERNAME não configurado em .env")
        return 1
    
    logger.info("=" * 60)
    logger.info("🚀 UC-001: INGESTÃO DE REPOSITÓRIOS")
    logger.info("=" * 60)
    logger.info(f"📝 Configuração:")
    logger.info(f"   Username:  {username}")
    logger.info(f"   Output:    {dest_path}")
    if max_repos:
        logger.info(f"   Max Repos: {max_repos}")
    if since_date:
        logger.info(f"   Since:     {since_date}")
    logger.info("")
    
    try:
        # ===== EXECUTAR =====
        downloader = RepoDownloader()
        
        result = downloader.download_repos(
            username=username,
            dest_base_path=dest_path,
            language_filter=None,  # Sem filtro (ou "Python", "JavaScript", etc)
            min_stars=0,            # Sem mínimo de stars (ou 10, 100, etc)
            max_repos=max_repos,    # Limite máximo de repos (ex: 50)
            since_date=since_date   # Data mínima de atualização (ex: "2024-01-01")
        )
        
        # ===== EXIBIR RESULTADO =====
        print("\n" + "=" * 60)
        print("✅ RESULTADO FINAL")
        print("=" * 60)
        print(f"👤 Usuário:          {result['user']}")
        print(f"📦 Repos baixados:   {result['repos_downloaded']}")
        print(f"❌ Repos falhados:   {result['repos_failed']}")
        print(f"⏭️  Repos pulados:    {result['repos_skipped']}")
        print(f"💾 Tamanho total:    {result['total_size_gb']} GB")
        print(f"📊 Status:           {result['status']}")
        print(f"⏰ Timestamp:        {result['timestamp']}")
        print(f"📂 Localizado em:    {result['storage_path']}")
        
        # ===== EXIBIR FILTROS APLICADOS =====
        if 'filters_applied' in result:
            print("\n🔍 Filtros Aplicados:")
            filters = result['filters_applied']
            if filters.get('max_repos'):
                print(f"   Máximo de Repos: {filters['max_repos']}")
            if filters.get('since_date'):
                print(f"   Desde Data:      {filters['since_date']}")
            if filters.get('language'):
                print(f"   Linguagem:       {filters['language']}")
            if filters.get('min_stars'):
                print(f"   Mínimo Stars:    {filters['min_stars']}")
        
        print("=" * 60 + "\n")
        
        # ===== DETALHE DOS REPOS =====
        if result['details']:
            print("📋 Repositórios (primeiros 10):\n")
            for i, repo in enumerate(result['details'][:10], 1):
                icon = "✅" if repo['status'] == 'success' else "❌"
                size_mb = repo.get('size_mb', 0)
                print(f"  {i:2d}. {icon} {repo['name']:30s} - {size_mb:>10.1f} MB")
            
            if len(result['details']) > 10:
                print(f"\n  ... e mais {len(result['details']) - 10} repositórios")
        
        print("")
        return 0
        
    except Exception as e:
        logger.error(f"💥 Erro durante execução: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())