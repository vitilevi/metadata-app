# Metadados de Imagem

App desktop (macOS) para gravar os **mesmos metadados em várias fotos de uma vez** —
uma pasta inteira ou apenas as imagens selecionadas na lista.

Escreve EXIF, IPTC e XMP simultaneamente, então o resultado é lido por Lightroom,
Photoshop, Finder, Google Fotos, bancos de imagem e afins.

---

## Como rodar

Roda em **Windows, macOS e Linux**. Os lançadores checam Python, Tkinter e
ExifTool antes de abrir e tentam instalar o ExifTool se ele faltar.

| Sistema | Como abrir |
|---|---|
| Windows | duplo clique em `run.bat` |
| macOS | duplo clique em `run.command` |
| Linux | `bash run.command` |

Ou direto pelo terminal, de qualquer sistema:

```bash
python3 app.py
```

### Requisitos

| Item | Windows | macOS | Linux |
|---|---|---|---|
| Python 3.10+ com Tkinter | [python.org](https://www.python.org/downloads/) — marque *Add python.exe to PATH* e *tcl/tk and IDLE* | já vem no sistema | `sudo apt install python3 python3-tk` |
| ExifTool | `winget install OliverBetz.ExifTool` | `brew install exiftool` | `sudo apt install libimage-exiftool-perl` |
| Pillow (só para gerar imagens de teste) | `pip install pillow` | idem | idem |

Nenhuma dependência pip para uso normal — Tkinter é stdlib e o ExifTool é chamado
por subprocess.

**Windows sem winget:** baixe o pacote em [exiftool.org](https://exiftool.org),
renomeie `exiftool(-k).exe` para `exiftool.exe` e coloque numa pasta do PATH **ou**
numa subpasta `exiftool\` ao lado do `app.py` — o programa procura nos dois lugares,
além de `C:\Program Files\ExifTool` e `C:\exiftool`.

---

## Fluxo de uso

1. **Adicionar pasta…** (com ou sem subpastas) ou **Adicionar arquivos…**
2. Marque *"Aplicar somente nas imagens selecionadas"* para atingir um subconjunto —
   selecione na lista com clique, Shift+clique ou Cmd+clique.
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

Gerar imagens de teste e rodar um ciclo grava → lê de volta:

```bash
python3 -m venv .venv && .venv/bin/pip install pillow
```

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
