import subprocess
from dataclasses import dataclass
from pathlib import Path

from .utils import ArquivoParaConverter


@dataclass
class ResultadoConversao:
    origem: Path
    destino: Path | None
    sucesso: bool
    erro: str | None = None


def converter_arquivo(
    origem: Path,
    pasta_saida: Path,
    bitrate: str = "192k",
    sobrescrever: bool = False,
) -> ResultadoConversao:
    """
    Converte um único arquivo de áudio ou vídeo (.mp3 ou .mp4) para .aac usando ffmpeg.
    O '-vn' garante que, se a origem for um vídeo, só o áudio é extraído (o vídeo é descartado).

    Args:
        origem: caminho do arquivo .mp3 ou .mp4 de entrada.
        pasta_saida: pasta onde o .aac será salvo.
        bitrate: taxa de bits do áudio de saída (ex: '128k', '192k', '256k').
        sobrescrever: se True, sobrescreve o arquivo de saída caso já exista.
    """
    pasta_saida.mkdir(parents=True, exist_ok=True)
    destino = pasta_saida / (origem.stem + ".aac")

    if destino.exists() and not sobrescrever:
        return ResultadoConversao(
            origem=origem,
            destino=destino,
            sucesso=False,
            erro="Arquivo de destino já existe (use --sobrescrever para substituir).",
        )

    comando = [
        "ffmpeg",
        "-y" if sobrescrever else "-n",
        "-i", str(origem),
        "-vn",                 # ignora qualquer stream de vídeo/capa embutida
        "-c:a", "aac",
        "-b:a", bitrate,
        str(destino),
    ]

    try:
        processo = subprocess.run(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError:
        return ResultadoConversao(
            origem=origem,
            destino=None,
            sucesso=False,
            erro="ffmpeg não encontrado. Instale o ffmpeg e garanta que está no PATH.",
        )

    if processo.returncode != 0:
        # Pega só a última linha útil do stderr do ffmpeg como resumo do erro
        ultima_linha = processo.stderr.strip().splitlines()[-1] if processo.stderr else "Erro desconhecido"
        return ResultadoConversao(
            origem=origem,
            destino=None,
            sucesso=False,
            erro=ultima_linha,
        )

    return ResultadoConversao(origem=origem, destino=destino, sucesso=True)


def converter_varios(
    arquivos: list[Path],
    pasta_saida: Path,
    bitrate: str = "192k",
    sobrescrever: bool = False,
    on_progresso=None,
) -> list[ResultadoConversao]:
    """
    Converte uma lista de arquivos (.mp3 e/ou .mp4) para .aac, em massa,
    todos para a MESMA pasta de saída.

    on_progresso: callback opcional chamado após cada arquivo,
                  recebendo (indice_atual, total, ResultadoConversao).
    """
    resultados = []
    total = len(arquivos)

    for i, arquivo in enumerate(arquivos, start=1):
        resultado = converter_arquivo(arquivo, pasta_saida, bitrate, sobrescrever)
        resultados.append(resultado)

        if on_progresso:
            on_progresso(i, total, resultado)

    return resultados


def converter_mapeados(
    arquivos: list[ArquivoParaConverter],
    bitrate: str = "192k",
    sobrescrever: bool = False,
    on_progresso=None,
) -> list[ResultadoConversao]:
    """
    Converte uma lista de ArquivoParaConverter (origem + pasta_saida já calculada
    individualmente para cada arquivo), preservando a estrutura de subpastas.

    on_progresso: callback opcional chamado após cada arquivo,
                  recebendo (indice_atual, total, ResultadoConversao).
    """
    resultados = []
    total = len(arquivos)

    for i, item in enumerate(arquivos, start=1):
        resultado = converter_arquivo(item.origem, item.pasta_saida, bitrate, sobrescrever)
        resultados.append(resultado)

        if on_progresso:
            on_progresso(i, total, resultado)

    return resultados
