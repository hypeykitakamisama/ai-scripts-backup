"""
文件后缀批量修改工具
Python 3.12 / tkinter（内置）
拖拽支持依赖 tkinterdnd2：pip install tkinterdnd2
"""

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import shutil
from pathlib import Path


# ── 配色 ──────────────────────────────────────────────────────────────────────
BG         = "#F7F6F3"
PANEL      = "#FFFFFF"
BORDER     = "#E0DED7"
TEXT       = "#1A1A18"
MUTED      = "#6B6A66"
ACCENT     = "#1A1A18"
SUCCESS    = "#3B6D11"
SUCCESS_BG = "#EAF3DE"
ERR        = "#A32D2D"
ERR_BG     = "#FCEBEB"
INFO_BG    = "#F1EFE8"
BTN_H      = "#ECEAE3"
DROP_HL    = "#D0E8FF"


# ── 规则行 ────────────────────────────────────────────────────────────────────
class RuleRow(tk.Frame):
    def __init__(self, parent, on_delete, **kwargs):
        super().__init__(parent, bg=PANEL, **kwargs)

        self.src_var    = tk.StringVar()
        self.dst_var    = tk.StringVar()
        self.folder_var = tk.StringVar()

        entry_cfg = dict(
            bg=BG, fg=TEXT, relief="flat",
            highlightthickness=1, highlightbackground=BORDER,
            highlightcolor=ACCENT, insertbackground=TEXT,
            font=("Segoe UI", 10), bd=0
        )

        self.src_entry = tk.Entry(self, textvariable=self.src_var, width=10, **entry_cfg)
        self.src_entry.insert(0, ".zip")
        self.src_entry.bind("<FocusIn>",  lambda e: self._clear_ph(self.src_entry,  ".zip"))
        self.src_entry.bind("<FocusOut>", lambda e: self._set_ph  (self.src_entry,  ".zip"))

        self.dst_entry = tk.Entry(self, textvariable=self.dst_var, width=10, **entry_cfg)
        self.dst_entry.insert(0, ".cbz")
        self.dst_entry.bind("<FocusIn>",  lambda e: self._clear_ph(self.dst_entry,  ".cbz"))
        self.dst_entry.bind("<FocusOut>", lambda e: self._set_ph  (self.dst_entry,  ".cbz"))

        self.folder_entry = tk.Entry(self, textvariable=self.folder_var, width=28, **entry_cfg)
        ph = "留空则原地修改"
        self.folder_entry.insert(0, ph)
        self.folder_entry.config(fg=MUTED)
        self.folder_entry.bind("<FocusIn>",  lambda e: self._clear_ph(self.folder_entry, ph, grey=True))
        self.folder_entry.bind("<FocusOut>", lambda e: self._set_ph  (self.folder_entry, ph, grey=True))

        browse_btn = tk.Button(self, text="…", width=2, bg=BG, fg=TEXT, relief="flat",
                               activebackground=BTN_H, font=("Segoe UI", 10), cursor="hand2",
                               command=self._browse_folder)
        del_btn = tk.Button(self, text="✕", width=2, bg=PANEL, fg=MUTED, relief="flat",
                            activebackground=ERR_BG, activeforeground=ERR,
                            font=("Segoe UI", 10), cursor="hand2", command=on_delete)

        self.src_entry.pack(side="left", ipady=4, padx=(0, 6))
        tk.Label(self, text="→", bg=PANEL, fg=MUTED, font=("Segoe UI", 10)).pack(side="left", padx=(0, 6))
        self.dst_entry.pack(side="left", ipady=4, padx=(0, 6))
        self.folder_entry.pack(side="left", ipady=4, padx=(0, 4), expand=True, fill="x")
        browse_btn.pack(side="left", padx=(0, 6))
        del_btn.pack(side="left")

    def _clear_ph(self, widget, placeholder, grey=False):
        if widget.get() == placeholder:
            widget.delete(0, "end")
            widget.config(fg=TEXT)

    def _set_ph(self, widget, placeholder, grey=False):
        if widget.get().strip() == "":
            widget.insert(0, placeholder)
            widget.config(fg=MUTED if grey else TEXT)

    def _browse_folder(self):
        path = filedialog.askdirectory(title="选择目标文件夹")
        if path:
            self.folder_var.set(path)
            self.folder_entry.config(fg=TEXT)

    def get_rule(self):
        src    = self.src_var.get().strip()
        dst    = self.dst_var.get().strip()
        folder = self.folder_var.get().strip()
        if folder == "留空则原地修改":
            folder = ""
        if src and not src.startswith("."):
            src = "." + src
        if dst and not dst.startswith("."):
            dst = "." + dst
        return src.lower(), dst, folder


# ── 拖拽区域 ─────────────────────────────────────────────────────────────────
class DropZone(tk.Frame):
    """
    拖拽放入区域。
    需要 tkinterdnd2；若未安装则退化为普通提示 Frame。
    on_drop(paths: list[Path]) 回调由外部传入。
    """
    def __init__(self, parent, on_drop, **kwargs):
        super().__init__(parent, bg=PANEL,
                         highlightthickness=1, highlightbackground=BORDER,
                         **kwargs)
        self._on_drop = on_drop
        self._build()

    def _build(self):
        self._label = tk.Label(
            self,
            text="将文件或文件夹拖拽到此处" if DND_AVAILABLE else
                 "拖拽不可用 — 请先运行：pip install tkinterdnd2",
            bg=PANEL, fg=MUTED, font=("Segoe UI", 10),
            pady=14
        )
        self._label.pack(fill="x")

        if DND_AVAILABLE:
            for widget in (self, self._label):
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind("<<Drop>>",      self._handle_drop)
                widget.dnd_bind("<<DragEnter>>", self._drag_enter)
                widget.dnd_bind("<<DragLeave>>", self._drag_leave)

    def _drag_enter(self, event):
        self.config(highlightbackground="#5AABF0", bg=DROP_HL)
        self._label.config(bg=DROP_HL, fg="#185FA5")

    def _drag_leave(self, event):
        self.config(highlightbackground=BORDER, bg=PANEL)
        self._label.config(bg=PANEL, fg=MUTED)

    def _handle_drop(self, event):
        self._drag_leave(event)
        paths = self._parse_drop_data(event.data)
        result: list[Path] = []
        for p in paths:
            pp = Path(p)
            if pp.is_file():
                result.append(pp)
            elif pp.is_dir():
                result.extend(f for f in pp.rglob("*") if f.is_file())
        if result:
            self._on_drop(result)

    @staticmethod
    def _parse_drop_data(data: str) -> list[str]:
        """处理 tkinterdnd2 路径字符串，含空格路径用 {} 包裹。"""
        paths, data = [], data.strip()
        while data:
            if data.startswith("{"):
                end = data.index("}")
                paths.append(data[1:end])
                data = data[end + 1:].strip()
            else:
                parts = data.split(" ", 1)
                paths.append(parts[0])
                data = parts[1].strip() if len(parts) > 1 else ""
        return paths


# ── 主窗口 ────────────────────────────────────────────────────────────────────
_BaseClass = TkinterDnD.Tk if DND_AVAILABLE else tk.Tk


class App(_BaseClass):
    def __init__(self):
        super().__init__()
        self.title("文件后缀批量修改")
        self.geometry("800x700")
        self.minsize(640, 520)
        self.configure(bg=BG)
        self.resizable(True, True)

        self._rule_rows: list[RuleRow] = []
        self._selected_paths: list[Path] = []
        self._build_ui()
        self._add_rule()

    # ── 界面构建 ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=20, pady=(18, 0))
        tk.Label(hdr, text="文件后缀批量修改工具", bg=BG, fg=TEXT,
                 font=("Segoe UI", 14, "bold")).pack(anchor="w")
        tk.Label(hdr, text="支持自定义规则、原地修改或移动到指定目录（含 SMB 映射盘符）",
                 bg=BG, fg=MUTED, font=("Segoe UI", 10)).pack(anchor="w", pady=(2, 0))

        self._build_rules_panel()
        self._build_files_panel()
        self._build_action_panel()

    def _section(self, title):
        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="x", padx=20, pady=(14, 0))
        panel = tk.Frame(outer, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        panel.pack(fill="x")
        tk.Label(panel, text=title, bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w", padx=14, pady=(10, 0))
        inner = tk.Frame(panel, bg=PANEL)
        inner.pack(fill="x", padx=14, pady=(6, 12))
        return inner

    def _build_rules_panel(self):
        inner = self._section("转换规则")

        hdr = tk.Frame(inner, bg=PANEL)
        hdr.pack(fill="x", pady=(0, 4))
        for text, w in [("源后缀", 10), ("", 2), ("目标后缀", 10), ("目标文件夹（留空=原地修改）", 28)]:
            tk.Label(hdr, text=text, bg=PANEL, fg=MUTED,
                     font=("Segoe UI", 9), width=w, anchor="w").pack(side="left", padx=(0, 6))

        self._rules_frame = tk.Frame(inner, bg=PANEL)
        self._rules_frame.pack(fill="x")

        tk.Button(inner, text="+ 添加规则", bg=BG, fg=MUTED, relief="flat",
                  activebackground=BTN_H, activeforeground=TEXT,
                  font=("Segoe UI", 10), cursor="hand2",
                  command=self._add_rule).pack(anchor="w", pady=(8, 0))

    def _build_files_panel(self):
        inner = self._section("选择文件")

        # 路径显示 + 按钮
        btn_row = tk.Frame(inner, bg=PANEL)
        btn_row.pack(fill="x")

        self._src_var = tk.StringVar()
        tk.Entry(btn_row, textvariable=self._src_var, state="readonly",
                 bg=BG, fg=TEXT, relief="flat",
                 highlightthickness=1, highlightbackground=BORDER,
                 font=("Segoe UI", 10), readonlybackground=BG
                 ).pack(side="left", fill="x", expand=True, ipady=5, padx=(0, 8))

        tk.Button(btn_row, text="选择文件", bg=BG, fg=TEXT, relief="flat",
                  activebackground=BTN_H, font=("Segoe UI", 10), cursor="hand2",
                  command=self._pick_files).pack(side="left", padx=(0, 6))
        tk.Button(btn_row, text="选择文件夹", bg=BG, fg=TEXT, relief="flat",
                  activebackground=BTN_H, font=("Segoe UI", 10), cursor="hand2",
                  command=self._pick_folder).pack(side="left")

        # 选项行
        opt_row = tk.Frame(inner, bg=PANEL)
        opt_row.pack(fill="x", pady=(8, 0))

        self._recursive_var = tk.BooleanVar(value=False)
        tk.Checkbutton(opt_row, text="包含子文件夹（递归）",
                       variable=self._recursive_var,
                       bg=PANEL, fg=TEXT, font=("Segoe UI", 10),
                       activebackground=PANEL, selectcolor=PANEL).pack(side="left", padx=(0, 20))

        self._keep_src_var = tk.BooleanVar(value=False)
        tk.Checkbutton(opt_row, text="保留源文件（复制而非移动/重命名）",
                       variable=self._keep_src_var,
                       bg=PANEL, fg=TEXT, font=("Segoe UI", 10),
                       activebackground=PANEL, selectcolor=PANEL).pack(side="left")

        # 拖拽区
        self._drop_zone = DropZone(inner, on_drop=self._on_drop)
        self._drop_zone.pack(fill="x", pady=(10, 0))

        # 文件预览
        self._preview_label = tk.Label(inner, text="尚未选择文件",
                                       bg=PANEL, fg=MUTED, font=("Segoe UI", 10),
                                       justify="left", anchor="w")
        self._preview_label.pack(fill="x", pady=(8, 0))

    def _build_action_panel(self):
        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True, padx=20, pady=(14, 14))
        panel = tk.Frame(outer, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        panel.pack(fill="both", expand=True)
        tk.Label(panel, text="执行", bg=PANEL, fg=MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w", padx=14, pady=(10, 0))
        inner = tk.Frame(panel, bg=PANEL)
        inner.pack(fill="both", expand=True, padx=14, pady=(6, 12))

        btn_row = tk.Frame(inner, bg=PANEL)
        btn_row.pack(fill="x")

        tk.Button(btn_row, text="执行重命名",
                  bg=ACCENT, fg="#FFFFFF", relief="flat",
                  activebackground="#333330", activeforeground="#FFFFFF",
                  font=("Segoe UI", 10, "bold"), cursor="hand2",
                  padx=16, pady=6, command=self._run).pack(side="left", padx=(0, 8))

        tk.Button(btn_row, text="清空列表", bg=BG, fg=MUTED, relief="flat",
                  activebackground=BTN_H, font=("Segoe UI", 10), cursor="hand2",
                  padx=12, pady=6, command=self._clear_list).pack(side="left", padx=(0, 6))

        tk.Button(btn_row, text="清空日志", bg=BG, fg=MUTED, relief="flat",
                  activebackground=BTN_H, font=("Segoe UI", 10), cursor="hand2",
                  padx=12, pady=6, command=self._clear_log).pack(side="left")

        log_outer = tk.Frame(inner, bg=PANEL)
        log_outer.pack(fill="both", expand=True, pady=(10, 0))

        self._log_text = tk.Text(log_outer, height=8, state="disabled",
                                 bg=INFO_BG, fg=TEXT, relief="flat",
                                 font=("Consolas", 9), wrap="word",
                                 highlightthickness=0, bd=0)
        self._log_text.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(log_outer, command=self._log_text.yview)
        sb.pack(side="right", fill="y")
        self._log_text.config(yscrollcommand=sb.set)

        self._log_text.tag_config("ok",   foreground=SUCCESS, background=SUCCESS_BG)
        self._log_text.tag_config("err",  foreground=ERR,     background=ERR_BG)
        self._log_text.tag_config("info", foreground=MUTED)
        self._log_text.tag_config("head", foreground=TEXT, font=("Consolas", 9, "bold"))

    # ── 规则管理 ──────────────────────────────────────────────────────────────
    def _add_rule(self):
        row = RuleRow(self._rules_frame,
                      on_delete=lambda r=None: self._delete_rule(row))
        row.pack(fill="x", pady=(0, 4))
        self._rule_rows.append(row)

    def _delete_rule(self, row):
        row.destroy()
        self._rule_rows.remove(row)

    # ── 文件选择 ──────────────────────────────────────────────────────────────
    def _pick_files(self):
        paths = filedialog.askopenfilenames(title="选择文件")
        if paths:
            self._add_paths([Path(p) for p in paths])

    def _pick_folder(self):
        folder = filedialog.askdirectory(title="选择文件夹")
        if folder:
            pattern = "**/*" if self._recursive_var.get() else "*"
            self._add_paths([p for p in Path(folder).glob(pattern) if p.is_file()])

    def _on_drop(self, paths: list[Path]):
        self._add_paths(paths)

    def _add_paths(self, new_paths: list[Path]):
        """去重追加，不替换已有列表。"""
        existing = {p.resolve() for p in self._selected_paths}
        for p in new_paths:
            if p.resolve() not in existing:
                self._selected_paths.append(p)
                existing.add(p.resolve())
        self._update_preview()

    def _update_preview(self):
        n = len(self._selected_paths)
        if n == 0:
            self._preview_label.config(text="尚未选择文件", fg=MUTED)
            self._src_var.set("")
            return
        dirs = {str(p.parent) for p in self._selected_paths}
        dir_hint = next(iter(dirs)) if len(dirs) == 1 else f"{len(dirs)} 个目录"
        self._src_var.set(f"{dir_hint}  （共 {n} 个文件）")
        preview = "\n".join(p.name for p in self._selected_paths[:8])
        if n > 8:
            preview += f"\n… 还有 {n - 8} 个文件"
        self._preview_label.config(text=preview, fg=TEXT)

    def _clear_list(self):
        self._selected_paths.clear()
        self._update_preview()

    # ── 执行 ──────────────────────────────────────────────────────────────────
    def _run(self):
        rules = [(s, d, f) for row in self._rule_rows
                 for s, d, f in [row.get_rule()] if s and d]

        if not rules:
            messagebox.showwarning("提示", "请至少配置一条有效规则")
            return
        if not self._selected_paths:
            messagebox.showwarning("提示", "请先选择要处理的文件")
            return

        keep_src   = self._keep_src_var.get()
        mode_label = "复制（保留源文件）" if keep_src else "移动/重命名"

        self._log("─" * 60, "head")
        self._log(f"开始处理  文件={len(self._selected_paths)}  规则={len(rules)}  模式={mode_label}", "info")

        ok = skip = err = 0

        for path in self._selected_paths:
            ext     = path.suffix.lower()
            matched = next((r for r in rules if r[0] == ext), None)
            if not matched:
                self._log(f"  ·  {path.name}  （无匹配规则，跳过）", "info")
                skip += 1
                continue

            _, dst_ext, dst_folder = matched
            new_name = path.stem + dst_ext
            dst_dir  = Path(dst_folder) if dst_folder else path.parent
            dst_path = dst_dir / new_name

            try:
                dst_dir.mkdir(parents=True, exist_ok=True)
                if dst_path.exists():
                    dst_path = self._resolve_conflict(dst_path)

                if keep_src:
                    shutil.copy2(str(path), str(dst_path))
                    action = f"复制 → {dst_path}"
                elif dst_folder:
                    shutil.move(str(path), str(dst_path))
                    action = f"移动 → {dst_path}"
                else:
                    path.rename(dst_path)
                    action = f"重命名 → {dst_path.name}"

                self._log(f"  ✓  {path.name}  →  {action}", "ok")
                ok += 1
            except Exception as e:
                self._log(f"  ✗  {path.name}  错误: {e}", "err")
                err += 1

        self._log(f"完成：成功 {ok}  跳过 {skip}  失败 {err}", "head")
        self._log("─" * 60, "head")

        # 仅移动/重命名模式下清空列表（复制模式源文件还在，保留列表方便复查）
        if not keep_src:
            self._selected_paths.clear()
            self._update_preview()

    def _resolve_conflict(self, path: Path) -> Path:
        i = 1
        while True:
            c = path.parent / f"{path.stem}_{i}{path.suffix}"
            if not c.exists():
                return c
            i += 1

    # ── 日志 ──────────────────────────────────────────────────────────────────
    def _log(self, msg, tag="info"):
        self._log_text.config(state="normal")
        self._log_text.insert("end", msg + "\n", tag)
        self._log_text.see("end")
        self._log_text.config(state="disabled")

    def _clear_log(self):
        self._log_text.config(state="normal")
        self._log_text.delete("1.0", "end")
        self._log_text.config(state="disabled")


if __name__ == "__main__":
    app = App()
    app.mainloop()
