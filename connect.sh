#!/bin/bash

# ============================================
# FortiClient VPN 后台自动重连脚本
# sudo add-apt-repository ppa:dwmw2/openconnect
# sudo apt update
# sudo apt install openconnect
# ============================================

VPN_HOST="connect.weifu.com.cn"
VPN_PORT="65210"
VPN_USER="ran.cao"
VPN_PASS="zlxcdjCR58@"
# 使用 openconnect 提示的正确指纹
SERVER_CERT="pin-sha256:n1VCGQ7Hzh0UX+S6IiuFU+StXynljk8lbuw46oN1LO0="

while true; do
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 开始连接 VPN..."
    
    echo "$VPN_PASS" | sudo openconnect \
        --user="$VPN_USER" \
        --passwd-on-stdin \
        --protocol=fortinet \
        --servercert="$SERVER_CERT" \
        "https://$VPN_HOST:$VPN_PORT"
    
    echo "$(date '+%Y-%m-%d %H:%M:%S') - VPN 断开，10秒后重连..."
    sleep 10
done
