# MP3/MP4 to AAC Converter

Conversor de linha de comando **em massa** que transforma **qualquer arquivo de áudio ou vídeo** (mp3, wav, flac, mp4, mkv, mov, avi, etc.) em `.aac`, preservando o nome original de cada arquivo e a **estrutura de subpastas**. Usa `ffmpeg` por baixo dos panos, que reconhece o formato automaticamente pelo conteúdo do arquivo (não pela extensão).

Se a origem for um vídeo, apenas o áudio é extraído — o vídeo é descartado automaticamente.

Arquivos que não são áudio/vídeo (ex: `.txt`, `.jpg`) são detectados pelo próprio ffmpeg e reportados como erro, sem travar a conversão dos demais. O único arquivo sempre ignorado é o próprio `.aac` (pra não reconverter o que já foi gerado), além de arquivos de sistema como `.DS_Store`.

## Requisitos

- Python 3.10+
- `ffmpeg` instalado e disponível no PATH

### Instalando o ffmpeg

- **Linux (Debian/Ubuntu):** `sudo apt install ffmpeg`
- **macOS:** `brew install ffmpeg`
- **Windows:** baixe em https://ffmpeg.org/download.html e adicione ao PATH

Para checar se já está instalado:
```bash
ffmpeg -version
```

## Estrutura do projeto

```
mp3-to-aac/
├── main.py            # ponto de entrada (CLI)
├── src/
│   ├── converter.py   # lógica de conversão (chama o ffmpeg)
│   └── utils.py       # funções auxiliares
├── input/              # coloque aqui os arquivos/pastas a converter
├── output/             # os .aac aparecem aqui, na mesma estrutura de input/
└── README.md
```

## Como usar

Sempre rode a partir da pasta raiz do projeto (onde está o `main.py`).

### Modo principal: pastas `input/` e `output/`

Organize seus arquivos dentro de `input/`, usando subpastas à vontade:

```
input/
├── legal/
│   └── gentefina/
│       ├── audio1.mp3
│       └── video1.mkv
└── outrapasta/
    └── audio2.wav
```

Rode:
```bash
python3 main.py
```

O programa espelha automaticamente a mesma estrutura de subpastas dentro de `output/`:

```
output/
├── legal/
│   └── gentefina/
│       ├── audio1.aac
│       └── video1.aac
└── outrapasta/
    └── audio2.aac
```

> O `.aac` é gerado com o mesmo nome do arquivo original, só trocando a extensão — não importa se a origem era `.mp3`, `.wav`, `.mkv`, `.mov`, etc.

Ou seja, `input/legal/gentefina/` gera `output/legal/gentefina/`, não importa quantos níveis de subpasta você tenha.

### Escolher outras pastas de entrada/saída (opcional)

Se não quiser usar `input/`/`output/` na pasta atual:
```bash
python3 main.py -i /caminho/para/entrada -o /caminho/para/saida
```

### Escolher o bitrate (qualidade) do áudio
```bash
python3 main.py -b 256k
```
Valores comuns: `128k`, `192k` (padrão), `256k`, `320k`.

### Sobrescrever arquivos .aac já existentes
Por padrão, se o `.aac` já existir no destino, aquele arquivo é pulado (pra não gastar tempo convertendo de novo). Para forçar a conversão de novo:
```bash
python3 main.py --sobrescrever
```

### Ver todas as opções
```bash
python3 main.py --help
```

## Exemplo de saída

```
🎵 2 arquivo(s) encontrado(s) (2 mp3, 0 mp4, 0 mkv)
📂 Entrada: /home/usuario/mp3-to-aac/input
📁 Saída:   /home/usuario/mp3-to-aac/output
🎚️  Bitrate: 192k

[1/2] ✅ legal/gentefina/audio1.mp3 -> legal/gentefina/audio1.aac (17.9 KB)
[2/2] ✅ outrapasta/audio2.mp3 -> outrapasta/audio2.aac (17.8 KB)

🏁 Concluído: 2 convertido(s), 0 erro(s)/pulado(s).
```

## Observação importante

Se na mesma subpasta existir `video.mp4` **e** `video.mp3` (mesmo nome, extensões diferentes), os dois vão gerar `video.aac` — o segundo será pulado como "já existe" (a menos que use `--sobrescrever`, que aí sobrescreve com o último processado). Isso é raro na prática, mas vale saber.
