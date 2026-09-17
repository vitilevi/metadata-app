"""Mapeamento dos campos do formulário para tags do ExifTool.

Cada campo escreve em múltiplos padrões (EXIF / IPTC / XMP) para que o
metadado seja lido por Lightroom, Photoshop, Finder, Google Fotos, etc.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Field:
    key: str
    label: str
    tags: tuple[str, ...]
    hint: str = ""
    choices: tuple[str, ...] = ()
    multiline: bool = False
    # Quando True, o valor é dividido por vírgula e cada item vira uma
    # ocorrência da tag (listas: keywords, criadores).
    is_list: bool = False


@dataclass(frozen=True)
class Group:
    name: str
    fields: tuple[Field, ...] = field(default_factory=tuple)


CAMERA = Group(
    "Câmera",
    (
        Field("make", "Marca da câmera", ("EXIF:Make", "XMP-tiff:Make"), "Ex.: Canon"),
        Field("model", "Modelo da câmera", ("EXIF:Model", "XMP-tiff:Model"), "Ex.: EOS R6"),
        Field(
            "lens",
            "Lente",
            ("EXIF:LensModel", "EXIF:LensMake", "XMP-exifEX:LensModel", "XMP-aux:Lens"),
            "Ex.: RF 24-70mm F2.8 L IS USM",
        ),
        Field(
            "focal",
            "Distância focal",
            ("EXIF:FocalLength", "XMP-exif:FocalLength"),
            "Ex.: 35 ou 35mm",
        ),
        Field(
            "exposure",
            "Tempo de exposição",
            ("EXIF:ExposureTime", "XMP-exif:ExposureTime"),
            "Ex.: 1/200 ou 0.005",
        ),
        Field(
            "fnumber",
            "Abertura (f/)",
            ("EXIF:FNumber", "XMP-exif:FNumber"),
            "Ex.: 2.8",
        ),
        Field(
            "iso",
            "ISO",
            ("EXIF:ISO", "XMP-exifEX:PhotographicSensitivity"),
            "Ex.: 400",
        ),
        Field(
            "flash",
            "Flash",
            ("EXIF:Flash",),
            "Estado do flash",
            choices=(
                "",
                "No Flash",
                "Fired",
                "Off, Did not fire",
                "On, Fired",
                "Auto, Fired",
                "Auto, Did not fire",
                "Fired, Red-eye reduction",
            ),
        ),
        Field(
            "datetime",
            "Data/hora original",
            (
                "EXIF:DateTimeOriginal",
                "EXIF:CreateDate",
                "EXIF:ModifyDate",
                "XMP:DateTimeOriginal",
                "XMP-photoshop:DateCreated",
                "IPTC:DateCreated",
                "IPTC:TimeCreated",
            ),
            "Formato: 2026:09:17 14:30:00",
        ),
        Field(
            "software",
            "Software",
            ("EXIF:Software", "XMP-xmp:CreatorTool"),
            "Ex.: Lightroom Classic 14.2",
        ),
    ),
)

# GPS é tratado separadamente em exif_writer.py (precisa de Ref N/S/E/W).
GPS = Group(
    "GPS",
    (
        Field("gps_lat", "Latitude", (), "Decimal. Ex.: -23.55052 (sul = negativo)"),
        Field("gps_lon", "Longitude", (), "Decimal. Ex.: -46.63331 (oeste = negativo)"),
        Field("gps_alt", "Altitude (m)", (), "Ex.: 760 (abaixo do nível do mar = negativo)"),
        Field(
            "gps_city",
            "Cidade",
            ("IPTC:City", "XMP-photoshop:City", "XMP-iptcExt:LocationCreatedCity"),
        ),
        Field(
            "gps_state",
            "Estado/Província",
            ("IPTC:Province-State", "XMP-photoshop:State", "XMP-iptcExt:LocationCreatedProvinceState"),
        ),
        Field(
            "gps_country",
            "País",
            (
                "IPTC:Country-PrimaryLocationName",
                "XMP-photoshop:Country",
                "XMP-iptcExt:LocationCreatedCountryName",
            ),
        ),
    ),
)

COPYRIGHT = Group(
    "Direitos autorais",
    (
        Field(
            "rights_owner",
            "Proprietário dos direitos",
            (
                "EXIF:Copyright",
                "IPTC:CopyrightNotice",
                "XMP-dc:Rights",
                "XMP-xmpRights:Owner",
            ),
            "Ex.: © 2026 Estúdio Fulano",
        ),
        Field(
            "rights_usage",
            "Direitos de uso",
            ("XMP-xmpRights:UsageTerms",),
            "Ex.: Uso editorial apenas. Proibida revenda.",
            multiline=True,
        ),
        Field(
            "rights_creator",
            "Criador / Autor",
            ("EXIF:Artist", "IPTC:By-line", "XMP-dc:Creator"),
            "Separe vários por vírgula",
            is_list=True,
        ),
        Field(
            "rights_job",
            "Cargo do criador",
            ("IPTC:By-lineTitle", "XMP-photoshop:AuthorsPosition"),
            "Ex.: Fotógrafo",
        ),
        Field(
            "rights_notice",
            "Aviso legal / Instruções",
            ("IPTC:SpecialInstructions", "XMP-photoshop:Instructions"),
            "Ex.: Não alterar sem autorização do autor.",
            multiline=True,
        ),
        Field(
            "rights_url",
            "URL dos termos",
            ("XMP-xmpRights:WebStatement",),
            "Ex.: https://exemplo.com/licenca",
        ),
        Field(
            "rights_marked",
            "Obra protegida",
            ("XMP-xmpRights:Marked",),
            "True = com direitos autorais, False = domínio público",
            choices=("", "True", "False"),
        ),
        Field(
            "rights_contact",
            "Contato",
            ("IPTC:Contact", "XMP-iptcCore:CreatorWorkEmail"),
            "E-mail de contato",
        ),
    ),
)

EXTRA = Group(
    "Dados adicionais",
    (
        Field("title", "Título", ("IPTC:ObjectName", "XMP-dc:Title")),
        Field(
            "description",
            "Descrição / Legenda",
            ("EXIF:ImageDescription", "IPTC:Caption-Abstract", "XMP-dc:Description"),
            multiline=True,
        ),
        Field(
            "keywords",
            "Palavras-chave",
            ("IPTC:Keywords", "XMP-dc:Subject"),
            "Separe por vírgula",
            is_list=True,
        ),
        Field(
            "credit",
            "Crédito",
            ("IPTC:Credit", "XMP-photoshop:Credit"),
        ),
        Field(
            "source",
            "Fonte",
            ("IPTC:Source", "XMP-photoshop:Source"),
        ),
        Field(
            "rating",
            "Avaliação (0-5)",
            ("XMP-xmp:Rating",),
            choices=("", "0", "1", "2", "3", "4", "5"),
        ),
    ),
)

GROUPS: tuple[Group, ...] = (CAMERA, GPS, COPYRIGHT, EXTRA)

# Campos GPS numéricos tratados à parte pelo writer.
GPS_NUMERIC_KEYS = ("gps_lat", "gps_lon", "gps_alt")

ALL_FIELDS: dict[str, Field] = {
    f.key: f for g in GROUPS for f in g.fields
}

# Extensões que o app aceita (subconjunto gravável do ExifTool).
IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".jpe", ".tif", ".tiff", ".png", ".webp",
    ".heic", ".heif", ".dng", ".cr2", ".cr3", ".nef", ".arw",
    ".orf", ".rw2", ".raf", ".pef", ".srw", ".avif", ".gif",
}
