# Metadados de Imagem

App desktop (macOS) para gravar os **mesmos metadados em várias fotos de uma vez** —
uma pasta inteira ou apenas as imagens selecionadas na lista.

Escreve EXIF, IPTC e XMP simultaneamente, então o resultado é lido por Lightroom,
Photoshop, Finder, Google Fotos, bancos de imagem e afins.

---

## Como rodar

Duplo clique em `run.command` (instala o ExifTool se faltar), ou pelo terminal:

```bash
cd ~/projects/metadata-app && python3 app.py
```

### Requisitos

| Item | Como obter | Obrigatório |
|---|---|---|
| Python 3.10+ com Tkinter | já vem no macOS | sim |
| ExifTool | `brew install exiftool` | sim |
| Pillow | `pip install pillow` | só para gerar imagens de teste |

Nenhuma dependência pip para uso normal — Tkinter é stdlib e o ExifTool é chamado
por subprocess.

```bash
brew install exiftool
```

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
├── run.command      # atalho de abertura (duplo clique)
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

## Limitações conhecidas

- macOS apenas no `run.command`; o `app.py` roda em Linux/Windows com Python+Tk,
  desde que o ExifTool esteja no PATH.
- PNG e GIF têm suporte parcial a EXIF pelo padrão do formato; XMP funciona bem.
- Sem desfazer em massa: para reverter, use o backup `_original` ou o modo de cópia.
