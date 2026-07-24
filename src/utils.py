import shutil
from dataclasses import dataclass
from pathlib import Path


# Arquivos que NUNCA devem ser tratados como entrada a converter:
# - .aac: já é o formato de saída (evita reconverter o que já foi gerado)
# - arquivos ocultos/de sistema comuns, caso o usuário tenha alguma sincronização
EXTENSOES_IGNORADAS = (".aac",)
ARQUIVOS_IGNORADOS = {".ds_store", "thumbs.db", "desktop.ini"}


def ffmpeg_disponivel() -> bool:
    """Verifica se o ffmpeg está instalado e acessível no PATH."""
    return shutil.which("ffmpeg") is not None


def _e_arquivo_valido(arquivo: Path) -> bool:
    """Filtra arquivos ocultos/de sistema e o próprio .aac, aceitando qualquer outro
    arquivo (áudio ou vídeo) para que o ffmpeg tente a conversão."""
    if arquivo.name.lower() in ARQUIVOS_IGNORADOS:
        return False
    if arquivo.name.startswith("."):
        return False
    if arquivo.suffix.lower() in EXTENSOES_IGNORADAS:
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
    áudio ou vídeo, exceto .aac e arquivos de sistema), calcula qual seria a pasta
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
    - Se 'caminho' for um arquivo válido (não .aac/sistema), retorna só ele.
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
