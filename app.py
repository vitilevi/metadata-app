#!/usr/bin/env python3
"""Metadados de Imagem — aplica os mesmos metadados em lote.

Interface desktop (Tkinter) sobre o ExifTool. Escolha uma pasta ou arquivos
avulsos, preencha os campos e aplique em todas as imagens ou apenas nas
selecionadas.
"""

from __future__ import annotations

import json
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import exif_writer as writer
from tags import GROUPS

APP_TITLE = "Metadados de Imagem"
PRESET_SUFFIX = ".metapreset.json"


class MetadataApp(ttk.Frame):
    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master, padding=10)
        self.master.title(APP_TITLE)
        self.master.geometry("1120x760")
        self.master.minsize(940, 640)
        self.pack(fill="both", expand=True)

        self.files: list[Path] = []
        self.vars: dict[str, tk.Variable] = {}
        self.text_widgets: dict[str, tk.Text] = {}
        self.custom_rows: list[tuple[tk.StringVar, tk.StringVar]] = []
        self.events: queue.Queue = queue.Queue()
        self.running = False

        self.only_selected = tk.BooleanVar(value=False)
        self.recursive = tk.BooleanVar(value=True)
        self.write_mode = tk.StringVar(value="inplace")
        self.output_dir = tk.StringVar(value="")
        self.backup = tk.BooleanVar(value=True)
        self.preserve_dates = tk.BooleanVar(value=True)
        self.clear_missing = tk.BooleanVar(value=False)

        self._build_ui()
        self._check_exiftool()
        self.after(120, self._drain_events)

    # ------------------------------------------------------------------ UI

    def _build_ui(self) -> None:
        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.pack(fill="both", expand=True)

        left = ttk.Frame(paned, padding=(0, 0, 8, 0))
        right = ttk.Frame(paned)
        paned.add(left, weight=1)
        paned.add(right, weight=2)

        self._build_file_panel(left)
        self._build_form_panel(right)
        self._build_bottom_panel()

    def _build_file_panel(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Imagens", font=("", 13, "bold")).pack(anchor="w")

        btns = ttk.Frame(parent)
        btns.pack(fill="x", pady=(6, 4))
        ttk.Button(btns, text="Adicionar pasta…", command=self.add_folder).pack(side="left")
        ttk.Button(btns, text="Adicionar arquivos…", command=self.add_files).pack(side="left", padx=4)
        ttk.Button(btns, text="Remover", command=self.remove_selected).pack(side="left")
        ttk.Button(btns, text="Limpar", command=self.clear_files).pack(side="left", padx=4)

        ttk.Checkbutton(
            parent, text="Incluir subpastas ao adicionar uma pasta", variable=self.recursive
        ).pack(anchor="w")
        ttk.Checkbutton(
            parent,
            text="Aplicar somente nas imagens selecionadas na lista",
            variable=self.only_selected,
        ).pack(anchor="w", pady=(0, 6))

        box = ttk.Frame(parent)
        box.pack(fill="both", expand=True)
        scroll_y = ttk.Scrollbar(box, orient="vertical")
        self.listbox = tk.Listbox(
            box, selectmode="extended", activestyle="none", yscrollcommand=scroll_y.set
        )
        scroll_y.config(command=self.listbox.yview)
        scroll_y.pack(side="right", fill="y")
        self.listbox.pack(side="left", fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", lambda _e: self._update_counts())

        self.count_label = ttk.Label(parent, text="0 imagens")
        self.count_label.pack(anchor="w", pady=(6, 0))

        ttk.Button(
            parent,
            text="Ler metadados da imagem selecionada",
            command=self.load_from_selected,
        ).pack(fill="x", pady=(8, 0))

    def _build_form_panel(self, parent: ttk.Frame) -> None:
        header = ttk.Frame(parent)
        header.pack(fill="x")
        ttk.Label(header, text="Metadados a aplicar", font=("", 13, "bold")).pack(side="left")
        ttk.Button(header, text="Carregar preset…", command=self.load_preset).pack(side="right")
        ttk.Button(header, text="Salvar preset…", command=self.save_preset).pack(side="right", padx=4)
        ttk.Button(header, text="Limpar campos", command=self.clear_fields).pack(side="right")

        notebook = ttk.Notebook(parent)
        notebook.pack(fill="both", expand=True, pady=(6, 0))

        for group in GROUPS:
            tab = ttk.Frame(notebook, padding=10)
            notebook.add(tab, text=group.name)
            self._build_group_fields(tab, group)

        custom_tab = ttk.Frame(notebook, padding=10)
        notebook.add(custom_tab, text="Tags manuais")
        self._build_custom_tab(custom_tab)

    def _build_group_fields(self, tab: ttk.Frame, group) -> None:
        tab.columnconfigure(1, weight=1)
        for row, field in enumerate(group.fields):
            ttk.Label(tab, text=field.label + ":").grid(
                row=row, column=0, sticky="nw", pady=4, padx=(0, 8)
            )
            if field.choices:
                var = tk.StringVar()
                widget = ttk.Combobox(tab, textvariable=var, values=list(field.choices))
                widget.grid(row=row, column=1, sticky="ew", pady=4)
                self.vars[field.key] = var
            elif field.multiline:
                text = tk.Text(tab, height=3, wrap="word")
                text.grid(row=row, column=1, sticky="ew", pady=4)
                self.text_widgets[field.key] = text
            else:
                var = tk.StringVar()
                ttk.Entry(tab, textvariable=var).grid(row=row, column=1, sticky="ew", pady=4)
                self.vars[field.key] = var
            if field.hint:
                ttk.Label(tab, text=field.hint, foreground="#777").grid(
                    row=row, column=2, sticky="w", padx=(8, 0)
                )

    def _build_custom_tab(self, tab: ttk.Frame) -> None:
        ttk.Label(
            tab,
            text=(
                "Escreva qualquer tag do ExifTool diretamente.\n"
                "Ex.: XMP-dc:Publisher  |  IPTC:Headline  |  EXIF:UserComment"
            ),
            foreground="#555",
        ).pack(anchor="w", pady=(0, 8))

        self.custom_container = ttk.Frame(tab)
        self.custom_container.pack(fill="x")
        self.custom_container.columnconfigure(1, weight=1)
        for _ in range(4):
            self._add_custom_row()

        ttk.Button(tab, text="+ Adicionar linha", command=self._add_custom_row).pack(
            anchor="w", pady=8
        )

    def _add_custom_row(self) -> None:
        row = len(self.custom_rows)
        tag_var, value_var = tk.StringVar(), tk.StringVar()
        ttk.Entry(self.custom_container, textvariable=tag_var, width=28).grid(
            row=row, column=0, sticky="w", pady=3, padx=(0, 8)
        )
        ttk.Entry(self.custom_container, textvariable=value_var).grid(
            row=row, column=1, sticky="ew", pady=3
        )
        self.custom_rows.append((tag_var, value_var))

    def _build_bottom_panel(self) -> None:
        bottom = ttk.Frame(self)
        bottom.pack(fill="x", pady=(10, 0))

        opts = ttk.LabelFrame(bottom, text="Gravação", padding=8)
        opts.pack(fill="x")

        ttk.Radiobutton(
            opts,
            text="Gravar nos arquivos originais",
            value="inplace",
            variable=self.write_mode,
            command=self._toggle_output,
        ).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(
            opts,
            text="Salvar cópias em outra pasta",
            value="copy",
            variable=self.write_mode,
            command=self._toggle_output,
        ).grid(row=0, column=1, sticky="w", padx=(16, 8))

        self.output_entry = ttk.Entry(opts, textvariable=self.output_dir, state="disabled")
        self.output_entry.grid(row=0, column=2, sticky="ew", padx=(0, 6))
        self.output_button = ttk.Button(
            opts, text="Escolher…", command=self.choose_output, state="disabled"
        )
        self.output_button.grid(row=0, column=3)
        opts.columnconfigure(2, weight=1)

        self.backup_check = ttk.Checkbutton(
            opts, text="Guardar backup do original (_original)", variable=self.backup
        )
        self.backup_check.grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Checkbutton(
            opts, text="Preservar data de modificação do arquivo", variable=self.preserve_dates
        ).grid(row=1, column=1, sticky="w", pady=(6, 0), padx=(16, 0))
        ttk.Checkbutton(
            opts,
            text="Apagar das imagens as tags deixadas em branco",
            variable=self.clear_missing,
        ).grid(row=1, column=2, columnspan=2, sticky="w", pady=(6, 0))

        actions = ttk.Frame(bottom)
        actions.pack(fill="x", pady=(8, 4))
        self.apply_button = ttk.Button(
            actions, text="Aplicar metadados", command=self.apply_metadata
        )
        self.apply_button.pack(side="left")
        self.progress = ttk.Progressbar(actions, mode="determinate")
        self.progress.pack(side="left", fill="x", expand=True, padx=10)
        self.status = ttk.Label(actions, text="Pronto")
        self.status.pack(side="right")

        log_frame = ttk.Frame(bottom)
        log_frame.pack(fill="both", expand=True)
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical")
        self.log = tk.Text(log_frame, height=7, wrap="word", state="disabled",
                           yscrollcommand=log_scroll.set)
        log_scroll.config(command=self.log.yview)
        log_scroll.pack(side="right", fill="y")
        self.log.pack(side="left", fill="both", expand=True)

    # --------------------------------------------------------------- estado

    def _check_exiftool(self) -> None:
        try:
            self._log(f"ExifTool {writer.exiftool_version()} encontrado.")
        except writer.ExifToolMissing as exc:
            self.apply_button.config(state="disabled")
            self._log(str(exc))
            messagebox.showerror(APP_TITLE, str(exc))

    def _toggle_output(self) -> None:
        copying = self.write_mode.get() == "copy"
        state = "normal" if copying else "disabled"
        self.output_entry.config(state=state)
        self.output_button.config(state=state)
        self.backup_check.config(state="disabled" if copying else "normal")

    def _log(self, message: str) -> None:
        self.log.config(state="normal")
        self.log.insert("end", message + "\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def _update_counts(self) -> None:
        selected = len(self.listbox.curselection())
        text = f"{len(self.files)} imagens"
        if selected:
            text += f" · {selected} selecionadas"
        self.count_label.config(text=text)

    def _refresh_list(self) -> None:
        self.listbox.delete(0, "end")
        for f in self.files:
            self.listbox.insert("end", f.name + "   —   " + str(f.parent))
        self._update_counts()

    # --------------------------------------------------------------- ações

    def add_folder(self) -> None:
        folder = filedialog.askdirectory(title="Escolha a pasta com as imagens")
        if not folder:
            return
        found = writer.collect_images([folder], recursive=self.recursive.get())
        self._extend_files(found)
        self._log(f"Pasta adicionada: {folder} ({len(found)} imagens)")

    def add_files(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Escolha as imagens",
            filetypes=[("Imagens", "*.jpg *.jpeg *.tif *.tiff *.png *.webp *.heic *.dng *.cr2 *.cr3 *.nef *.arw"), ("Todos", "*.*")],
        )
        if not paths:
            return
        found = writer.collect_images(paths)
        self._extend_files(found)
        self._log(f"{len(found)} imagens adicionadas.")

    def _extend_files(self, found: list[Path]) -> None:
        known = set(self.files)
        self.files.extend(f for f in found if f not in known)
        self._refresh_list()

    def remove_selected(self) -> None:
        for index in sorted(self.listbox.curselection(), reverse=True):
            del self.files[index]
        self._refresh_list()

    def clear_files(self) -> None:
        self.files.clear()
        self._refresh_list()

    def choose_output(self) -> None:
        folder = filedialog.askdirectory(title="Pasta de saída")
        if folder:
            self.output_dir.set(folder)

    def clear_fields(self) -> None:
        for var in self.vars.values():
            var.set("")
        for text in self.text_widgets.values():
            text.delete("1.0", "end")
        for tag_var, value_var in self.custom_rows:
            tag_var.set("")
            value_var.set("")

    def collect_values(self) -> dict[str, str]:
        values = {key: str(var.get()) for key, var in self.vars.items()}
        for key, text in self.text_widgets.items():
            values[key] = text.get("1.0", "end").strip()
        return values

    def collect_custom(self) -> list[tuple[str, str]]:
        return [
            (tag_var.get(), value_var.get())
            for tag_var, value_var in self.custom_rows
            if tag_var.get().strip()
        ]

    def set_values(self, values: dict[str, str]) -> None:
        for key, value in values.items():
            if key in self.vars:
                self.vars[key].set(value)
            elif key in self.text_widgets:
                self.text_widgets[key].delete("1.0", "end")
                self.text_widgets[key].insert("1.0", value)

    def load_from_selected(self) -> None:
        indices = self.listbox.curselection()
        if not indices:
            messagebox.showinfo(APP_TITLE, "Selecione uma imagem na lista primeiro.")
            return
        source = self.files[indices[0]]
        data = writer.read_metadata(source)
        if not data:
            self._log(f"Nenhum metadado legível em {source.name}.")
            return
        self.set_values(data)
        self._log(f"Campos preenchidos a partir de {source.name} ({len(data)} valores).")

    def save_preset(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Salvar preset", defaultextension=PRESET_SUFFIX,
            filetypes=[("Preset de metadados", f"*{PRESET_SUFFIX}")],
        )
        if not path:
            return
        payload = {"values": self.collect_values(), "custom": self.collect_custom()}
        Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self._log(f"Preset salvo em {path}")

    def load_preset(self) -> None:
        path = filedialog.askopenfilename(
            title="Carregar preset",
            filetypes=[("Preset de metadados", f"*{PRESET_SUFFIX}"), ("JSON", "*.json")],
        )
        if not path:
            return
        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            messagebox.showerror(APP_TITLE, f"Preset inválido: {exc}")
            return
        self.set_values(payload.get("values", {}))
        for (tag_var, value_var), pair in zip(self.custom_rows, payload.get("custom", [])):
            tag_var.set(pair[0])
            value_var.set(pair[1])
        self._log(f"Preset carregado de {path}")

    # ------------------------------------------------------------ execução

    def _target_files(self) -> list[Path]:
        if self.only_selected.get():
            return [self.files[i] for i in self.listbox.curselection()]
        return list(self.files)

    def apply_metadata(self) -> None:
        if self.running:
            return
        targets = self._target_files()
        if not targets:
            messagebox.showinfo(APP_TITLE, "Nenhuma imagem na fila.")
            return

        values = self.collect_values()
        custom = self.collect_custom()
        if not any(v.strip() for v in values.values()) and not custom:
            messagebox.showinfo(APP_TITLE, "Preencha ao menos um campo.")
            return

        output_dir = None
        if self.write_mode.get() == "copy":
            if not self.output_dir.get().strip():
                messagebox.showinfo(APP_TITLE, "Escolha a pasta de saída.")
                return
            output_dir = Path(self.output_dir.get()).expanduser()
        else:
            extra = "\n\nAs tags em branco serão APAGADAS das imagens." if self.clear_missing.get() else ""
            confirm = messagebox.askyesno(
                APP_TITLE,
                f"Gravar metadados em {len(targets)} imagem(ns) originais?"
                f"{'' if self.backup.get() else ' Sem backup.'}{extra}",
            )
            if not confirm:
                return

        self.running = True
        self.apply_button.config(state="disabled")
        self.progress.config(value=0, maximum=len(targets))
        self.status.config(text="Processando…")
        self._log(f"Aplicando em {len(targets)} imagem(ns)…")

        thread = threading.Thread(
            target=self._worker,
            args=(targets, values, custom, output_dir,
                  self.clear_missing.get(), self.preserve_dates.get(),
                  self.backup.get() and output_dir is None),
            daemon=True,
        )
        thread.start()

    def _worker(self, targets, values, custom, output_dir, clear_missing,
                preserve_dates, backup) -> None:
        def progress(done: int, total: int, name: str) -> None:
            self.events.put(("progress", (done, total, name)))

        try:
            result = writer.apply_metadata(
                targets, values, custom,
                output_dir=output_dir,
                clear_missing=clear_missing,
                preserve_file_dates=preserve_dates,
                backup_originals=backup,
                progress=progress,
            )
            self.events.put(("done", result))
        except Exception as exc:  # erro do ExifTool ou de I/O
            self.events.put(("error", exc))

    def _drain_events(self) -> None:
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "progress":
                    done, total, name = payload
                    self.progress.config(value=done)
                    self.status.config(text=f"{done}/{total} — {name}")
                elif kind == "done":
                    self._finish(payload)
                elif kind == "error":
                    self._log(f"Erro: {payload}")
                    messagebox.showerror(APP_TITLE, str(payload))
                    self._reset_run_state("Erro")
        except queue.Empty:
            pass
        self.after(120, self._drain_events)

    def _finish(self, result: writer.WriteResult) -> None:
        for message in result.messages:
            self._log(message)
        self._log(f"Concluído: {result.updated} atualizadas, {result.failed} com falha.")
        self._reset_run_state(f"{result.updated} atualizadas")

    def _reset_run_state(self, status: str) -> None:
        self.running = False
        self.apply_button.config(state="normal")
        self.status.config(text=status)


def main() -> None:
    root = tk.Tk()
    try:
        ttk.Style().theme_use("aqua")  # macOS
    except tk.TclError:
        pass
    MetadataApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
