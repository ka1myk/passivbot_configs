import subprocess

gs_order = subprocess.Popen(
    [
        "python3",
        "passivbot.py",
        "binance_01",
        "XRPBUSD",
        "/root/passivbot_configs/long.json",
        "-lm",
        "gs",
        "-sm",
        "gs"
    ]
)
