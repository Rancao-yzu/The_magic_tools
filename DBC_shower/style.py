"""
DBC 工具统一样式表
提供颜色、字体、ttk 主题配置，供 dbc_parser_gui.py 和 dbc_shower.py 共用。
"""

import tkinter as tk
from tkinter import ttk

# ==================== 调色板 ====================

PRIMARY       = "#2563EB"   # 主色 - 按钮 / 选中
PRIMARY_LIGHT = "#60A5FA"   # 主色浅色
SUCCESS       = "#16A34A"   # 成功 / 运行中
SUCCESS_LIGHT = "#4ADE80"   # 成功浅色
WARNING       = "#EA580C"   # 警告
WARNING_LIGHT = "#FB923C"   # 警告浅色
DANGER        = "#DC2626"   # 错误 / 停止
DANGER_LIGHT  = "#F87171"   # 错误浅色
BG            = "#F1F5F9"   # 页面背景
BG_LIGHT      = "#F8FAFC"   # 浅色背景
SURFACE       = "#FFFFFF"   # 面板底色
BORDER        = "#CBD5E1"   # 边框
BORDER_LIGHT  = "#E2E8F0"   # 浅色边框
TEXT          = "#1E293B"   # 主文字
TEXT_SECONDARY = "#64748B"  # 次要文字
TEXT_DISABLED  = "#9B9B9B"  # 禁用态文字
HOVER_BG      = "#E2E8F0"   # 悬停背景
ACTIVE_BG     = "#CBD5E1"   # 激活背景
BG_DARK       = "#E2E8F0"   # 深色背景
BORDER_DISABLED = "#CBD5E1"  # 禁用状态边框

# Canvas 位布局颜色
CANVAS_BG      = "#FFFFFF"
BYTE_ODD       = "#E8F0E8"
BYTE_EVEN      = "#D8E8D8"
SIGNAL_COLORS  = [
    "#FFB3BA", "#BAE1FF", "#BAFFC9", "#FFFFBA",
    "#E8BAFF", "#FFD9BA", "#FFF2B3", "#FFB3DE",
    "#B3D4FF", "#C9FFB3", "#D9B3FF", "#BAFFF5",
]

# 滚动条颜色
SCROLL_TROUGH  = "#F1F5F9"   # 轨道背景
SCROLL_SLIDER  = "#CBD5E1"   # 滑块颜色
SCROLL_HOVER   = "#94A3B8"   # 滑块悬停颜色
SCROLL_ACTIVE  = "#64748B"   # 滑块激活颜色
SCROLL_ARROW   = "#64748B"   # 箭头颜色

# ==================== 字体 ====================

FONT_MONO    = ("Consolas", 10)       # 等宽 - 报文详情
FONT_BODY    = ("Segoe UI", 9)        # 正文
FONT_SMALL   = ("Segoe UI", 8)        # 小字
FONT_TINY    = ("Segoe UI", 7)        # 微小
FONT_HEADING = ("Segoe UI", 10, "bold")  # 标题
FONT_TREEVIEW = ("Segoe UI", 9)       # Treeview字体

# ==================== 间距 ====================

PAD_X = 5
PAD_Y = 5
TREE_ROW_HEIGHT = 28  # Treeview行高

# ==================== 主题应用 ====================

def apply_style(root: tk.Tk):
    """配置 ttk 全局主题和控件样式"""

    style = ttk.Style(root)

    # --- 基础主题 ---
    available = style.theme_names()
    if "clam" in available:
        style.theme_use("clam")

    # --- 框架 ---
    style.configure("TLabelframe", 
                    background=SURFACE, 
                    bordercolor=BORDER,
                    relief="solid", 
                    borderwidth=1)
    style.configure("TLabelframe.Label", 
                    background=SURFACE, 
                    foreground=TEXT,
                    font=FONT_HEADING)
    style.configure("TFrame", 
                    background=BG)

    # --- 按钮 ---
    style.configure("TButton", 
                    background=SURFACE, 
                    foreground=TEXT,
                    borderwidth=1, 
                    focusthickness=0, 
                    padding=(8, 4),
                    font=FONT_BODY)
    style.map("TButton",
              background=[("active", HOVER_BG), 
                         ("pressed", ACTIVE_BG),
                         ("disabled", BG)],
              foreground=[("disabled", TEXT_DISABLED)],
              relief=[("pressed", "sunken")])

    # --- 标签 ---
    style.configure("TLabel", 
                    background=BG, 
                    foreground=TEXT, 
                    font=FONT_BODY)

    # --- 输入框 ---
    style.configure("TEntry", 
                    fieldbackground=SURFACE, 
                    foreground=TEXT,
                    borderwidth=1, 
                    padding=4, 
                    font=FONT_BODY)
    style.map("TEntry",
              fieldbackground=[("readonly", BG_LIGHT)],
              bordercolor=[("focus", PRIMARY), 
                          ("!focus", BORDER)],
              lightcolor=[("focus", PRIMARY)],
              darkcolor=[("focus", PRIMARY)])

    # --- 下拉框 ---
    style.configure("TCombobox", 
                    fieldbackground=SURFACE, 
                    foreground=TEXT,
                    arrowcolor=TEXT, 
                    padding=4, 
                    font=FONT_BODY)
    style.map("TCombobox",
              fieldbackground=[("readonly", SURFACE)],
              foreground=[("readonly", TEXT)])
    
    style.configure("Disabled.TCombobox",
                fieldbackground=BG_DARK,
                foreground=TEXT_DISABLED,
                arrowcolor=TEXT_DISABLED,
                bordercolor=BORDER_DISABLED)

    # ==== Treeview 优化样式 ====
    style.configure("Treeview",
                    background=SURFACE,
                    foreground=TEXT,
                    fieldbackground=SURFACE,
                    borderwidth=0,
                    font=FONT_TREEVIEW,
                    rowheight=TREE_ROW_HEIGHT,
                    relief="flat")
    
    # Treeview 表头样式
    style.configure("Treeview.Heading",
                    background=BG,
                    foreground=TEXT,
                    font=FONT_HEADING,
                    borderwidth=1,
                    relief="flat",
                    padding=(8, 4))
    
    # Treeview 状态映射
    style.map("Treeview.Heading",
              background=[("active", HOVER_BG)],
              relief=[("active", "flat")])
    
    style.map("Treeview",
              background=[("selected", PRIMARY)],
              foreground=[("selected", SURFACE)])
    
    # 添加斑马线效果配置函数
    _configure_tree_zebra_style(style)
    
    # ==== 滚动条优化样式 ====
    _configure_scrollbar_styles(style)
    
    # --- 状态栏标签 ---
    style.configure("Status.TLabel", 
                    background=BORDER, 
                    foreground=TEXT,
                    font=FONT_SMALL, 
                    padding=(6, 3))

    # --- 辅助色标签 ---
    style.configure("Secondary.TLabel", 
                    foreground=TEXT_SECONDARY)
    
    # --- 分隔线 ---
    style.configure("TSeparator",
                    background=BORDER_LIGHT)

def _configure_scrollbar_styles(style: ttk.Style):
    """配置滚动条样式"""
    
    # 垂直滚动条
    style.configure("Vertical.TScrollbar",
                    background=SCROLL_TROUGH,
                    troughcolor=SCROLL_TROUGH,
                    bordercolor=SCROLL_TROUGH,
                    arrowcolor=SCROLL_ARROW,
                    width=12,
                    borderwidth=0,
                    relief="flat")
    
    # 水平滚动条
    style.configure("Horizontal.TScrollbar",
                    background=SCROLL_TROUGH,
                    troughcolor=SCROLL_TROUGH,
                    bordercolor=SCROLL_TROUGH,
                    arrowcolor=SCROLL_ARROW,
                    height=12,
                    borderwidth=0,
                    relief="flat")
    
    # 滚动条滑块样式映射
    style.map("Vertical.TScrollbar",
              background=[("pressed", SCROLL_ACTIVE),
                         ("active", SCROLL_HOVER),
                         ("!disabled", SCROLL_SLIDER)],
              arrowsize=[("pressed", 9),
                        ("!disabled", 8)])
    
    style.map("Horizontal.TScrollbar",
              background=[("pressed", SCROLL_ACTIVE),
                         ("active", SCROLL_HOVER),
                         ("!disabled", SCROLL_SLIDER)],
              arrowsize=[("pressed", 9),
                        ("!disabled", 8)])

def _configure_tree_zebra_style(style: ttk.Style):
    """为Treeview配置斑马线样式"""
    # 通过布局修改器添加alternate样式
    style.layout("Treeview.Item",
                 [('Treeitem.padding',
                   {'sticky': 'nswe',
                    'children': [('Treeitem.indicator', {'side': 'left', 'sticky': ''}),
                                 ('Treeitem.image', {'side': 'left', 'sticky': ''}),
                                 ('Treeitem.text', {'side': 'left', 'sticky': ''})]})])

# ==================== Treeview 高级功能 ====================

def configure_tree_tags(tree: ttk.Treeview):
    """为 Treeview 组件设置常用行标签样式"""
    # 斑马线标签
    tree.tag_configure("oddrow", background=SURFACE)
    tree.tag_configure("evenrow", background=BG_LIGHT)
    
    # 信号相关标签
    tree.tag_configure("signal", 
                       foreground=SUCCESS, 
                       font=FONT_TREEVIEW)
    tree.tag_configure("no_signal", 
                       foreground=TEXT_DISABLED, 
                       font=FONT_TREEVIEW)
    
    # 状态标签
    tree.tag_configure("success", 
                       background=SUCCESS_LIGHT, 
                       foreground=SUCCESS)
    tree.tag_configure("warning", 
                       background=WARNING_LIGHT,
                       foreground=WARNING)
    tree.tag_configure("error", 
                       background=DANGER_LIGHT,
                       foreground=DANGER)
    
    # 高亮标签
    tree.tag_configure("highlight", 
                       background=PRIMARY_LIGHT,
                       foreground=PRIMARY)
    
    # 禁用标签
    tree.tag_configure("disabled", 
                       background=BG_LIGHT,
                       foreground=TEXT_DISABLED)

def create_scrollable_frame(parent, **kwargs):
    """创建带滚动条的框架（适用于大量数据展示）"""
    container = ttk.Frame(parent)
    
    # 创建Canvas和滚动条
    canvas = tk.Canvas(container, 
                      highlightthickness=0,
                      background=BG)
    
    v_scrollbar = ttk.Scrollbar(container, 
                               orient="vertical", 
                               command=canvas.yview)
    h_scrollbar = ttk.Scrollbar(container, 
                               orient="horizontal", 
                               command=canvas.xview)
    
    scrollable_frame = ttk.Frame(canvas)
    
    # 绑定滚动事件
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=v_scrollbar.set,
                    xscrollcommand=h_scrollbar.set)
    
    # 网格布局
    canvas.grid(row=0, column=0, sticky="nsew")
    v_scrollbar.grid(row=0, column=1, sticky="ns")
    h_scrollbar.grid(row=1, column=0, sticky="ew")
    
    container.grid_rowconfigure(0, weight=1)
    container.grid_columnconfigure(0, weight=1)
    
    # 鼠标滚轮支持
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    return container, scrollable_frame

def style_treeview_widgets(tree: ttk.Treeview, enable_zebra=True):
    """美化Treeview组件，包括滚动条、行高、字体等"""
    
    # 设置行高
    tree.configure(height=15)  # 默认显示15行
    
    # 配置标签
    configure_tree_tags(tree)
    
    # 如果启用斑马线
    if enable_zebra:
        tree.bind("<<TreeviewOpen>>", lambda e: update_zebra_stripes(tree))
        tree.bind("<<TreeviewClose>>", lambda e: update_zebra_stripes(tree))
        tree.bind("<Configure>", lambda e: update_zebra_stripes(tree))
        
        # 初始应用斑马线
        update_zebra_stripes(tree)
    
    # 设置网格线
    tree.configure(show="tree headings")
    
    # 配置列宽自适应
    for col in tree["columns"]:
        tree.heading(col, text=col, anchor="w")
        tree.column(col, anchor="w", stretch=True, minwidth=50)
    
    return tree

def update_zebra_stripes(tree: ttk.Treeview):
    """更新Treeview的斑马线条纹"""
    children = tree.get_children()
    for index, item in enumerate(children):
        tag = "evenrow" if index % 2 == 0 else "oddrow"
        tags = list(tree.item(item, "tags"))
        
        # 移除旧的斑马线标签
        if "evenrow" in tags:
            tags.remove("evenrow")
        if "oddrow" in tags:
            tags.remove("oddrow")
        
        # 添加新的斑马线标签
        tags.append(tag)
        tree.item(item, tags=tags)
        
        # 递归处理子项
        _update_child_zebra_stripes(tree, item, index)

def _update_child_zebra_stripes(tree: ttk.Treeview, parent_item, parent_index):
    """递归更新子项的斑马线条纹"""
    children = tree.get_children(parent_item)
    for child_index, child_item in enumerate(children):
        # 子项的索引是父项索引 + 子项在父项中的位置
        absolute_index = parent_index + child_index + 1
        tag = "evenrow" if absolute_index % 2 == 0 else "oddrow"
        tags = list(tree.item(child_item, "tags"))
        
        # 移除旧的斑马线标签
        if "evenrow" in tags:
            tags.remove("evenrow")
        if "oddrow" in tags:
            tags.remove("oddrow")
        
        # 添加新的斑马线标签
        tags.append(tag)
        tree.item(child_item, tags=tags)
        
        # 递归处理孙子项
        _update_child_zebra_stripes(tree, child_item, absolute_index)

# ==================== 使用示例 ====================

if __name__ == "__main__":
    # 测试样式
    root = tk.Tk()
    root.title("样式测试")
    root.geometry("800x600")
    
    apply_style(root)
    
    # 创建主框架
    main_frame = ttk.Frame(root, padding=20)
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    # 创建带滚动条的Treeview
    container = ttk.Frame(main_frame)
    container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Treeview
    tree = ttk.Treeview(container, columns=("ID", "名称", "值", "单位", "描述"), show="headings")
    
    # 设置列标题
    tree.heading("ID", text="ID")
    tree.heading("名称", text="信号名称")
    tree.heading("值", text="数值")
    tree.heading("单位", text="单位")
    tree.heading("描述", text="描述")
    
    # 设置列宽
    tree.column("ID", width=80, anchor="center")
    tree.column("名称", width=150)
    tree.column("值", width=100, anchor="center")
    tree.column("单位", width=80, anchor="center")
    tree.column("描述", width=200)
    
    # 美化Treeview
    style_treeview_widgets(tree, enable_zebra=True)
    
    # 添加示例数据
    sample_data = [
        ("0x100", "Engine_Speed", "2500", "RPM", "发动机转速"),
        ("0x101", "Vehicle_Speed", "80", "km/h", "车速"),
        ("0x102", "Coolant_Temp", "90", "°C", "冷却液温度"),
        ("0x103", "Fuel_Level", "65", "%", "燃油液位"),
        ("0x104", "Battery_Voltage", "12.5", "V", "电池电压"),
        ("0x105", "Odometer", "12500", "km", "里程表"),
        ("0x106", "Oil_Pressure", "3.2", "bar", "机油压力"),
        ("0x107", "Brake_Pressure", "150", "kPa", "刹车压力"),
        ("0x108", "Steering_Angle", "15.5", "deg", "转向角度"),
        ("0x109", "Accelerator", "45", "%", "油门踏板"),
        ("0x10A", "Brake_Pedal", "0", "%", "刹车踏板"),
        ("0x10B", "Gear_Position", "D", "", "档位"),
        ("0x10C", "Door_Status", "Closed", "", "车门状态"),
    ]
    
    for i, data in enumerate(sample_data):
        tree.insert("", "end", values=data, tags=("signal" if i % 3 != 0 else "no_signal"))
    
    # 滚动条
    v_scrollbar = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
    h_scrollbar = ttk.Scrollbar(container, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
    
    # 布局
    tree.grid(row=0, column=0, sticky="nsew")
    v_scrollbar.grid(row=0, column=1, sticky="ns")
    h_scrollbar.grid(row=1, column=0, sticky="ew")
    
    container.grid_rowconfigure(0, weight=1)
    container.grid_columnconfigure(0, weight=1)
    
    # 按钮框架
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill=tk.X, pady=(20, 0))
    
    ttk.Button(button_frame, text="刷新", width=10).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_frame, text="导出", width=10).pack(side=tk.LEFT, padx=5)
    ttk.Button(button_frame, text="清空", width=10).pack(side=tk.LEFT, padx=5)
    
    root.mainloop()