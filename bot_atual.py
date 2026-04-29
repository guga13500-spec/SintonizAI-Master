"""
ZapiaMusic - Bot de música para TeamTalk5
Servidor: blindmasters.org:19558
Canal: Grupo dos amigos

Comandos (via mensagem de texto no canal):
  h           - mostra os comandos disponíveis
  t <música>  - toca uma música (busca no YouTube)
  p           - pausa/continua a música
  s           - para a música
  v <0-100>   - ajusta o volume
"""

# ── Fix SDK: reescreve ttsdk_downloader.py antes de qualquer import ────────────
# O downloader original usa VERSION_IDENTIFIER="5.15" (inexistente na página),
# causando "list index out of range". Substituímos por URL direta da v5.22a.
import os
import sys
import platform
import importlib.util

def _fix_sdk_downloader():
    """Reescreve o arquivo ttsdk_downloader.py para usar URL fixa da v5.22a."""
    spec = importlib.util.find_spec("teamtalk")
    if spec is None:
        return  # teamtalk não instalado, vai falhar depois
    
    pkg_dir = os.path.dirname(spec.origin)
    target = os.path.join(pkg_dir, "tools", "ttsdk_downloader.py")
    
    if not os.path.exists(target):
        print(f"[fix] Arquivo não encontrado: {target}")
        return

    new_content = '''"""Downloader fixado para usar SDK v5.22a diretamente (sem scraping)."""
import os
import platform
import shutil
import sys

import patoolib
import requests

from . import downloader

cd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_url_suffix_from_platform() -> str:
    machine = platform.machine()
    if sys.platform == "win32":
        architecture = platform.architecture()
        if machine == "AMD64" or machine == "x86":
            if architecture[0] == "64bit":
                return "win64"
            else:
                return "win32"
        else:
            sys.exit("Native Windows on ARM is not supported")
    elif sys.platform == "darwin":
        sys.exit("Darwin is not supported")
    else:
        if machine == "AMD64" or machine == "x86_64":
            return "ubuntu22_x86_64"
        elif "arm" in machine:
            return "raspbian_armhf"
        else:
            sys.exit("Your architecture is not supported")


def download() -> None:
    suffix = get_url_suffix_from_platform()
    sdk_url = f"https://bearware.dk/teamtalksdk/v5.22a/tt5sdk_v5.22a_{suffix}.7z"
    print(f"[fix] Baixando SDK de {sdk_url}")
    downloader.download_file(sdk_url, os.path.join(cd, "ttsdk.7z"))
    print("[fix] Download concluido.")


def extract() -> None:
    try:
        os.mkdir(os.path.join(cd, "ttsdk"))
    except FileExistsError:
        shutil.rmtree(os.path.join(cd, "ttsdk"))
        os.mkdir(os.path.join(cd, "ttsdk"))
    patoolib.extract_archive(os.path.join(cd, "ttsdk.7z"), outdir=os.path.join(cd, "ttsdk"))


def move() -> None:
    path = os.path.join(cd, "ttsdk", os.listdir(os.path.join(cd, "ttsdk"))[0])
    libraries = ["TeamTalk_DLL", "TeamTalkPy"]
    try:
        os.makedirs(os.path.join(cd, "implementation"))
    except FileExistsError:
        shutil.rmtree(os.path.join(cd, "implementation"))
        os.makedirs(os.path.join(cd, "implementation"))
    for library in libraries:
        try:
            os.rename(
                os.path.join(path, "Library", library),
                os.path.join(cd, "implementation", library),
            )
        except OSError:
            shutil.rmtree(os.path.join(cd, "implementation", library))
            os.rename(
                os.path.join(path, "Library", library),
                os.path.join(cd, "implementation", library),
            )
        try:
            os.remove(os.path.join(cd, "implementation", "__init__.py"))
        except OSError:
            pass
        finally:
            with open(os.path.join(cd, "implementation", "__init__.py"), "w") as f:
                f.write("")


def clean() -> None:
    os.remove(os.path.join(cd, "ttsdk.7z"))
    shutil.rmtree(os.path.join(cd, "ttsdk"))
    shutil.rmtree(os.path.join(cd, "implementation", "TeamTalkPy", "test"))


def install() -> None:
    print("Installing TeamTalk sdk components")
    try:
        print("Downloading latest sdk version")
        download()
    except Exception as e:
        print("Failed to download sdk. Error: ", e)
        sys.exit(1)
    try:
        print("Downloaded. extracting")
        extract()
    except patoolib.util.PatoolError as e:
        print("Failed to extract sdk. Error: ", e)
        sys.exit(1)
    print("Extracted. moving")
    move()
    if not os.path.exists(os.path.join(cd, "implementation", "TeamTalk_DLL")):
        print("Failed to move TeamTalk_DLL")
        sys.exit(1)
    if not os.path.exists(os.path.join(cd, "implementation", "TeamTalkPy")):
        print("Failed to move TeamTalkPy")
        sys.exit(1)
    print("moved. cleaning")
    clean()
    print("cleaned.")
    print("Installed")
    sys.exit(0)
'''
    
    with open(target, "w") as f:
        f.write(new_content)
    
    # Remove .pyc para forçar recompilação
    pyc = target + "c"
    if os.path.exists(pyc):
        os.remove(pyc)
    pycache = os.path.join(os.path.dirname(target), "__pycache__")
    if os.path.exists(pycache):
        import glob
        for old in glob.glob(os.path.join(pycache, "ttsdk_downloader*.pyc")):
            os.remove(old)
    
    print(f"[fix] ttsdk_downloader.py reescrito para usar v5.22a.")

_fix_sdk_downloader()

# ── Importações principais ────────────────────────────────────────────────────
import asyncio
import logging
import teamtalk

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ── Configurações do servidor ──────────────────────────────────────────────────
SERVER = {
    "host": "blindmasters.org",
    "port": 19558,
    "username": "ADM.geral2007",
    "password": "2007",
    "nickname": "ZapiaMusic",
    "channel": "/Grupo dos amigos",
    "channel_password": "",
}

AJUDA = (
    "=== ZapiaMusic - Comandos ===\n"
    "h            - mostra esta ajuda\n"
    "t <música>   - toca uma música (ex: t Evidências Chitãozinho)\n"
    "p            - pausa ou continua a música\n"
    "s            - para a música\n"
    "v <0-100>    - ajusta o volume (ex: v 80)"
)

# ── Estado global do bot ───────────────────────────────────────────────────────
pausado = False
streamer_atual = None

# ── Bot ────────────────────────────────────────────────────────────────────────
bot = teamtalk.TeamTalkBot(client_name="ZapiaMusic")


@bot.event
async def on_ready():
    logging.info("Bot conectado e pronto!")
    for tt in bot.teamtalks:
        canal = tt.get_channel(SERVER["channel"])
        if canal:
            tt.join_channel(canal)
            logging.info(f"Entrou no canal: {canal.name}")


@bot.event
async def on_message(message):
    global pausado, streamer_atual

    texto = message.content.strip()
    if not texto:
        return

    canal = message.channel
    tt = message.server

    def get_streamer():
        return teamtalk.Streamer.get_streamer_for_channel(canal)

    # ── h: ajuda ──────────────────────────────────────────────────────────────
    if texto.lower() == "h":
        canal.send_message(AJUDA)
        return

    # ── t <música>: tocar ─────────────────────────────────────────────────────
    if texto.lower().startswith("t "):
        query = texto[2:].strip()
        if not query:
            canal.send_message("Use: t <nome da musica>  (ex: t Evidências Chitãozinho)")
            return
        streamer_atual = get_streamer()
        if not streamer_atual.ffmpeg_available:
            canal.send_message("Erro: ffmpeg não instalado.")
            return
        if not streamer_atual.yt_dlp_available:
            canal.send_message("Erro: yt-dlp não instalado.")
            return
        canal.send_message(f"Procurando: {query}...")
        pausado = False
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, streamer_atual.search_and_stream, query)
        return

    # ── p: pausar/continuar ───────────────────────────────────────────────────
    if texto.lower() == "p":
        s = get_streamer()
        if pausado:
            canal.send_message("Continuando...")
            pausado = False
            canal.send_message("(Nota: use 't <música>' para tocar de novo)")
        else:
            canal.send_message("Pausando...")
            s.stop()
            pausado = True
        return

    # ── s: parar ──────────────────────────────────────────────────────────────
    if texto.lower() == "s":
        s = get_streamer()
        s.stop()
        pausado = False
        canal.send_message("Música parada.")
        return

    # ── v <número>: volume ────────────────────────────────────────────────────
    if texto.lower().startswith("v "):
        try:
            vol = int(texto[2:].strip())
            vol = max(0, min(100, vol))
            s = get_streamer()
            s.volume = vol
            canal.send_message(f"Volume: {vol}%")
        except ValueError:
            canal.send_message("Use: v <0-100>  (ex: v 80)")
        return


# ── Inicialização ──────────────────────────────────────────────────────────────
async def main():
    await bot.add_server(SERVER)
    await bot._start()


if __name__ == "__main__":
    bot.run()

