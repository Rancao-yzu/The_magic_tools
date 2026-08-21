#!/usr/bin/env python3
"""
路由设置脚本（UI 版）

用途：在多网卡环境下分流网络流量
  - 默认流量(A)：所有普通网络请求走此网卡（即"99%"的部分）
  - 内网流量(B)：仅访问公司内网 10.68.100.x 走此网卡（即"1%"的部分）

使用方法：python3 router.py
（执行路由变更时若非 root 会自动通过 pkexec 提权弹窗）
"""

import os
import re
import shlex
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk

# 公司内网目标网段（访问此网段的流量走 B）
DEFAULT_INTERNAL_NET = "10.68.100.0/24"

# 需要排除的虚拟网卡
EXCLUDE_IFACES = {"lo", "docker0"}

# 扁平纯白主题色
BG = "#FFFFFF"
FG = "#000000"
SUB_FG = "#666666"
LINE = "#E0E0E0"
HOVER = "#F5F5F5"


def run(cmd):
    """执行 shell 命令，返回 (返回码, 标准输出, 标准错误)"""
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def list_up_interfaces():
    """列出处于 UP 状态的网卡（排除 lo、docker0 等虚拟接口）"""
    rc, out, _ = run("ip -o link show")
    if rc != 0:
        return []
    result = []
    for line in out.splitlines():
        # 形如: 4: wlo1: <BROADCAST,MULTICAST,UP,LOWER_UP> ...
        m = re.match(r"\d+:\s+(\S+?):\s+<([^>]*)>", line)
        if not m:
            continue
        name, flags = m.group(1), m.group(2)
        if "UP" not in flags.split(","):
            continue
        if name in EXCLUDE_IFACES:
            continue
        result.append(name)
    return result


def get_gateway(iface):
    """获取指定网卡的默认网关"""
    _, out, _ = run(f"ip route show dev {iface}")
    for line in out.splitlines():
        if line.startswith("default via "):
            return line.split()[2]
    return None


def friendly_name(iface):
    """给网卡名加用户友好的类型标签，便于不懂接口名的用户识别"""
    lower = iface.lower()
    if lower.startswith("wl"):
        kind = "WiFi"
    elif lower.startswith("enx"):
        kind = "USB 网卡"
    elif lower.startswith(("eno", "enp", "eth")):
        kind = "以太网"
    else:
        kind = "网卡"
    return f"{kind} · {iface}"


def default_route_friendly():
    """返回当前默认路由的用户友好描述（解析 via/dev 转成友好名，按设备+网关去重）"""
    _, out, _ = run("ip route show default")
    if not out:
        return "无"
    seen = set()
    items = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        gw = parts[2] if len(parts) > 2 and parts[1] == "via" else ""
        dev = ""
        if "dev" in parts:
            i = parts.index("dev")
            if i + 1 < len(parts):
                dev = parts[i + 1]
        # 按 (设备, 网关) 去重，避免同网卡多条默认路由重复展示
        key = (dev, gw)
        if key in seen:
            continue
        seen.add(key)
        if gw and dev:
            items.append(f"{friendly_name(dev)}  网关 {gw}")
        else:
            items.append(line)
    return "\n".join(items) if items else "无"


def route_show_friendly():
    """返回 ip route show 全量路由表的用户友好输出（过滤 docker 等虚拟网卡路由）"""
    _, out, _ = run("ip route show")
    if not out:
        return "（无路由）"
    lines_out = []
    seen_default = set()
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        dst = parts[0]
        gw = ""
        dev = ""
        src = ""
        if "via" in parts:
            i = parts.index("via")
            if i + 1 < len(parts):
                gw = parts[i + 1]
        if "dev" in parts:
            i = parts.index("dev")
            if i + 1 < len(parts):
                dev = parts[i + 1]
        if "src" in parts:
            i = parts.index("src")
            if i + 1 < len(parts):
                src = parts[i + 1]
        # 过滤 docker 等虚拟网卡路由
        if dev in EXCLUDE_IFACES:
            continue
        fdev = friendly_name(dev) if dev else ""
        if dst == "default":
            # 默认路由按 (设备, 网关) 去重
            key = (dev, gw)
            if key in seen_default:
                continue
            seen_default.add(key)
            lines_out.append(f"默认网络: {fdev}  网关 {gw}" if gw and dev else line)
        elif gw:
            # 经网关的路由（转发）
            lines_out.append(f"到 {dst}: 经 {fdev} 网关 {gw}" if dev else line)
        elif "scope" in parts and "link" in parts:
            # 直连网段路由
            txt = f"直连 {dst}: {fdev}"
            if src:
                txt += f"  本机 {src}"
            lines_out.append(txt if dev else line)
        else:
            lines_out.append(line)
    return "\n".join(lines_out) if lines_out else "（无路由）"


def run_as_root(cmd):
    """非 root 时通过 pkexec 提权执行命令；root 则直接执行"""
    if os.geteuid() == 0:
        return run(cmd)
    return run(f"pkexec sh -c {shlex.quote(cmd)}")


class RouterApp:
    """路由设置主界面"""

    def __init__(self, root):
        self.root = root
        root.title("路由设置")
        root.configure(bg=BG)
        root.geometry("900x520")

        self.ifaces = []             # 当前 UP 网卡列表
        self.display_to_iface = {}   # 友好名 -> 接口名 的映射
        self.var_a = tk.StringVar()  # 默认网络(A) 选中网卡
        self.var_b = tk.StringVar()  # 内网网络(B) 选中网卡
        self.var_net = tk.StringVar(value=DEFAULT_INTERNAL_NET)

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # 左右分栏：左侧操作区，右侧日志区
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True)

        left = tk.Frame(main, bg=BG)
        left.pack(side="left", fill="y", padx=(20, 10), pady=20, anchor="n")

        right = tk.Frame(main, bg=BG)
        right.pack(side="left", fill="both", expand=True, padx=(10, 20), pady=20)

        # ---- 左侧操作区 ----
        tk.Label(left, text="路由设置", bg=BG, fg=FG,
                 font=("Sans", 16, "bold")).pack(anchor="w")
        tk.Label(left, text="A=默认网络（普通流量）  B=内网网络（访问公司内网）",
                 bg=BG, fg=SUB_FG).pack(anchor="w", pady=(6, 0))

        # 网卡列表区
        tk.Label(left, text="网卡列表", bg=BG, fg=FG,
                 font=("Sans", 11, "bold")).pack(anchor="w", pady=(12, 4))
        self.list_box = tk.Frame(left, bg=BG)
        self.list_box.pack(fill="x")

        # A/B 选择
        sel = tk.Frame(left, bg=BG)
        sel.pack(fill="x", pady=12)
        tk.Label(sel, text="默认网络(A):", bg=BG, fg=FG).grid(row=0, column=0, sticky="w", pady=3)
        self.combo_a = ttk.Combobox(sel, textvariable=self.var_a, state="readonly", width=30)
        self.combo_a.grid(row=0, column=1, sticky="w", padx=(8, 0), pady=3)
        tk.Label(sel, text="内网网络(B):", bg=BG, fg=FG).grid(row=1, column=0, sticky="w", pady=3)
        self.combo_b = ttk.Combobox(sel, textvariable=self.var_b, state="readonly", width=30)
        self.combo_b.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=3)

        # 内网目标网段
        net_frame = tk.Frame(left, bg=BG)
        net_frame.pack(fill="x", pady=4)
        tk.Label(net_frame, text="内网目标网段:", bg=BG, fg=FG).pack(side="left")
        tk.Entry(net_frame, textvariable=self.var_net, width=24,
                 bg=BG, fg=FG, insertbackground=FG, relief="flat",
                 highlightthickness=1, highlightbackground=LINE,
                 highlightcolor=LINE).pack(side="left", padx=(8, 0))

        # 操作按钮
        btn = tk.Frame(left, bg=BG)
        btn.pack(fill="x", pady=12)
        ttk.Button(btn, text="刷新网卡", command=self.refresh).pack(side="left")
        ttk.Button(btn, text="执行路由设置", command=self.apply_routes).pack(side="left", padx=8)
        ttk.Button(btn, text="取消路由设置", command=self.cancel_routes).pack(side="left")
        ttk.Button(btn, text="查看路由状态", command=self.show_routes).pack(side="left", padx=8)

        # 当前默认路由展示
        self.old_label = tk.Label(left, text="", bg=BG, fg=SUB_FG,
                                  wraplength=320, justify="left")
        self.old_label.pack(anchor="w", pady=(2, 0))

        # ---- 右侧日志区 ----
        tk.Label(right, text="日志", bg=BG, fg=FG,
                 font=("Sans", 11, "bold")).pack(anchor="w", pady=(0, 4))
        log_frame = tk.Frame(right, bg=BG, highlightthickness=1,
                             highlightbackground=LINE)
        log_frame.pack(fill="both", expand=True)
        self.log_text = tk.Text(log_frame, bg=BG, fg=FG, insertbackground=FG,
                                relief="flat", borderwidth=0,
                                font=("Monospace", 9), wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=6, pady=6)
        # 转发路由标红
        self.log_text.tag_config("red", foreground="#CC0000")

    def log(self, msg):
        """追加一行日志，同时打印到终端便于排查"""
        self.log_text.insert("end", msg + "\n")
        self.log_text.see("end")
        print(msg, flush=True)

    def refresh(self):
        """刷新网卡列表和默认路由展示"""
        for w in self.list_box.winfo_children():
            w.destroy()
        # 只保留已拿到网关的网卡（无网关说明未真正联网，不显示也不可选）
        self.ifaces = [n for n in list_up_interfaces() if get_gateway(n)]
        if not self.ifaces:
            tk.Label(self.list_box, text="未发现可用网卡（未获取到网关的网卡已忽略）",
                     bg=BG, fg=SUB_FG).pack(anchor="w")
            self.combo_a["values"] = []
            self.combo_b["values"] = []
            self.var_a.set("")
            self.var_b.set("")
            self.display_to_iface = {}
            return
        # 构造 友好名 -> 接口名 映射，下拉框显示友好名
        self.display_to_iface = {friendly_name(n): n for n in self.ifaces}
        display_names = list(self.display_to_iface.keys())
        for name in self.ifaces:
            gw = get_gateway(name)
            row = tk.Frame(self.list_box, bg=BG)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=friendly_name(name), bg=BG, fg=FG,
                     width=30, anchor="w").pack(side="left")
            tk.Label(row, text=f"网关: {gw}", bg=BG, fg=SUB_FG, anchor="w").pack(side="left")
        self.combo_a["values"] = display_names
        self.combo_b["values"] = display_names
        old = default_route_friendly()
        self.old_label.config(text=f"当前默认网络:\n{old}")
        self.log(f"已刷新网卡: {', '.join(self.ifaces)}")

    def apply_routes(self):
        """执行路由变更"""
        # 下拉框显示的是友好名，这里转回实际接口名
        a = self.display_to_iface.get(self.var_a.get(), "")
        b = self.display_to_iface.get(self.var_b.get(), "")
        net = self.var_net.get().strip() or DEFAULT_INTERNAL_NET
        if not a or not b:
            messagebox.showwarning("提示", "请先选择 A 和 B 网卡")
            return
        if a == b:
            messagebox.showwarning("提示", "A、B 不能为同一张网卡")
            return
        gw_a = get_gateway(a)
        gw_b = get_gateway(b)
        if not gw_a:
            messagebox.showerror("错误", f"无法获取 {a} 的网关")
            return
        if not gw_b:
            messagebox.showerror("错误", f"无法获取 {b} 的网关")
            return

        # 组合两条路由命令，一次提权执行
        cmd = (f"ip route replace default via {gw_a} dev {a} "
               f"&& ip route replace {net} via {gw_b} dev {b}")
        if not messagebox.askyesno("确认", f"将执行:\n{cmd}\n\n确认?"):
            return

        self.log(f"[执行] {cmd}")
        rc, _, err = run_as_root(cmd)
        if rc != 0:
            self.log(f"[失败] {err}")
            messagebox.showerror("失败", err or "命令执行失败")
            return
        self.log("[完成] 路由设置完成")
        messagebox.showinfo("完成", "路由设置完成")
        self.refresh()

    def cancel_routes(self):
        """撤销路由设置：删除内网路由并删除手动加的默认路由（交还 DHCP）"""
        net = self.var_net.get().strip() or DEFAULT_INTERNAL_NET
        # 删内网路由；删默认路由（优先删手动加的 metric 0 那条，DHCP 默认路由保留接管）
        cmd = f"ip route del {net} 2>/dev/null || true; ip route del default 2>/dev/null || true"
        if not messagebox.askyesno("确认", f"将撤销路由设置:\n{cmd}\n\n确认?"):
            return
        self.log(f"[执行] {cmd}")
        rc, _, err = run_as_root(cmd)
        if rc != 0:
            self.log(f"[失败] {err}")
            messagebox.showerror("失败", err or "命令执行失败")
            return
        self.log("[完成] 已撤销路由设置，默认路由交还 DHCP")
        messagebox.showinfo("完成", "已撤销路由设置，默认路由交还 DHCP")
        self.refresh()

    def show_routes(self):
        """查看当前路由表状态，友好输出到日志和终端；转发路由标红"""
        self.log_text.insert("end", "=== 当前路由状态 ===\n")
        print("=== 当前路由状态 ===", flush=True)
        for line in route_show_friendly().splitlines():
            # 转发路由（"到 " 开头）标红
            if line.startswith("到 "):
                self.log_text.insert("end", line + "\n", "red")
            else:
                self.log_text.insert("end", line + "\n")
            print(line, flush=True)
        self.log_text.insert("end", "====================\n")
        self.log_text.see("end")
        print("====================", flush=True)


def main():
    root = tk.Tk()
    # 使用 clam 主题以支持纯白扁平配色
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure("TCombobox", fieldbackground=BG, background=BG, foreground=FG,
                    bordercolor=LINE, lightcolor=LINE, darkcolor=LINE,
                    arrowcolor=FG, padding=4)
    style.map("TCombobox",
              fieldbackground=[("readonly", BG)],
              foreground=[("readonly", FG)],
              bordercolor=[("focus", FG)])
    style.configure("TButton", background=BG, foreground=FG, bordercolor=LINE,
                    focusthickness=0, padding=(12, 6))
    style.map("TButton", background=[("active", HOVER)])
    RouterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
