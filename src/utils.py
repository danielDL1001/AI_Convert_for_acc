import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


# Arquivos de sistema/ocultos que NUNCA devem ser tratados como entrada.
# Obs.: arquivos .aac agora SÃO aceitos como entrada: eles são apenas copiados
# para o output, sem reconverter.
ARQUIVOS_IGNORADOS = {".ds_store", "thumbs.db", "desktop.ini"}


def ffmpeg_disponivel() -> bool:
    """Verifica se o ffmpeg está instalado e acessível no PATH."""
    return shutil.which("ffmpeg") is not None


def ffprobe_disponivel() -> bool:
    """Verifica se o ffprobe (que acompanha o ffmpeg) está acessível no PATH."""
    return shutil.which("ffprobe") is not None


def codec_audio(caminho: Path) -> str | None:
    """
    Retorna o codec do primeiro stream de áudio do arquivo (ex: 'aac', 'mp3'),
    ou None se não for possível detectar (sem ffprobe, sem áudio, arquivo inválido...).
    """
    try:
        resultado = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-select_streams", "a:0",
                "-show_entries", "stream=codec_name",
                "-of", "default=nw=1:nk=1",
                str(caminho),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )
    except (subprocess.SubprocessError, OSError):
        return None

    return resultado.stdout.strip().splitlines()[0] if resultado.stdout.strip() else None


def e_aac_puro(caminho: Path) -> bool:
    """True se o arquivo já é um .aac (mesmo formato de saída): basta copiar."""
    return caminho.suffix.lower() == ".aac"


def tem_audio_aac(caminho: Path) -> bool:
    """True se o áudio do arquivo já está codificado em AAC (ex: .m4a, .mp4)."""
    return codec_audio(caminho) == "aac"


def _e_arquivo_valido(arquivo: Path) -> bool:
    """Filtra arquivos ocultos/de sistema, aceitando qualquer outro arquivo
    (áudio ou vídeo, inclusive .aac) para que o conversor decida o que fazer."""
    if arquivo.name.lower() in ARQUIVOS_IGNORADOS:
        return False
    if arquivo.name.startswith("."):
        return False
    return True


@dataclass
class ArquivoParaConverter:
    origem: Path        # caminho completo do arquivo de entrada
    pasta_saida: Path    # pasta de destino correspondente (já espelhando a estrutura)


def mapear_arquivos(
    pasta_entrada: Path,
    pasta_saida_raiz: Path,
) -> list[ArquivoParaConverter]:
    """
    Varre 'pasta_entrada' recursivamente e, para cada arquivo encontrado (qualquer
    áudio ou vídeo, exceto arquivos de sistema), calcula qual seria a pasta
    de destino correspondente dentro de 'pasta_saida_raiz', espelhando a mesma
    estrutura de subpastas.

    Exemplo:
        pasta_entrada  = input/
        pasta_saida_raiz = output/
        input/legal/gentefina/audio.mp3 -> pasta de saída: output/legal/gentefina/
    """
    if not pasta_entrada.is_dir():
        return []

    encontrados = []
    for arquivo in sorted(pasta_entrada.rglob("*")):
        if arquivo.is_file() and _e_arquivo_valido(arquivo):
            caminho_relativo = arquivo.relative_to(pasta_entrada)
            pasta_saida_correspondente = pasta_saida_raiz / caminho_relativo.parent
            encontrados.append(
                ArquivoParaConverter(origem=arquivo, pasta_saida=pasta_saida_correspondente)
            )

    return encontrados


def listar_arquivos(caminho: Path) -> list[Path]:
    """
    Retorna uma lista de arquivos a converter, sem se preocupar com estrutura.
    - Se 'caminho' for um arquivo válido (não de sistema), retorna só ele.
    - Se 'caminho' for uma pasta, retorna todos os arquivos válidos encontrados (recursivo).

    Mantido para compatibilidade (uso com um único arquivo de entrada).
    """
    if caminho.is_file():
        if _e_arquivo_valido(caminho):
            return [caminho]
        return []

    if caminho.is_dir():
        encontrados = [
            arquivo for arquivo in caminho.rglob("*")
            if arquivo.is_file() and _e_arquivo_valido(arquivo)
        ]
        return sorted(encontrados)

    return []


def formatar_tamanho(bytes_: int) -> str:
    """Converte bytes em um texto legível (KB, MB...)."""
    tamanho = float(bytes_)
    for unidade in ["B", "KB", "MB", "GB"]:
        if tamanho < 1024:
            return f"{tamanho:.1f} {unidade}"
        tamanho /= 1024
    return f"{tamanho:.1f} TB"
