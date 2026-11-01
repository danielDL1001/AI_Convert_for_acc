import argparse
import sys
from pathlib import Path

from src.converter import converter_mapeados
from src.utils import (
    ffmpeg_disponivel,
    ffprobe_disponivel,
    mapear_arquivos,
    formatar_tamanho,
)


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mp3-to-aac",
        description=(
            "Converte qualquer arquivo de áudio ou vídeo para AAC usando ffmpeg, "
            "preservando a estrutura de subpastas entre 'input/' e 'output/'. "
            "Arquivos que já são AAC não são reconvertidos, apenas copiados."
        ),
    )
    parser.add_argument(
        "-i", "--entrada",
        type=str,
        default="input",
        help="Pasta de entrada (padrão: 'input', ao lado do main.py)",
    )
    parser.add_argument(
        "-o", "--saida",
        type=str,
        default="output",
        help="Pasta de saída (padrão: 'output', ao lado do main.py)",
    )
    parser.add_argument(
        "-b", "--bitrate",
        type=str,
        default="192k",
        help="Bitrate do áudio de saída (padrão: 192k). Ignorado para arquivos que já são AAC.",
    )
    parser.add_argument(
        "--sobrescrever",
        action="store_true",
        help="Sobrescreve arquivos .aac já existentes no destino",
    )
    return parser


def main():
    parser = criar_parser()
    args = parser.parse_args()

    if not ffmpeg_disponivel():
        print("❌ ffmpeg não encontrado no sistema.")
        print("   Instale com: sudo apt install ffmpeg  (Linux)")
        print("                brew install ffmpeg      (macOS)")
        print("   Ou baixe em: https://ffmpeg.org/download.html  (Windows)")
        sys.exit(1)

    if not ffprobe_disponivel():
        print("⚠️  ffprobe não encontrado: não será possível detectar AAC dentro de .m4a/.mp4.")
        print("   Apenas arquivos .aac serão copiados; os demais serão reconvertidos.\n")

    pasta_entrada = Path(args.entrada).expanduser().resolve()
    pasta_saida = Path(args.saida).expanduser().resolve()

    if not pasta_entrada.exists():
        print(f"❌ Pasta de entrada não encontrada: {pasta_entrada}")
        print("   Crie a pasta 'input' (ou informe outra com -i) e coloque os arquivos dentro.")
        sys.exit(1)

    arquivos = mapear_arquivos(pasta_entrada, pasta_saida)

    if not arquivos:
        print(f"⚠️  Nenhum arquivo encontrado em: {pasta_entrada}")
        sys.exit(0)

    contagem_por_extensao: dict[str, int] = {}
    for a in arquivos:
        ext = a.origem.suffix.lower().lstrip(".") or "sem extensão"
        contagem_por_extensao[ext] = contagem_por_extensao.get(ext, 0) + 1
    resumo_extensoes = ", ".join(f"{qtd} {ext}" for ext, qtd in sorted(contagem_por_extensao.items()))

    print(f"🎵 {len(arquivos)} arquivo(s) encontrado(s) ({resumo_extensoes})")
    print(f"📂 Entrada: {pasta_entrada}")
    print(f"📁 Saída:   {pasta_saida}")
    print(f"🎚️  Bitrate: {args.bitrate}\n")

    def mostrar_progresso(indice, total, resultado):
        prefixo = f"[{indice}/{total}]"
        caminho_relativo_origem = resultado.origem.relative_to(pasta_entrada)
        if resultado.sucesso:
            tamanho = formatar_tamanho(resultado.destino.stat().st_size)
            caminho_relativo_destino = resultado.destino.relative_to(pasta_saida)
            if resultado.copiado:
                print(f"{prefixo} 📋 {caminho_relativo_origem} -> {caminho_relativo_destino} ({tamanho}, já era AAC: copiado)")
            else:
                print(f"{prefixo} ✅ {caminho_relativo_origem} -> {caminho_relativo_destino} ({tamanho})")
        else:
            print(f"{prefixo} ❌ {caminho_relativo_origem}: {resultado.erro}")

    resultados = converter_mapeados(
        arquivos,
        bitrate=args.bitrate,
        sobrescrever=args.sobrescrever,
        on_progresso=mostrar_progresso,
    )

    copiados = sum(1 for r in resultados if r.sucesso and r.copiado)
    convertidos = sum(1 for r in resultados if r.sucesso and not r.copiado)
    falhas = len(resultados) - copiados - convertidos

    print(
        f"\n🏁 Concluído: {convertidos} convertido(s), {copiados} copiado(s) (já eram AAC), "
        f"{falhas} erro(s)/pulado(s)."
    )


if __name__ == "__main__":
    main()
