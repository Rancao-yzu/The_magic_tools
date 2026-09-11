#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# record_corner_radar.py —— 启动即录（只生成一个 bag）

import os
import sys
import time
import signal
import subprocess
from datetime import datetime
from pathlib import Path

import rospy
from rospy.msg import AnyMsg

# ============ 配置区 ============
TOPICS = [
    "/wf/corner_radar/parsed/float_data_1",
    "/wf/corner_radar/simulate_data_1",
]

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SCRIPT_DIR / "bags"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ⚠️ 如果你运行脚本的 shell 已经 source 过 ROS 环境，
#    保持空列表即可，这样 rosbag 直接 exec，启动最快。
#    如果没 source，再取消下面的注释。
SETUP_SCRIPTS = [
    # "/opt/ros/noetic/setup.bash",
    # "/home/yourname/your_ws/devel/setup.bash",
]

FRESHNESS_TIMEOUT = 2.0   # 数据"新鲜度"阈值（秒）
POLL_INTERVAL = 0.2       # 主循环轮询间隔（秒）

# ============ 全局 ============
_bag_proc = None
_running = True
_last_seen = {t: 0.0 for t in TOPICS}


def log(msg):
    print(msg, flush=True)


# ---------- rospy 回调（仅用于状态打印） ----------
def _on_msg(_msg, topic):
    _last_seen[topic] = time.time()


def is_topic_alive(topic):
    return (time.time() - _last_seen.get(topic, 0.0)) < FRESHNESS_TIMEOUT


def all_topics_alive():
    return all(is_topic_alive(t) for t in TOPICS)


# ---------- 录制控制 ----------
def start_recording():
    global _bag_proc
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bag_path = OUTPUT_DIR / f"corner_radar_{ts}.bag"

    cmd = ["rosbag", "record", "-O", str(bag_path), *TOPICS]

    if SETUP_SCRIPTS:
        src = " && ".join(f"source {s}" for s in SETUP_SCRIPTS)
        full_cmd = ["bash", "-c", f"{src} && exec " + " ".join(cmd)]
    else:
        full_cmd = cmd  # 直接 exec，省一层 bash，快几十毫秒

    log(f"==> rosbag 输出文件: {bag_path}")
    _bag_proc = subprocess.Popen(full_cmd)
    return bag_path


def stop_recording():
    global _bag_proc
    if _bag_proc and _bag_proc.poll() is None:
        log("==> 停止录制...")
        try:
            _bag_proc.send_signal(signal.SIGINT)
            _bag_proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            _bag_proc.kill()
            _bag_proc.wait()
        except Exception as e:
            log(f"    [警告] 停止录制出错: {e}")
    _bag_proc = None


# ---------- 信号 ----------
def shutdown_handler(signum, frame):
    global _running
    _running = False
    log("\n==> 收到退出信号...")
    stop_recording()


# ---------- 主流程 ----------
def main():
    global _bag_proc, _running

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    log("=" * 60)
    log("立即启动录制（不等 topic）...")
    for t in TOPICS:
        log(f"  - {t}")
    log("=" * 60)

    # ★ 关键：一开始就启动 rosbag，抢时间
    try:
        start_recording()
    except Exception as e:
        log(f"[错误] 启动录制失败: {e}")
        return

    # 再初始化 rospy 监听（只用于打印状态，不影响录制）
    rospy.init_node("corner_radar_watcher", anonymous=True, disable_signals=True)
    for t in TOPICS:
        rospy.Subscriber(t, AnyMsg, _on_msg, callback_args=t)

    log("==> 正在等待 topic 数据...")

    data_started = False
    while _running:
        time.sleep(POLL_INTERVAL)

        # rosbag 挂了（磁盘满、类型错误等）→ 直接退出，不再启新 bag
        if _bag_proc is None or _bag_proc.poll() is not None:
            code = _bag_proc.returncode if _bag_proc else "unknown"
            log(f"==> rosbag 进程已退出 (returncode={code})")
            _running = False
            break

        # 两个 topic 都有数据了 → 打印一次提示
        if not data_started and all_topics_alive():
            log("")
            log("---开始接受——————")
            log("")
            data_started = True

    stop_recording()
    log("==> 已退出")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        shutdown_handler(None, None)
