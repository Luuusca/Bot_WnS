# monitor.py
import os
import re
import sys
import json
import hashlib
import logging
import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, List, Any

import requests
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# ========= Descobrir a pasta base (funciona em .py e .exe) =========
def get_base_dir() -> Path:
    # Quando empacotado por PyInstaller, sys.frozen estará definido
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    # Execução normal (arquivo .py)
    return Path(os.path.dirname(os.path.abspath(__file__)))

BASE_DIR = get_base_dir()

# ========= Configurações básicas =========
TARGET_DIV_ID = "conteudoDinamico"
SNAPSHOT_DEFAULT = "snapshot.json"
URLS_JSON_DEFAULT = "urls.json"
DISCORD_FILE_DEFAULT = "discord.txt"

# Padrões do bloco dinâmico a ser ignorado
STATS_PATTERNS = [
    r"Estatísticas da NF-e",
    r"NF-?e\s+Autorizadas",
    r"Número\s+de\s+Emissores",
]

# Fallbacks de seletores comuns
FALLBACK_SELECTORS = ("#content", "main", ".content", "#conteudo", ".conteudo")


# ========= Tipos =========
@dataclass
class MonitoredItem:
    id: int
    label: str
    url: str
    selector: Optional[str] = None  # CSS selector opcional, por item


# ========= Selenium / Coleta =========
def build_driver(headless: bool = True) -> webdriver.Chrome:
    chrome_opts = Options()
    if headless:
        chrome_opts.add_argument("--headless=new")
    chrome_opts.add_argument("--no-sandbox")
    chrome_opts.add_argument("--disable-gpu")
    chrome_opts.add_argument("--disable-dev-shm-usage")
    chrome_opts.add_argument("--window-size=1280,1024")
    chrome_opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
    # Silenciar ruídos do Chromium/ChromeDriver
    chrome_opts.add_argument("--log-level=3")
    chrome_opts.add_argument("--disable-logging")
    chrome_opts.add_experimental_option("excludeSwitches", ["enable-logging"])

    driver = webdriver.Chrome(options=chrome_opts)
    driver.set_page_load_timeout(60)
    return driver


def get_item_html(driver: webdriver.Chrome, item: MonitoredItem, timeout: int = 60) -> str:
    """
    Tenta extrair HTML do item na seguinte ordem:
      1) item.selector (CSS, se fornecido)
      2) #conteudoDinamico (padrão NFe)
      3) Fallbacks comuns (#content, main, .content, #conteudo, .conteudo)
      4) body completo (último recurso)
    """
    driver.get(item.url)
    WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    # 1) Seletor customizado do item
    if item.selector:
        try:
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, item.selector)))
            elem = driver.find_element(By.CSS_SELECTOR, item.selector)
            html = elem.get_attribute("outerHTML")
            if html and html.strip():
                return html
        except Exception:
            pass  # segue para as próximas tentativas

    # 2) Padrão NFe
    try:
        WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, TARGET_DIV_ID)))
        elem = driver.find_element(By.ID, TARGET_DIV_ID)
        html = elem.get_attribute("outerHTML")
        if html and html.strip():
            return html
    except Exception:
        pass

    # 3) Fallbacks comuns
    for css in FALLBACK_SELECTORS:
        try:
            elem = driver.find_element(By.CSS_SELECTOR, css)
            html = elem.get_attribute("outerHTML")
            if html and html.strip():
                return html
        except Exception:
            continue

    # 4) Último recurso: body
    page = driver.page_source or ""
    if page.strip():
        soup = BeautifulSoup(page, "html.parser")
        body = soup.find("body")
        return str(body) if body else page

    raise RuntimeError(f"Não foi possível extrair conteúdo de {item.url}. Verifique o seletor.")


# ========= Limpeza do HTML =========
def _remove_scripts_styles(soup: BeautifulSoup) -> None:
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()


def _contains_any_pattern(text: str, patterns) -> bool:
    if not text:
        return False
    for pat in patterns:
        if re.search(pat, text, flags=re.IGNORECASE):
            return True
    return False


def _prune_stats_blocks(soup: BeautifulSoup) -> None:
    """
    Remove o bloco de estatísticas dinâmicas, subindo níveis no DOM
    para tirar o contêiner relevante e evitar falsos positivos.
    """
    candidates = soup.find_all(string=lambda s: _contains_any_pattern(str(s), STATS_PATTERNS))
    for text_node in candidates:
        container = text_node.parent
        for _ in range(6):
            if container is None:
                break
            if container.name in ("div", "section", "table", "tbody", "ul", "ol", "article"):
                break
            container = container.parent
        if container is None:
            container = text_node.parent
        try:
            if container is not None:
                container.decompose()
            else:
                text_node.extract()
        except Exception:
            try:
                text_node.extract()
            except Exception:
                pass


def clean_content(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    _remove_scripts_styles(soup)
    _prune_stats_blocks(soup)
    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ========= Hash / Snapshot =========
def generate_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def load_snapshot(path: Path) -> Dict[str, str]:
    """
    Snapshot esperado: { "1": "hash", "2": "hash", ... }
    Compatibilidade:
      - Formato antigo único: {"snapshot_hash": "..."} -> vira {"__single__": "..."}
      - Formato antigo por URL: {"https://...": "hash"} -> migraremos na execução ao ID correspondente.
    """
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "snapshot_hash" in data and isinstance(data["snapshot_hash"], str):
            return {"__single__": data["snapshot_hash"]}
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
    except Exception as e:
        logging.warning(f"Falha ao ler snapshot: {e}")
    return {}


def save_snapshot(path: Path, mapping: Dict[str, str]) -> None:
    path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")


def compare_hash(prev: Optional[str], curr: str) -> bool:
    if prev is None:
        return True  # sem snapshot anterior → tratar como mudança para inicializar
    return prev != curr


# ========= Discord =========
def send_discord_alert(
    webhook_url: str,
    message: str,
    username: Optional[str] = None,
    avatar_url: Optional[str] = None
) -> None:
    payload = {"content": message}
    if username:
        payload["username"] = username
    if avatar_url:
        payload["avatar_url"] = avatar_url

    try:
        resp = requests.post(webhook_url, json=payload, timeout=30)
        if resp.status_code >= 400:
            raise RuntimeError(f"Discord retornou {resp.status_code}: {resp.text}")
    except Exception as e:
        logging.error(f"Falha ao enviar alerta ao Discord: {e}")


# ========= Arquivos de configuração =========
def load_urls_json(path: Path) -> List[MonitoredItem]:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo de URLs (JSON) não encontrado: {path}")
    try:
        data: Dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise ValueError(f"Falha ao ler JSON {path}: {e}")

    if not isinstance(data, dict) or "items" not in data or not isinstance(data["items"], list):
        raise ValueError("Estrutura inválida em urls.json. Esperado: {'items': [ ... ]}")

    items: List[MonitoredItem] = []
    seen_ids = set()
    for raw in data["items"]:
        if not isinstance(raw, dict):
            continue
        rid = raw.get("id")
        label = raw.get("label")
        url = raw.get("url")
        selector = raw.get("selector")  # opcional

        if not isinstance(rid, int):
            raise ValueError(f"Item com 'id' inválido: {raw}")
        if rid in seen_ids:
            raise ValueError(f"ID duplicado no urls.json: {rid}")
        seen_ids.add(rid)

        if not isinstance(label, str) or not label.strip():
            raise ValueError(f"Item {rid} com 'label' inválido.")
        if not isinstance(url, str) or not url.strip():
            raise ValueError(f"Item {rid} com 'url' inválida.")

        items.append(
            MonitoredItem(
                id=rid,
                label=label.strip(),
                url=url.strip(),
                selector=(selector.strip() if isinstance(selector, str) and selector.strip() else None),
            )
        )

    if not items:
        raise ValueError("Nenhum item válido encontrado em urls.json.")
    return items


def load_discord_creds(path: Path) -> Dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo de credenciais Discord não encontrado: {path}")
    creds: Dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        creds[k.strip()] = v.strip()
    if "DISCORD_WEBHOOK_URL" not in creds or not creds["DISCORD_WEBHOOK_URL"]:
        raise ValueError("DISCORD_WEBHOOK_URL ausente em discord.txt.")
    return creds


# ========= Execução em lote =========
def run_monitor_batch(
    urls_json_file: Path,
    discord_file: Path,
    snapshot_file: Path,
    headless: bool = True,
    log_each_ok: bool = True
) -> None:
    items = load_urls_json(urls_json_file)
    creds = load_discord_creds(discord_file)

    webhook = creds.get("DISCORD_WEBHOOK_URL")
    username = creds.get("USERNAME")
    avatar = creds.get("AVATAR_URL")
    mention_role_id = creds.get("MENTION_ROLE_ID")  # opcional

    if not webhook:
        logging.error("DISCORD_WEBHOOK_URL não encontrado no arquivo discord.txt.")
        return

    # carrega snapshot dict {"1": "hash", "2": "hash", ...}
    snap = load_snapshot(snapshot_file)

    # Compat: migrar chaves antigas por URL para ID
    url_to_id: Dict[str, str] = {it.url: str(it.id) for it in items}
    migrated = False
    for k in list(snap.keys()):
        if k.startswith("http://") or k.startswith("https://"):
            new_key = url_to_id.get(k)
            if new_key and new_key not in snap:
                snap[new_key] = snap[k]
                migrated = True
            del snap[k]
            migrated = True
    if migrated:
        logging.info("Snapshot antigo por URL migrado para chaves por ID.")

    driver = None
    try:
        driver = build_driver(headless=headless)
        changed_any = False

        for it in items:
            try:
                raw_html = get_item_html(driver, it)
                filtered_text = clean_content(raw_html)
                curr_hash = generate_hash(filtered_text)

                prev_hash = snap.get(str(it.id))
                changed = compare_hash(prev_hash, curr_hash)

                if changed:
                    # atualiza antes de notificar — tolerância a falhas
                    snap[str(it.id)] = curr_hash
                    changed_any = True
                    prefix = f"<@&{mention_role_id}> " if mention_role_id else ""
                    msg = f"{prefix}Houve alteração em **{it.label}**:\n{it.url}"
                    send_discord_alert(webhook, msg, username=username, avatar_url=avatar)
                    logging.info(f"[ALTERAÇÃO] {it.label} - {it.url}")
                else:
                    if log_each_ok:
                        logging.info(f"[OK] Sem mudanças: {it.label}")

            except Exception as e:
                logging.error(f"[ERRO] {it.id} - {it.label} → {e}")

        # salva o snapshot consolidado (apenas por ID)
        save_snapshot(snapshot_file, {k: v for k, v in snap.items() if k.isdigit()})

        if not changed_any:
            logging.info("Nenhuma mudança relevante detectada em nenhum item.")

    finally:
        if driver:
            driver.quit()


# ========= CLI =========
def parse_args():
    parser = argparse.ArgumentParser(
        description="Monitora mudanças em páginas (via seletor/DOM) e alerta no Discord."
    )
    parser.add_argument(
        "--urls-json",
        default=URLS_JSON_DEFAULT,
        help=f"Arquivo JSON com itens a monitorar (padrão: {URLS_JSON_DEFAULT})."
    )
    parser.add_argument(
        "--discord-file",
        default=DISCORD_FILE_DEFAULT,
        help=f"Arquivo de credenciais Discord (padrão: {DISCORD_FILE_DEFAULT})."
    )
    parser.add_argument(
        "--snapshot-file",
        default=SNAPSHOT_DEFAULT,
        help=f"Arquivo JSON de snapshots por ID (padrão: {SNAPSHOT_DEFAULT})."
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Executa o navegador com UI visível (não headless)."
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Nível de log."
    )
    parser.add_argument(
        "--quiet-ok",
        action="store_true",
        help="Não logar linhas [OK] para itens sem alterações."
    )
    return parser.parse_args()


# ========= Main =========
if __name__ == "__main__":
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level, "INFO"),
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    run_monitor_batch(
        urls_json_file=BASE_DIR / args.urls_json,
        discord_file=BASE_DIR / args.discord_file,
        snapshot_file=BASE_DIR / args.snapshot_file,
        headless=not args.no_headless,
        log_each_ok=not args.quiet_ok
    )
