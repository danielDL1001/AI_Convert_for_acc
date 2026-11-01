import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .utils import ArquivoParaConverter, e_aac_puro, tem_audio_aac


@dataclass
class ResultadoConversao:
    origem: Path
    destino: Path | None
    sucesso: bool
    erro: str | None = None
    copiado: bool = False  # True quando o áudio já era AAC e não foi reconvertido


def _executar_ffmpeg(comando: list[str]) -> str | None:
    """Executa o ffmpeg. Retorna None se deu certo, ou uma mensagem de erro."""
    try:
        processo = subprocess.run(
            comando,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError:
        return "ffmpeg não encontrado. Instale o ffmpeg e garanta que está no PATH."

    if processo.returncode != 0:
        # Pega só a última linha útil do stderr do ffmpeg como resumo do erro
        return processo.stderr.strip().splitlines()[-1] if processo.stderr.strip() else "Erro desconhecido"

    return None


def converter_arquivo(
    origem: Path,
    pasta_saida: Path,
    bitrate: str = "192k",
    sobrescrever: bool = False,
) -> ResultadoConversao:
    """
    Processa um único arquivo de áudio ou vídeo e gera um .aac na pasta de saída:

    - Se a origem já é um .aac: apenas copia o arquivo para o destino.
    - Se a origem contém áudio AAC dentro de outro container (.m4a, .mp4...):
      extrai o stream com '-c:a copy' (sem reencodar, sem perda de qualidade).
    - Caso contrário: converte para AAC com ffmpeg usando o bitrate informado.
      O '-vn' garante que, se a origem for um vídeo, só o áudio é extraído.

    Args:
        origem: caminho do arquivo de entrada.
        pasta_saida: pasta onde o .aac será salvo.
        bitrate: taxa de bits do áudio de saída (ex: '128k', '192k', '256k').
                 Ignorado quando o áudio já é AAC.
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

    # Caso 1: já é .aac -> só recopia
    if e_aac_puro(origem):
        try:
            shutil.copy2(origem, destino)
        except OSError as e:
            return ResultadoConversao(
                origem=origem, destino=None, sucesso=False, erro=f"Falha ao copiar: {e}"
            )
        return ResultadoConversao(origem=origem, destino=destino, sucesso=True, copiado=True)

    flag_sobrescrita = "-y" if sobrescrever else "-n"

    # Caso 2: áudio já é AAC em outro container -> extrai o stream sem reencodar
    if tem_audio_aac(origem):
        comando = [
            "ffmpeg",
            flag_sobrescrita,
            "-i", str(origem),
            "-vn",
            "-c:a", "copy",
            str(destino),
        ]
        erro = _executar_ffmpeg(comando)
        if erro is None:
            return ResultadoConversao(origem=origem, destino=destino, sucesso=True, copiado=True)
        # Se o copy falhar por algum motivo, cai para a conversão normal abaixo.

    # Caso 3: conversão normal
    comando = [
        "ffmpeg",
        flag_sobrescrita,
        "-i", str(origem),
        "-vn",                 # ignora qualquer stream de vídeo/capa embutida
        "-c:a", "aac",
        "-b:a", bitrate,
        str(destino),
    ]
    erro = _executar_ffmpeg(comando)
    if erro is not None:
        return ResultadoConversao(origem=origem, destino=None, sucesso=False, erro=erro)

    return ResultadoConversao(origem=origem, destino=destino, sucesso=True)


def converter_varios(
    arquivos: list[Path],
    pasta_saida: Path,
    bitrate: str = "192k",
    sobrescrever: bool = False,
    on_progresso=None,
) -> list[ResultadoConversao]:
    """
    Processa uma lista de arquivos para .aac, em massa,
    todos para a MESMA pasta de saída (arquivos já AAC são apenas copiados).

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
    Processa uma lista de ArquivoParaConverter (origem + pasta_saida já calculada
    individualmente para cada arquivo), preservando a estrutura de subpastas.
    Arquivos que já são AAC são apenas copiados para o output.

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
