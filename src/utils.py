import shutil
from dataclasses import dataclass
from pathlib import Path


EXTENSOES_SUPORTADAS = (".mp3", ".mp4")


def ffmpeg_disponivel() -> bool:
    """Verifica se o ffmpeg está instalado e acessível no PATH."""
    return shutil.which("ffmpeg") is not None


@dataclass
class ArquivoParaConverter:
    origem: Path        # caminho completo do arquivo de entrada
    pasta_saida: Path    # pasta de destino correspondente (já espelhando a estrutura)


def mapear_arquivos(
    pasta_entrada: Path,
    pasta_saida_raiz: Path,
    extensoes: tuple[str, ...] = EXTENSOES_SUPORTADAS,
) -> list[ArquivoParaConverter]:
    """
    Varre 'pasta_entrada' recursivamente e, para cada arquivo suportado encontrado,
    calcula qual seria a pasta de destino correspondente dentro de 'pasta_saida_raiz',
    espelhando a mesma estrutura de subpastas.

    Exemplo:
        pasta_entrada  = input/
        pasta_saida_raiz = output/
        input/legal/gentefina/audio.mp3 -> pasta de saída: output/legal/gentefina/
    """
    extensoes = tuple(e.lower() for e in extensoes)

    if not pasta_entrada.is_dir():
        return []

    encontrados = []
    for arquivo in sorted(pasta_entrada.rglob("*")):
        if arquivo.is_file() and arquivo.suffix.lower() in extensoes:
            caminho_relativo = arquivo.relative_to(pasta_entrada)
            pasta_saida_correspondente = pasta_saida_raiz / caminho_relativo.parent
            encontrados.append(
                ArquivoParaConverter(origem=arquivo, pasta_saida=pasta_saida_correspondente)
            )

    return encontrados


def listar_arquivos(caminho: Path, extensoes: tuple[str, ...] = EXTENSOES_SUPORTADAS) -> list[Path]:
    """
    Retorna uma lista de arquivos a converter (mp3 e/ou mp4), sem se preocupar com estrutura.
    - Se 'caminho' for um arquivo com extensão suportada, retorna só ele.
    - Se 'caminho' for uma pasta, retorna todos os arquivos suportados encontrados (recursivo).

    Mantido para compatibilidade (uso com um único arquivo de entrada).
    """
    extensoes = tuple(e.lower() for e in extensoes)

    if caminho.is_file():
        if caminho.suffix.lower() in extensoes:
            return [caminho]
        return []

    if caminho.is_dir():
        encontrados = [
            arquivo for arquivo in caminho.rglob("*")
            if arquivo.is_file() and arquivo.suffix.lower() in extensoes
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
