"""Camada de gravação de metadados sobre o ExifTool."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence

from tags import ALL_FIELDS, GPS_NUMERIC_KEYS, IMAGE_EXTENSIONS

CHUNK_SIZE = 150


class ExifToolMissing(RuntimeError):
    pass


def exiftool_path() -> str:
    path = shutil.which("exiftool")
    if not path:
        raise ExifToolMissing(
            "ExifTool não encontrado no PATH.\n\n"
            "Instale com:  brew install exiftool"
        )
    return path


def exiftool_version() -> str:
    out = subprocess.run(
        [exiftool_path(), "-ver"], capture_output=True, text=True, check=False
    )
    return out.stdout.strip() or "?"


@dataclass
class WriteResult:
    updated: int = 0
    failed: int = 0
    messages: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.messages is None:
            self.messages = []


def collect_images(paths: Iterable[str | os.PathLike[str]], recursive: bool = True) -> list[Path]:
    """Expande arquivos e pastas em uma lista de imagens suportadas."""
    found: list[Path] = []
    seen: set[Path] = set()
    for raw in paths:
        p = Path(raw).expanduser()
        candidates: Iterable[Path]
        if p.is_dir():
            candidates = sorted(p.rglob("*") if recursive else p.glob("*"))
        else:
            candidates = [p]
        for c in candidates:
            if not c.is_file():
                continue
            if c.name.startswith("._"):  # resource forks do macOS
                continue
            if c.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            resolved = c.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            found.append(resolved)
    return found


def _decimal(value: str) -> float | None:
    try:
        return float(value.replace(",", ".").strip())
    except ValueError:
        return None


def build_args(
    values: dict[str, str],
    custom: Sequence[tuple[str, str]] = (),
    clear_missing: bool = False,
) -> tuple[list[str], list[str]]:
    """Converte o formulário em argumentos do ExifTool.

    Retorna (args, avisos). Campos vazios são ignorados, a menos que
    `clear_missing` esteja ativo — nesse caso a tag é apagada das imagens.
    """
    args: list[str] = []
    warnings: list[str] = []

    for key, field in ALL_FIELDS.items():
        if key in GPS_NUMERIC_KEYS:
            continue
        raw = (values.get(key) or "").strip()
        if not raw:
            if clear_missing and field.tags:
                args.extend(f"-{tag}=" for tag in field.tags)
            continue
        if field.is_list:
            items = [i.strip() for i in raw.split(",") if i.strip()]
            for tag in field.tags:
                if tag.startswith("EXIF:"):
                    # EXIF não tem tags de lista: grava tudo em uma string.
                    args.append(f"-{tag}={'; '.join(items)}")
                    continue
                args.append(f"-{tag}=")  # limpa a lista antes de reescrever
                args.extend(f"-{tag}={item}" for item in items)
        else:
            args.extend(f"-{tag}={raw}" for tag in field.tags)

    args.extend(_gps_args(values, clear_missing, warnings))

    for tag, value in custom:
        tag = tag.strip().lstrip("-")
        if not tag:
            continue
        args.append(f"-{tag}={value.strip()}")

    return args, warnings


def _gps_args(values: dict[str, str], clear_missing: bool, warnings: list[str]) -> list[str]:
    args: list[str] = []

    lat_raw = (values.get("gps_lat") or "").strip()
    lon_raw = (values.get("gps_lon") or "").strip()
    alt_raw = (values.get("gps_alt") or "").strip()

    if lat_raw:
        lat = _decimal(lat_raw)
        if lat is None or not -90 <= lat <= 90:
            warnings.append(f"Latitude inválida ignorada: {lat_raw!r}")
        else:
            ref = "N" if lat >= 0 else "S"
            args += [
                f"-EXIF:GPSLatitude={abs(lat)}",
                f"-EXIF:GPSLatitudeRef={ref}",
                f"-XMP:GPSLatitude={lat}",
            ]
    elif clear_missing:
        args += ["-EXIF:GPSLatitude=", "-EXIF:GPSLatitudeRef=", "-XMP:GPSLatitude="]

    if lon_raw:
        lon = _decimal(lon_raw)
        if lon is None or not -180 <= lon <= 180:
            warnings.append(f"Longitude inválida ignorada: {lon_raw!r}")
        else:
            ref = "E" if lon >= 0 else "W"
            args += [
                f"-EXIF:GPSLongitude={abs(lon)}",
                f"-EXIF:GPSLongitudeRef={ref}",
                f"-XMP:GPSLongitude={lon}",
            ]
    elif clear_missing:
        args += ["-EXIF:GPSLongitude=", "-EXIF:GPSLongitudeRef=", "-XMP:GPSLongitude="]

    if alt_raw:
        alt = _decimal(alt_raw)
        if alt is None:
            warnings.append(f"Altitude inválida ignorada: {alt_raw!r}")
        else:
            args += [
                f"-EXIF:GPSAltitude={abs(alt)}",
                f"-EXIF:GPSAltitudeRef={'Above Sea Level' if alt >= 0 else 'Below Sea Level'}",
                f"-XMP:GPSAltitude={alt}",
            ]
    elif clear_missing:
        args += ["-EXIF:GPSAltitude=", "-EXIF:GPSAltitudeRef=", "-XMP:GPSAltitude="]

    return args


def _unique_destination(dest_dir: Path, name: str) -> Path:
    target = dest_dir / name
    if not target.exists():
        return target
    stem, suffix = target.stem, target.suffix
    i = 1
    while True:
        candidate = dest_dir / f"{stem}_{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def _run_exiftool(args: list[str], files: Sequence[Path]) -> subprocess.CompletedProcess[str]:
    """Executa o ExifTool passando as opções via arquivo de argumentos (UTF-8)."""
    with tempfile.NamedTemporaryFile("w", suffix=".args", delete=False, encoding="utf-8") as fh:
        for a in args:
            fh.write(a + "\n")
        for f in files:
            fh.write(str(f) + "\n")
        argfile = fh.name
    try:
        cmd = [
            exiftool_path(),
            "-charset", "filename=utf8",
            "-charset", "iptc=utf8",
            "-codedcharacterset=utf8",
            "-overwrite_original",
            "-m",                 # ignora avisos menores de tags
            "-@", argfile,
        ]
        return subprocess.run(cmd, capture_output=True, text=True, check=False)
    finally:
        os.unlink(argfile)


def apply_metadata(
    files: Sequence[Path],
    values: dict[str, str],
    custom: Sequence[tuple[str, str]] = (),
    output_dir: Path | None = None,
    clear_missing: bool = False,
    preserve_file_dates: bool = True,
    backup_originals: bool = False,
    progress: Callable[[int, int, str], None] | None = None,
) -> WriteResult:
    """Aplica os metadados.

    output_dir=None grava nos arquivos originais; caso contrário copia cada
    imagem para a pasta indicada e grava apenas nas cópias.
    """
    result = WriteResult()
    args, warnings = build_args(values, custom, clear_missing)
    result.messages.extend(f"Aviso: {w}" for w in warnings)

    if not args:
        result.messages.append("Nenhum campo preenchido — nada a gravar.")
        return result

    if preserve_file_dates:
        args = ["-P", *args]

    targets: list[Path] = []
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        for src in files:
            try:
                dst = _unique_destination(output_dir, src.name)
                shutil.copy2(src, dst)
                targets.append(dst)
            except OSError as exc:
                result.failed += 1
                result.messages.append(f"Falha ao copiar {src.name}: {exc}")
    else:
        if backup_originals:
            for src in files:
                try:
                    shutil.copy2(src, src.with_suffix(src.suffix + "_original"))
                except OSError as exc:
                    result.messages.append(f"Backup falhou para {src.name}: {exc}")
        targets = list(files)

    total = len(targets)
    done = 0
    for start in range(0, total, CHUNK_SIZE):
        chunk = targets[start : start + CHUNK_SIZE]
        proc = _run_exiftool(args, chunk)
        stderr = proc.stderr.strip()
        if stderr:
            for line in stderr.splitlines():
                result.messages.append(line.strip())
        # ExifTool reporta "N image files updated" no stdout.
        updated_here = 0
        for line in proc.stdout.splitlines():
            line = line.strip()
            if line.endswith("updated"):
                updated_here = int(line.split()[0])
            elif line.endswith("unchanged") or "weren't updated" in line:
                result.messages.append(line)
        result.updated += updated_here
        result.failed += len(chunk) - updated_here
        done += len(chunk)
        if progress:
            progress(done, total, chunk[-1].name)

    return result


def _exiftool_json(file: Path, tags: Sequence[str], numeric: bool) -> dict[str, str]:
    cmd = [
        exiftool_path(),
        "-charset", "filename=utf8",
        "-json", "-G0",
        *(["-n"] if numeric else []),
        *[f"-{t}" for t in tags],
        str(file),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0 or not proc.stdout.strip():
        return {}
    try:
        data = json.loads(proc.stdout)[0]
    except (json.JSONDecodeError, IndexError, KeyError):
        return {}

    flat: dict[str, str] = {}
    for key, value in data.items():
        short = key.split(":")[-1]
        if isinstance(value, list):
            value = ", ".join(str(v) for v in value)
        flat.setdefault(short, str(value))
    return flat


def read_metadata(file: Path) -> dict[str, str]:
    """Lê os campos do formulário a partir de uma imagem existente."""
    tags_wanted: set[str] = set()
    for field in ALL_FIELDS.values():
        tags_wanted.update(t.split(":")[-1] for t in field.tags)

    # Valores legíveis (Flash="No Flash", exposição="1/200") para o formulário.
    flat = _exiftool_json(file, sorted(tags_wanted), numeric=False)
    # GPS composto vem assinado (sul/oeste negativos) apenas no modo numérico.
    gps = _exiftool_json(
        file,
        ["Composite:GPSLatitude", "Composite:GPSLongitude", "Composite:GPSAltitude"],
        numeric=True,
    )

    out: dict[str, str] = {}
    for key, field in ALL_FIELDS.items():
        if key in GPS_NUMERIC_KEYS:
            continue
        for tag in field.tags:
            short = tag.split(":")[-1]
            if short in flat and flat[short] != "":
                out[key] = flat[short]
                break

    for key, tag in (
        ("gps_lat", "GPSLatitude"),
        ("gps_lon", "GPSLongitude"),
        ("gps_alt", "GPSAltitude"),
    ):
        if tag in gps:
            out[key] = gps[tag]

    return out
