# The Magic Tools

一个集合了多种车载诊断（UDS）、CAN 总线、ROS Bag 处理等常用工具的“魔法工具箱”。

---

## 📁 目录结构

```
The_magic_tools/
├── bag_parser/                # ROS Bag 解析工具
│   └── bag_parserV1.2         # 解析器可执行文件/脚本
├── Canking_Ran_on_linux/      # CAN 总线测试工具（Linux版）
│   └── Canking_Ran            # 主程序
├── DBC_shower/                # DBC 文件可视化/查看工具
│   ├── dbc_shower             # 可执行文件
│   ├── dbc_shower.py          # Python 源码
│   └── style.py               # 样式/配置文件
├── Dcoker_Win/                # Docker Windows 容器配置
│   ├── docker-compose.yml
│   └── Dockerfile
├── rosbag_editor/             # ROS Bag 编辑器（Qt 图形界面）
│   ├── README.md              # 子项目说明
│   ├── src/                   # 源码目录
│   │   ├── CMakeLists.txt     # CMake 构建配置
│   │   ├── package.xml        # ROS 包描述
│   │   ├── desktop/           # 桌面图标资源
│   │   └── src/               # C++/Qt 源码
│   └── start.sh               # 启动脚本
├── Router/                    # 路由/转发工具
│   ├── router                 # 可执行文件
│   └── router.py              # Python 源码
├── connect.sh                 # VPN连接脚本
├── rog.sh                     # ROG 专用脚本（硬件/环境配置）
└── Readme.md                  # 本文件
```

---
