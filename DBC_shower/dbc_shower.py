#!/usr/bin/env python3
"""
DBC 报文结构图形化查看工具
使用 cantools 解析 DBC 文件，ttk 构建图形界面，展示每个 CAN ID 的报文信号布局。
"""

import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cantools

import style


class DbcViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("DBC 报文结构查看器")
        self.root.geometry("1100x700")
        self.root.configure(bg=style.BG)
        style.apply_style(self.root)
        self.db = None
        self.dbc_path = None
        self._setup_ui()

    def _setup_ui(self):
        # 顶部工具栏
        toolbar = ttk.Frame(self.root, padding=5)
        toolbar.pack(fill=tk.X)

        ttk.Button(toolbar, text="打开 DBC 文件", command=self.open_dbc).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="导出结构体", command=self.export_struct).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="退出", command=self.root.destroy).pack(side=tk.LEFT, padx=5)
        self.file_label = ttk.Label(toolbar, text="未加载文件", style="Secondary.TLabel")
        self.file_label.pack(side=tk.LEFT, padx=10)

        # 主内容区：左右分栏
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 左侧：报文列表
        left_frame = ttk.LabelFrame(paned, text="报文列表 (Message List)", padding=3)
        paned.add(left_frame, weight=1)

        self.msg_tree = ttk.Treeview(left_frame, columns=("id", "name", "signals"), show="headings", selectmode="browse")
        self.msg_tree.heading("id", text="CAN ID")
        self.msg_tree.heading("name", text="报文名称")
        self.msg_tree.heading("signals", text="信号数")
        self.msg_tree.column("id", width=90, anchor=tk.CENTER)
        self.msg_tree.column("name", width=160)
        self.msg_tree.column("signals", width=60, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.msg_tree.yview)
        self.msg_tree.configure(yscrollcommand=scrollbar.set)
        self.msg_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.msg_tree.bind("<<TreeviewSelect>>", self.on_msg_select)
        style.configure_tree_tags(self.msg_tree)

        # 右侧：详情面板
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=2)

        # 右上：报文概要
        info_frame = ttk.LabelFrame(right_frame, text="报文概要", padding=5)
        info_frame.pack(fill=tk.X, pady=(0, 5))

        self.info_text = tk.Text(info_frame, height=4, wrap=tk.WORD, font=style.FONT_MONO)
        self.info_text.pack(fill=tk.X)

        # 右下：信号布局画布 (Canvas)
        sig_frame = ttk.LabelFrame(right_frame, text="信号位布局 (Signal Bit Layout)", padding=3)
        sig_frame.pack(fill=tk.BOTH, expand=False)

        canvas_container = ttk.Frame(sig_frame)
        canvas_container.pack(fill=tk.BOTH, expand=True)

        h_scrollbar = ttk.Scrollbar(canvas_container, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas = tk.Canvas(canvas_container, bg=style.CANVAS_BG, height=150,
                                xscrollcommand=h_scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        h_scrollbar.configure(command=self.canvas.xview)

        # 信号详情表格
        detail_frame = ttk.LabelFrame(right_frame, text="信号详情", padding=3)
        detail_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        self.sig_tree = ttk.Treeview(detail_frame, columns=("name", "start", "len", "endian", "scale", "offset", "min", "max", "unit"),
                                     show="headings", height=12)
        for col, txt, w in [
            ("name", "信号名", 140), ("start", "起始位", 55), ("len", "长度", 45),
            ("endian", "字节序", 55), ("scale", "缩放", 55), ("offset", "偏移", 55),
            ("min", "最小值", 60), ("max", "最大值", 60), ("unit", "单位", 55),
        ]:
            self.sig_tree.heading(col, text=txt)
            self.sig_tree.column(col, width=w, anchor=tk.CENTER)
        self.sig_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        style.configure_tree_tags(self.sig_tree)

        sig_scroll = ttk.Scrollbar(detail_frame, orient=tk.VERTICAL, command=self.sig_tree.yview)
        self.sig_tree.configure(yscrollcommand=sig_scroll.set)
        sig_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    # ==================== 文件操作 ====================

    def open_dbc(self):
        filepath = filedialog.askopenfilename(
            title="选择 DBC 文件",
            filetypes=[("DBC 文件", "*.dbc"), ("所有文件", "*.*")]
        )
        if not filepath:
            return
        try:
            self.db = cantools.database.load_file(filepath)
            self.dbc_path = filepath
            self.file_label.configure(text=filepath, style="TLabel")
            self._populate_message_list()
        except Exception as e:
            messagebox.showerror("错误", f"加载 DBC 文件失败:\n{e}")

    def export_struct(self):
        if self.db is None:
            messagebox.showwarning("提示", "请先打开 DBC 文件")
            return
        self._show_export_dialog()

    def _show_export_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("导出结构体")
        dialog.geometry("340x180")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="选择导出格式：", padding=10).pack()

        fmt_var = tk.StringVar(value="c")

        ttk.Radiobutton(dialog, text="C 头文件 (type.h)  — typedef struct + #define CAN ID", variable=fmt_var, value="c").pack(anchor=tk.W, padx=20, pady=(5, 0))
        ttk.Radiobutton(dialog, text="Python 文件 (type.py) — dataclass + CAN ID 常量", variable=fmt_var, value="py").pack(anchor=tk.W, padx=20, pady=5)

        btn_frame = ttk.Frame(dialog, padding=10)
        btn_frame.pack()

        def do_export():
            fmt = fmt_var.get()
            dialog.destroy()
            ext = ".h" if fmt == "c" else ".py"
            default_name = "type" + ext
            filepath = filedialog.asksaveasfilename(
                title=f"保存为 {ext} 文件",
                defaultextension=ext,
                initialfile=default_name,
                filetypes=[("C Header" if fmt == "c" else "Python", f"*{ext}"), ("所有文件", "*.*")]
            )
            if not filepath:
                return
            try:
                if fmt == "c":
                    content = self._generate_c_header()
                else:
                    content = self._generate_py_types()
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                messagebox.showinfo("完成", f"已导出到:\n{filepath}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败:\n{e}")

        ttk.Button(btn_frame, text="导出", command=do_export).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    # ==================== 代码生成 ====================

    @staticmethod
    def _sanitize_name(name):
        """将 DBC 名称转为合法 C/Python 标识符"""
        s = re.sub(r'[^A-Za-z0-9_]', '_', name)
        if s and s[0].isdigit():
            s = '_' + s
        return s or "_unnamed"

    @staticmethod
    def _c_type_for_bits(bits):
        """根据位宽返回 C 整数类型"""
        if bits == 1:
            return "uint8_t"
        elif bits <= 8:
            return "uint8_t"
        elif bits <= 16:
            return "uint16_t"
        elif bits <= 32:
            return "uint32_t"
        elif bits <= 64:
            return "uint64_t"
        else:
            return "uint64_t"

    def _generate_c_header(self):
        lines = []
        guard = "TYPE_H"
        lines.append(f"#ifndef {guard}")
        lines.append(f"#define {guard}\n")
        lines.append("#include <stdint.h>\n")

        # CAN ID 宏定义
        lines.append("/* ========== CAN ID 定义 ========== */")
        for msg in self.db.messages:
            macro = f"CAN_ID_{self._sanitize_name(msg.name).upper()}"
            lines.append(f"#define {macro}  0x{msg.frame_id:X}U")
        lines.append("\n/* ========== 报文结构体 ========== */")

        for msg in self.db.messages:
            struct_name = f"{self._sanitize_name(msg.name)}_t"
            lines.append(f"typedef struct {{")
            for sig in msg.signals:
                ctype = self._c_type_for_bits(sig.length)
                sname = self._sanitize_name(sig.name)
                comment = f"  // start={sig.start}, len={sig.length}"
                if sig.unit:
                    comment += f", unit={sig.unit}"
                lines.append(f"    {ctype}  {sname};{comment}")
            lines.append(f"}} {struct_name};\n")

        lines.append(f"#endif /* {guard} */")
        return "\n".join(lines) + "\n"

    def _generate_py_types(self):
        lines = []
        lines.append("# -*- coding: utf-8 -*-")
        lines.append("from dataclasses import dataclass, field\n")

        # CAN ID 常量
        lines.append("\n# ========== CAN ID 定义 ==========")
        for msg in self.db.messages:
            name = self._sanitize_name(msg.name).upper()
            lines.append(f"CAN_ID_{name} = 0x{msg.frame_id:X}")
        lines.append("\n# ========== 报文结构体 ==========\n")

        for msg in self.db.messages:
            class_name = self._sanitize_name(msg.name)
            lines.append("@dataclass")
            lines.append(f"class {class_name}:")
            if msg.comment:
                lines.append(f'    """{msg.comment}"""')
            for sig in msg.signals:
                sname = self._sanitize_name(sig.name)
                comment = f"  # start={sig.start}, len={sig.length}"
                if sig.unit:
                    comment += f", unit={sig.unit}"
                lines.append(f"    {sname}: int = 0{comment}")
            lines.append("")

        return "\n".join(lines) + "\n"

    # ==================== 报文列表 ====================

    def _populate_message_list(self):
        for item in self.msg_tree.get_children():
            self.msg_tree.delete(item)
        if self.db is None:
            return
        for msg in self.db.messages:
            self.msg_tree.insert("", tk.END, iid=msg.name,
                                 values=(f"0x{msg.frame_id:X}", msg.name, len(msg.signals)))

    def on_msg_select(self, event):
        sel = self.msg_tree.selection()
        if not sel or self.db is None:
            return
        msg_name = sel[0]
        msg = self.db.get_message_by_name(msg_name)
        self._show_msg_info(msg)
        self._draw_layout(msg)
        self._populate_signal_details(msg)

    def _show_msg_info(self, msg):
        self.info_text.configure(state=tk.NORMAL)
        self.info_text.delete("1.0", tk.END)
        info_lines = [
            f"报文名称: {msg.name}",
            f"CAN ID: 0x{msg.frame_id:X} ({msg.frame_id})",
            f"数据长度: {msg.length} 字节",
            f"发送周期: {msg.cycle_time} ms" if msg.cycle_time else "发送周期: 无",
            f"发送节点: {msg.senders}" if msg.senders else "发送节点: 无",
            f"信号数量: {len(msg.signals)}",
        ]
        self.info_text.insert("1.0", "\n".join(info_lines))
        self.info_text.configure(state=tk.DISABLED)

    # ==================== 信号名布局辅助 ====================

    @staticmethod
    def _char_width(ch):
        code = ord(ch)
        if (0x1100 <= code <= 0x115F or 0x2E80 <= code <= 0xA4CF or
            0xAC00 <= code <= 0xD7A3 or 0xF900 <= code <= 0xFAFF or
            0xFE10 <= code <= 0xFE19 or 0xFE30 <= code <= 0xFE6F or
            0xFF01 <= code <= 0xFF60 or 0xFFE0 <= code <= 0xFFE6 or
            0x20000 <= code <= 0x2FFFF):
            return 6
        return 4

    @staticmethod
    def _wrap_text(text, max_width_px):
        lines = []
        current_line = ""
        current_width = 0
        for ch in text:
            cw = DbcViewer._char_width(ch)
            if current_width + cw > max_width_px and current_line:
                lines.append(current_line)
                current_line = ch
                current_width = cw
            else:
                current_line += ch
                current_width += cw
        if current_line:
            lines.append(current_line)
        return lines if lines else [""]

    # ==================== 信号位布局绘制 ====================

    def _draw_layout(self, msg):
        self.canvas.delete("all")
        if not msg.signals:
            self.canvas.create_text(300, 180, text="无信号", fill="gray", font=("", 14))
            return

        byte_count = msg.length
        pixel_per_byte = 80
        pixel_per_bit = pixel_per_byte / 8
        base_row_height = 28
        header_h = 32
        left_margin = 20
        top_margin = 20
        label_font = 7
        line_height = 10

        self.canvas.create_text(left_margin - 5, top_margin + 8, text="Byte", font=("", 8), anchor=tk.E, fill="gray")

        for byte_idx in range(byte_count):
            x0 = left_margin + byte_idx * pixel_per_byte
            byte_color = style.BYTE_ODD if byte_idx % 2 == 0 else style.BYTE_EVEN
            self.canvas.create_rectangle(x0, top_margin, x0 + pixel_per_byte, top_margin + header_h,
                                         fill=byte_color, outline="gray")
            self.canvas.create_text(x0 + pixel_per_byte / 2, top_margin + 12,
                                    text=f"Byte {byte_idx}", font=("", 7), fill="#333")
            for bit_off in range(8):
                self.canvas.create_text(x0 + pixel_per_byte - bit_off * pixel_per_bit - pixel_per_bit / 2,
                                        top_margin + 23, text=str(bit_off), font=("", 6), fill="#666")

        canvas_width = left_margin + byte_count * pixel_per_byte + 40
        allocated = []
        signal_rows = []

        for sig in msg.signals:
            start_byte = sig.start // 8
            start_bit = sig.start % 8
            end_bit_abs = sig.start + sig.length - 1
            end_byte = end_bit_abs // 8
            end_bit = end_bit_abs % 8

            y = None
            for candidate_row in range(len(signal_rows) + 1):
                ok = True
                for (bs, bts, be, bte, row) in allocated:
                    if row != candidate_row:
                        continue
                    if not (start_byte > be or end_byte < bs or
                            (start_byte == be and (end_bit < bts or start_bit > bte))):
                        ok = False
                        break
                if ok:
                    y = candidate_row
                    break
            if y is None:
                y = len(signal_rows)
            if y >= len(signal_rows):
                signal_rows.append([])
            signal_rows[y].append(sig)
            allocated.append((start_byte, start_bit, end_byte, end_bit, y))

        colors = style.SIGNAL_COLORS

        sig_lines_map = {}
        for sig in msg.signals:
            byte_s = sig.start // 8
            bit_s = sig.start % 8
            end_abs = sig.start + sig.length - 1
            byte_e = end_abs // 8
            bit_e = end_abs % 8
            x_start = left_margin + byte_s * pixel_per_byte + pixel_per_byte - (bit_s + 1) * pixel_per_bit
            x_end   = left_margin + byte_e * pixel_per_byte + pixel_per_byte - bit_e * pixel_per_bit
            sig_left = min(x_start, x_end)
            sig_right = max(x_start, x_end)
            sig_width = sig_right - sig_left
            line_max_px = pixel_per_byte * sig.length / 8
            if line_max_px >= 8:
                lines = self._wrap_text(sig.name, line_max_px - 2)
            else:
                lines = []
            sig_lines_map[sig.name] = (lines, sig_left, sig_right, sig_width)

        row_heights = []
        for row_sigs in signal_rows:
            max_lines = 1
            for sig in row_sigs:
                lines, *rest = sig_lines_map[sig.name]
                if lines:
                    max_lines = max(max_lines, len(lines))
            row_heights.append(base_row_height + (max_lines - 1) * line_height)

        row_start_y = top_margin + header_h + 10
        current_y = row_start_y

        for row_idx, row_sigs in enumerate(signal_rows):
            row_h = row_heights[row_idx]
            y0 = current_y
            for si, sig in enumerate(row_sigs):
                color = colors[si % len(colors)]
                byte_s = sig.start // 8
                bit_s = sig.start % 8
                end_abs = sig.start + sig.length - 1
                byte_e = end_abs // 8
                bit_e = end_abs % 8

                for b in range(byte_s, byte_e + 1):
                    bx = left_margin + b * pixel_per_byte
                    if b == byte_s and b == byte_e:
                        b_start_bit = bit_s
                        b_end_bit = bit_e
                    elif b == byte_s:
                        b_start_bit = bit_s
                        b_end_bit = 7
                    elif b == byte_e:
                        b_start_bit = 0
                        b_end_bit = bit_e
                    else:
                        b_start_bit = 0
                        b_end_bit = 7

                    rect_x0 = bx + pixel_per_byte - (b_start_bit + 1) * pixel_per_bit
                    rect_x1 = bx + pixel_per_byte - b_end_bit * pixel_per_bit
                    self.canvas.create_rectangle(rect_x0, y0, rect_x1, y0 + row_h - 4,
                                                 fill=color, outline="#888")

                lines, sig_left, sig_right, sig_width = sig_lines_map[sig.name]
                if lines and sig_width >= 8:
                    text_x = sig_left + sig_width / 2
                    total_text_h = len(lines) * line_height
                    text_start_y = y0 + (row_h - total_text_h) / 2 - 2
                    for li, line in enumerate(lines):
                        self.canvas.create_text(text_x, text_start_y + li * line_height,
                                                text=line, font=("", label_font),
                                                anchor=tk.CENTER, fill="#000")

            current_y += row_h

        total_height = current_y + 20
        self.canvas.configure(scrollregion=(0, 0, canvas_width, total_height),
                              height=min(total_height + 10, 500))

    # ==================== 信号详情表格 ====================

    def _populate_signal_details(self, msg):
        for item in self.sig_tree.get_children():
            self.sig_tree.delete(item)
        for sig in msg.signals:
            self.sig_tree.insert("", tk.END, values=(
                sig.name,
                sig.start,
                sig.length,
                sig.byte_order,
                f"{sig.scale:.3g}" if sig.scale else "-",
                f"{sig.offset:.3g}" if sig.offset else "-",
                f"{sig.minimum:.3g}" if sig.minimum is not None else "-",
                f"{sig.maximum:.3g}" if sig.maximum is not None else "-",
                sig.unit or "-",
            ))


def main():
    root = tk.Tk()
    app = DbcViewer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
