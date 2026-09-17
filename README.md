# Metadados de Imagem

App desktop para gravar os **mesmos metadados em várias fotos de uma vez** —
uma pasta inteira ou apenas as imagens selecionadas na lista.
Roda em **Windows, macOS e Linux**.

Escreve EXIF, IPTC e XMP simultaneamente, então o resultado é lido por Lightroom,
Photoshop, Explorer/Finder, Google Fotos, bancos de imagem e afins.

---

## Instalação e execução

Dois pré-requisitos em qualquer sistema: **Python 3.10+ com Tkinter** e
**ExifTool**. Nenhuma dependência pip — Tkinter é biblioteca padrão e o ExifTool é
chamado por subprocess. Os lançadores (`run.bat` / `run.command`) checam os dois
antes de abrir e tentam instalar o ExifTool se ele faltar.

<details open>
<summary><b>Windows</b></summary>

**1. Python** — instale por [python.org/downloads](https://www.python.org/downloads/)
e marque as opções **“Add python.exe to PATH”** e **“tcl/tk and IDLE”**.
Ou via winget:

```powershell
winget install -e --id Python.Python.3.12
```

**2. ExifTool**

```powershell
winget install -e --id OliverBetz.ExifTool
```

Sem winget: baixe o *Windows Executable* em [exiftool.org](https://exiftool.org),
renomeie `exiftool(-k).exe` para `exiftool.exe` e coloque numa pasta do PATH **ou**
numa subpasta `exiftool\` ao lado do `app.py`. O app também procura em
`C:\Program Files\ExifTool` e `C:\exiftool`, e aceita o nome original
`exiftool(-k).exe`.

**3. Abrir** — duplo clique em **`run.bat`**. Pelo terminal:

```powershell
cd caminho\para\metadata-app
py -3 app.py
```

O `run.bat` abre o app com `pyw`/`pythonw`, ou seja, sem janela de console. Se algo
falhar antes disso, o próprio `.bat` mostra a mensagem e espera um Enter.

</details>

<details open>
<summary><b>macOS</b></summary>

**1. Python** — já vem no sistema. Se `python3 -c "import tkinter"` falhar,
instale o Python oficial de [python.org](https://www.python.org/downloads/)
(o do Xcode/Command Line Tools às vezes vem sem Tk).

**2. ExifTool**

```bash
brew install exiftool
```

**3. Abrir** — duplo clique em **`run.command`**. Pelo terminal:

```bash
cd ~/projects/metadata-app && python3 app.py
```

Se o macOS bloquear o `run.command` na primeira vez (“não pôde ser aberto”),
clique com o botão direito → **Abrir** → **Abrir**, ou libere a execução:

```bash
chmod +x run.command
```

</details>

<details open>
<summary><b>Linux</b></summary>

**1. Python + Tkinter** (o Tk costuma vir em pacote separado)

```bash
sudo apt install python3 python3-tk        # Debian/Ubuntu
```

```bash
sudo dnf install python3 python3-tkinter    # Fedora
```

**2. ExifTool**

```bash
sudo apt install libimage-exiftool-perl     # Debian/Ubuntu
```

```bash
sudo dnf install perl-Image-ExifTool        # Fedora
```

```bash
sudo pacman -S perl-image-exiftool          # Arch
```

**3. Abrir**

```bash
cd ~/projects/metadata-app && bash run.command
```

Ou direto: `python3 app.py`. O `run.command` detecta apt/dnf/pacman e oferece
instalar o ExifTool se faltar.

</details>

### Verificar a instalação

```bash
python3 -c "import tkinter; print('tkinter ok')" && exiftool -ver
```

No Windows, troque `python3` por `py -3`. Saída esperada: `tkinter ok` seguido do
número da versão do ExifTool (ex.: `13.55`).

### Problemas comuns

| Sintoma | Causa e solução |
|---|---|
| “ExifTool não encontrado” mesmo instalado | não está no PATH. No Windows, ponha o `exiftool.exe` na subpasta `exiftool\` do projeto — o app procura lá. |
| `ModuleNotFoundError: No module named 'tkinter'` | Python sem Tk: Linux → instale `python3-tk`; Windows → reinstale marcando *tcl/tk and IDLE*; macOS → use o Python de python.org. |
| Janela abre borrada no Windows | resolvido via DPI awareness; se persistir, confira a escala do monitor nas configurações de vídeo. |
| Acentos e `©` saem trocados | rode sempre pelos lançadores; eles garantem o ambiente UTF-8 usado nas chamadas ao ExifTool. |
| Nada acontece ao dar duplo clique no `run.bat` | abra o PowerShell na pasta e rode `py -3 app.py` para ver a mensagem de erro. |

---

## Fluxo de uso

1. **Adicionar pasta…** (com ou sem subpastas) ou **Adicionar arquivos…**
2. Marque *"Aplicar somente nas imagens selecionadas"* para atingir um subconjunto —
   selecione na lista com clique, Shift+clique ou Cmd+clique (Ctrl+clique no
   Windows e Linux).
3. Preencha as abas **Câmera**, **GPS**, **Direitos autorais**, **Dados adicionais**
   e **Tags manuais**. Campos em branco são ignorados.
4. Escolha o modo de gravação:
   - **Nos arquivos originais** — com backup `foto.jpg_original` (recomendado).
   - **Cópias em outra pasta** — originais ficam intactos.
5. **Aplicar metadados**. O log mostra atualizadas e falhas.

Botões úteis:

- **Ler metadados da imagem selecionada** — preenche o formulário a partir de uma
  foto existente (bom para replicar os dados de uma foto em todo o lote).
- **Salvar / Carregar preset** — guarda o conjunto de campos em JSON
  (`*.metapreset.json`) para reaproveitar em outro dia.

---

## O que é gravado

| Campo do formulário | Tags escritas |
|---|---|
| Marca / Modelo | `EXIF:Make`, `EXIF:Model`, `XMP-tiff:*` |
| Lente | `EXIF:LensModel`, `EXIF:LensMake`, `XMP-exifEX:LensModel`, `XMP-aux:Lens` |
| Distância focal | `EXIF:FocalLength`, `XMP-exif:FocalLength` |
| Tempo de exposição | `EXIF:ExposureTime` (aceita `1/200`) |
| Abertura | `EXIF:FNumber` |
| ISO | `EXIF:ISO`, `XMP-exifEX:PhotographicSensitivity` |
| Flash | `EXIF:Flash` |
| Data/hora original | `EXIF:DateTimeOriginal/CreateDate/ModifyDate`, `IPTC:DateCreated`, XMP |
| GPS | `EXIF:GPSLatitude/Longitude/Altitude` + refs N/S/E/W, `XMP:GPS*` |
| Cidade / Estado / País | `IPTC:City`, `IPTC:Province-State`, `IPTC:Country-PrimaryLocationName`, `XMP-photoshop:*`, `XMP-iptcExt:*` |
| Proprietário dos direitos | `EXIF:Copyright`, `IPTC:CopyrightNotice`, `XMP-dc:Rights`, `XMP-xmpRights:Owner` |
| Direitos de uso | `XMP-xmpRights:UsageTerms` |
| Criador / Cargo | `EXIF:Artist`, `IPTC:By-line`, `XMP-dc:Creator`, `IPTC:By-lineTitle` |
| Aviso legal | `IPTC:SpecialInstructions`, `XMP-photoshop:Instructions` |
| URL dos termos / Obra protegida | `XMP-xmpRights:WebStatement`, `XMP-xmpRights:Marked` |
| Título / Descrição / Palavras-chave | `IPTC:ObjectName`, `IPTC:Caption-Abstract`, `IPTC:Keywords`, `XMP-dc:*` |
| Crédito / Fonte / Rating | `IPTC:Credit`, `IPTC:Source`, `XMP-xmp:Rating` |

**GPS** usa graus decimais: sul e oeste são **negativos** (`-23.55052`, `-46.63331`).
O app converte para o formato EXIF e preenche as referências N/S/E/W.

**Campos de lista** (palavras-chave, criador) aceitam vários itens separados por
vírgula; em EXIF, que não tem tags de lista, viram uma string única separada por `;`.

---

## Opções de gravação

- **Backup do original** — cria `foto.jpg_original` ao lado do arquivo.
- **Preservar data de modificação** — o arquivo não “envelhece” no Finder (`-P`).
- **Apagar tags em branco** — remove das imagens todo campo deixado vazio.
  Use com cuidado: apaga metadados já existentes.

---

## Estrutura do projeto

```
metadata-app/
├── app.py           # interface Tkinter: lista, abas, opções, log, thread worker
├── exif_writer.py   # camada sobre o ExifTool: args, lotes, cópia, leitura
├── tags.py          # mapa campo → tags EXIF/IPTC/XMP + extensões suportadas
├── run.bat          # atalho de abertura no Windows
├── run.command      # atalho de abertura no macOS (e `bash run.command` no Linux)
└── README.md
```

### Arquitetura

- **`tags.py`** é a fonte da verdade. Cada `Field` tem `key`, rótulo, a tupla de tags
  e flags (`choices`, `multiline`, `is_list`). O formulário da UI é construído a
  partir dessa estrutura — **adicionar um campo novo é só adicionar um `Field`**.
- **`exif_writer.py`** converte o formulário em argumentos do ExifTool, grava via
  arquivo de argumentos temporário em UTF-8 (`-@`), processa em lotes de 150 arquivos
  e devolve contagem de atualizadas/falhas. GPS tem tratamento próprio por causa das
  referências N/S/E/W.
- **`app.py`** só cuida de UI e estado. A gravação roda em thread separada e se
  comunica com a interface por `queue.Queue`, então a janela não congela em lotes
  grandes.

### Desenvolvimento

Gerar imagens de teste e rodar um ciclo grava → lê de volta.

Ambiente virtual — macOS/Linux:

```bash
python3 -m venv .venv && .venv/bin/pip install pillow
```

Windows (PowerShell):

```powershell
py -3 -m venv .venv; .venv\Scripts\pip install pillow
```

Gerar as imagens (troque `.venv/bin/python` por `.venv\Scripts\python` no Windows):

```bash
.venv/bin/python -c "from PIL import Image; import pathlib; d=pathlib.Path('testdata'); d.mkdir(exist_ok=True); [Image.new('RGB',(64,48),(30*i,90,160)).save(d/f'foto_{i}.jpg') for i in range(3)]"
```

Inspecionar o que foi gravado em uma imagem:

```bash
exiftool -G -a -s testdata/foto_0.jpg
```

---

## Formatos suportados

JPEG, TIFF, PNG, WebP, HEIC/HEIF, AVIF, GIF e RAW (DNG, CR2, CR3, NEF, ARW, ORF,
RW2, RAF, PEF, SRW).

RAW aceita gravação, mas mexer no RAW original é sempre mais arriscado — prefira o
modo de cópia para esses.

## Notas de portabilidade

- No Windows o app procura o `exiftool.exe` fora do PATH (pasta do projeto,
  `exiftool\`, Program Files, `C:\exiftool`) e aceita o nome original
  `exiftool(-k).exe`.
- Chamadas ao ExifTool usam `CREATE_NO_WINDOW` no Windows, senão um console
  piscaria a cada lote.
- Entrada e saída do ExifTool são forçadas em UTF-8 — sem isso, acentos e `©`
  quebrariam no console cp1252 do Windows.
- `run.bat` abre o app com `pyw`/`pythonw` (sem console). Erros inesperados
  aparecem em uma caixa de diálogo, já que não haveria terminal para mostrá-los.
- A UI usa o tema nativo de cada sistema (`vista`, `aqua`, `clam`) e ativa
  DPI awareness no Windows para não ficar borrada em telas com escala.
- `.gitattributes` mantém `run.bat` com CRLF e os demais scripts com LF.

## Limitações conhecidas

- PNG e GIF têm suporte parcial a EXIF pelo padrão do formato; XMP funciona bem.
- Sem desfazer em massa: para reverter, use o backup `_original` ou o modo de cópia.
