"""
Script de Automação de Deploy para o GitHub e Ativação do GitHub Pages
Utiliza o token autenticado do Git Credential Manager em memória RAM.
Cria o repositório se não existir, realiza o git push e ativa o GitHub Pages via API.
"""

import os
import sys
import subprocess
import requests
import json
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def obter_token_gcm():
    """Recupera as credenciais do GitHub armazenadas no Git Credential Manager do Windows."""
    p = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        text=True,
        capture_output=True,
    )
    creds = {}
    for line in p.stdout.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            creds[k] = v
    username = creds.get("username")
    token = creds.get("password")
    if not token:
        raise ValueError("Token do GitHub não encontrado no Git Credential Manager.")
    return username, token


def garantir_repositorio_remoto(username, token, repo_name="sistema-financeiro-casa"):
    """Verifica se o repositório existe no GitHub; se não, cria via API."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    url_check = f"https://api.github.com/repos/{username}/{repo_name}"
    res = requests.get(url_check, headers=headers, timeout=15)

    if res.status_code == 200:
        print(f"Repositório https://github.com/{username}/{repo_name} já existe!")
        return res.json()
    elif res.status_code == 404:
        print(f"Criando novo repositório https://github.com/{username}/{repo_name} via GitHub API...")
        payload = {
            "name": repo_name,
            "description": "Painel financeiro mobile PWA com criptografia client-side AES-256-GCM e 28 categorias",
            "private": False,
            "auto_init": False,
        }
        res_create = requests.post("https://api.github.com/user/repos", headers=headers, json=payload, timeout=15)
        if res_create.status_code in [200, 201]:
            print("Repositório criado com sucesso no GitHub!")
            return res_create.json()
        else:
            raise RuntimeError(f"Falha ao criar repositório: {res_create.status_code} - {res_create.text}")
    else:
        raise RuntimeError(f"Erro ao verificar repositório: {res.status_code} - {res.text}")


def executar_git_push(username, token, repo_name="sistema-financeiro-casa"):
    """Configura o remote com autenticação e faz o push da branch main."""
    os.chdir(BASE_DIR)

    # 1. Stage and commit all changes
    subprocess.run(["git", "add", "-A"], check=True)
    status_proc = subprocess.run(["git", "status", "--porcelain"], text=True, capture_output=True)
    if status_proc.stdout.strip():
        subprocess.run(["git", "commit", "-m", "feat: atualiza PWA com 28 categorias, layout responsivo e drill-down de compras"], check=True)
        print("Novo commit criado com as atualizações!")
    else:
        print("Nenhuma alteração pendente para commit.")

    # 2. Configura remote URL seguro temporariamente para push
    remote_auth_url = f"https://{username}:{token}@github.com/{username}/{repo_name}.git"
    clean_remote_url = f"https://github.com/{username}/{repo_name}.git"

    # Verifica se já existe origin
    remotes = subprocess.run(["git", "remote"], text=True, capture_output=True).stdout.splitlines()
    if "origin" in remotes:
        subprocess.run(["git", "remote", "set-url", "origin", remote_auth_url], check=True)
    else:
        subprocess.run(["git", "remote", "add", "origin", remote_auth_url], check=True)

    try:
        # Garante branch main
        subprocess.run(["git", "branch", "-M", "main"], check=True)
        print("Empurrando commits para o GitHub origin/main...")
        push_res = subprocess.run(["git", "push", "-u", "origin", "main", "--force"], capture_output=True, text=True)
        if push_res.returncode != 0:
            raise RuntimeError(f"Falha no git push: {push_res.stderr}")
        print("Git push realizado com sucesso!")
    finally:
        # Restaura a URL limpa (sem token gravado no disco)
        subprocess.run(["git", "remote", "set-url", "origin", clean_remote_url], check=True)
        print("URL remota redefinida para formato limpo (sem token no .git/config).")


def ativar_github_pages(username, token, repo_name="sistema-financeiro-casa"):
    """Ativa ou verifica o GitHub Pages via API."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    url_pages = f"https://api.github.com/repos/{username}/{repo_name}/pages"

    res = requests.get(url_pages, headers=headers, timeout=15)
    if res.status_code == 200:
        pages_info = res.json()
        print(f"GitHub Pages já ativo: {pages_info.get('html_url')}")
        return pages_info.get("html_url")

    print("Habilitando GitHub Pages com build type 'workflow'...")
    payload = {
        "build_type": "workflow"
    }
    res_post = requests.post(url_pages, headers=headers, json=payload, timeout=15)
    if res_post.status_code in [200, 201]:
        print("GitHub Pages ativado com sucesso!")
        return f"https://{username}.github.io/{repo_name}/"
    else:
        # Tenta modo legado branch main se workflow falhar
        payload_legacy = {
            "source": {
                "branch": "main",
                "path": "/"
            }
        }
        res_legacy = requests.post(url_pages, headers=headers, json=payload_legacy, timeout=15)
        if res_legacy.status_code in [200, 201]:
            print("GitHub Pages ativado com sucesso via branch main!")
            return f"https://{username}.github.io/{repo_name}/"
        else:
            print(f"Aviso Pages: {res_post.status_code} - {res_post.text}")
            return f"https://{username}.github.io/{repo_name}/"


def main():
    print("=== DEPLOY AUTOMÁTICO GITHUB & GITHUB PAGES ===")
    username, token = obter_token_gcm()
    print(f"Usuário autenticado via GCM: {username}")

    garantir_repositorio_remoto(username, token)
    executar_git_push(username, token)
    pages_url = ativar_github_pages(username, token)

    print("\n" + "=" * 50)
    print("🚀 DEPLOY CONCLUÍDO COM SUCESSO!")
    print(f"Repositório: https://github.com/{username}/sistema-financeiro-casa")
    print(f"Link Oficial do App (PWA): {pages_url}")
    print("=" * 50)


if __name__ == "__main__":
    main()
