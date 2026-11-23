from core.ui_widgets import attach_tab_popup_to_main
# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import socket
import threading
import tkinter as tk
import urllib.parse
import cv2
if not hasattr(cv2, '__version__'): cv2.__version__ = '4.10.0'
import pyautogui
from PIL import ImageTk
from core.i18n import get_lang
from core.ui_widgets import RoundedCard, apply_win11_round_corners, bind_child_window_to_parent

try:
    import qrcode
except Exception:
    qrcode = None


def _get_wifi_lan_ip() -> str:
    """Определяет реальный IP-адрес компьютера в локальной Wi-Fi сети (игнорируя виртуальные VPN-адаптеры)."""
    candidates = []
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip_addr = str(info[4][0])
            if ip_addr.startswith(("192.168.", "10.", "172.16.", "172.17.", "172.18.", "172.19.", "172.2", "172.3")):
                if not ip_addr.endswith(".1"):
                    candidates.append(ip_addr)
    except Exception:
        pass
    if candidates:
        for c in candidates:
            if c.startswith("192.168."):
                return c
        return candidates[0]
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = str(s.getsockname()[0])
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


MOBILE_REMOTE_HTML = """<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>AiPulsar Quantum Bridge</title>
<style>
body{background:#07090E;color:#fff;font-family:-apple-system,BlinkMacSystemFont,sans-serif;margin:0;padding:16px;text-align:center}
.card{background:#0D1117;border:1px solid #7C4DFF;border-radius:16px;padding:14px;margin-bottom:14px}
h2{margin:0 0 8px;font-size:18px;color:#64FFDA}
input,button{width:100%;box-sizing:border-box;border-radius:10px;border:none;padding:12px;font-size:16px;margin-top:8px}
input{background:#161B22;color:#fff;border:1px solid #30363D}
button{background:#7C4DFF;color:#fff;font-weight:600}
.pad{height:160px;background:#161B22;border:1px dashed #7C4DFF;border-radius:12px;display:flex;align-items:center;justify-content:center;color:#8B949E;touch-action:none;margin-top:8px;user-select:none}
.row{display:flex;gap:8px}.row button{flex:1;background:#21262D;font-size:14px}
#st{color:#64FFDA;font-size:13px;min-height:18px;margin-top:6px}
</style></head><body>
<div class="card"><h2>⚡ AiPulsar Quantum Bridge</h2><div id="st">Связь с ПК установлена по Wi-Fi</div>
<input id="cmd" placeholder="Введите команду для ПК..."><button onclick="sendCmd()">Выполнить на ПК</button></div>
<div class="card"><b>📁 Телепорт фото / файла на Рабочий стол ПК</b>
<input type="file" id="f" onchange="upFile()"><div id="fst" style="font-size:13px;color:#8B949E;margin-top:6px">Выберите фото из галереи или файл</div></div>
<div class="card"><b>🖱 Беспроводной тачпад ПК</b><div class="pad" id="pad">Водите пальцем здесь для движения мыши</div>
<div class="row"><button onclick="act('lclick')">Левый клик</button><button onclick="act('rclick')">Правый клик</button><button onclick="act('space')">Пауза / Play</button></div></div>
<script>
function sendCmd(){let v=document.getElementById('cmd').value;if(!v)return;fetch('/cmd',{method:'POST',body:JSON.stringify({text:v})});document.getElementById('cmd').value='';document.getElementById('st').innerText='Отправлено на ПК: '+v;}
function act(a){fetch('/act',{method:'POST',body:JSON.stringify({action:a})});}
function upFile(){let inp=document.getElementById('f');if(!inp.files||!inp.files.length)return;let file=inp.files[0];document.getElementById('fst').innerText='Телепортация '+file.name+'...';fetch('/upload?name='+encodeURIComponent(file.name),{method:'POST',body:file}).then(()=>{document.getElementById('fst').innerText='Готово! Файл на Рабочем столе ПК: '+file.name;});}
let lx=null,ly=null,pad=document.getElementById('pad');
pad.addEventListener('touchstart',e=>{if(e.touches&&e.touches.length){lx=e.touches[0].clientX;ly=e.touches[0].clientY;}});
pad.addEventListener('touchmove',e=>{e.preventDefault();if(!e.touches||!e.touches.length)return;let nx=e.touches[0].clientX,ny=e.touches[0].clientY;fetch('/move',{method:'POST',body:JSON.stringify({dx:(nx-lx)*2.4,dy:(ny-ly)*2.4})});lx=nx;ly=ny;},{passive:false});
</script></body></html>"""
class QuantumPhoneBridgeDialog:
    """Квантовый мост Телефон <-> ПК по QR-коду (PRO): пульт, тачпад и телепорт файлов без интернета и приложений."""

    ACCENT = "#7C4DFF"
    BG_ROOT = "#07090E"
    BG_CARD = "#0D1117"

    def __init__(self, root: tk.Widget, on_remote_cmd=None, on_notify=None):
        self.root = root
        self.on_remote_cmd = on_remote_cmd
        self.on_notify = on_notify
        self._win = None
        self._server = None
        self._port = 8765
        self._qr_photo = None

    def _ensure_server(self) -> str:
        ip = _get_wifi_lan_ip()
        if self._server is not None:
            return f"http://{ip}:{self._port}"

        outer_self = self

        class BridgeHandler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_GET(self):
                body = MOBILE_REMOTE_HTML.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                parsed = urllib.parse.urlparse(self.path)
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length) if length else b""

                if parsed.path == "/cmd":
                    data = json.loads(raw.decode("utf-8"))
                    txt = str(data.get("text", "")).strip()
                    if txt and outer_self.on_remote_cmd:
                        threading.Thread(target=outer_self.on_remote_cmd, args=(txt,), daemon=True).start()
                elif parsed.path == "/move":
                    data = json.loads(raw.decode("utf-8"))
                    pyautogui.moveRel(int(data.get("dx", 0)), int(data.get("dy", 0)), _pause=False)
                elif parsed.path == "/act":
                    data = json.loads(raw.decode("utf-8"))
                    act = data.get("action")
                    if act == "lclick":
                        pyautogui.click()
                    elif act == "rclick":
                        pyautogui.rightClick()
                    elif act == "space":
                        pyautogui.press("space")
                elif parsed.path == "/upload":
                    qs = urllib.parse.parse_qs(parsed.query)
                    raw_name = qs.get("name", ["Phone_File.bin"])[0]
                    fname = os.path.basename(raw_name) or "Phone_File.bin"
                    desk = os.path.join(os.path.expanduser("~"), "Desktop")
                    os.makedirs(desk, exist_ok=True)
                    dest = os.path.join(desk, f"Phone_{fname}")
                    with open(dest, "wb") as f:
                        f.write(raw)
                    if outer_self.on_notify:
                        outer_self.on_notify("AiPulsar", f"📱 Файл с телефона телепортирован на Рабочий стол: Phone_{fname}")

                self.send_response(200)
                self.send_header("Content-Length", "2")
                self.end_headers()
                self.wfile.write(b"OK")

        self._server = ThreadingHTTPServer(("0.0.0.0", self._port), BridgeHandler)
        threading.Thread(target=self._server.serve_forever, daemon=True).start()
        return f"http://{ip}:{self._port}"

    def show(self):
        if self._win and self._win.winfo_exists():
            self._win.lift()
            return

        url = self._ensure_server()
        is_en = get_lang() == "en"

        win = tk.Toplevel(self.root)

        attach_tab_popup_to_main(self.root if 'self.root'.strip() else None, win)
        win.title("Quantum Phone Bridge")
        win.configure(bg=self.BG_ROOT)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        self._win = win

        outer = RoundedCard(win, radius=18, border_color="#383838", bg_color=self.BG_CARD, pad=14, width=440, height=445)
        outer.pack(fill=tk.BOTH, expand=True)
        box = outer.inner

        hdr = tk.Frame(box, bg=self.BG_CARD)
        hdr.pack(fill=tk.X, pady=(0, 8))
        tk.Label(hdr, text="📱  КВАНТОВЫЙ МОСТ: ТЕЛЕФОН ↔ ПК" if not is_en else "📱  QUANTUM BRIDGE: PHONE ↔ PC", bg=self.BG_CARD, fg="#FFFFFF", font=("Segoe UI Semibold", 10)).pack(side=tk.LEFT)
        tk.Button(hdr, text="✕", command=win.destroy, bg=self.BG_CARD, fg="#FFFFFF", activebackground="#1F242D", relief=tk.FLAT, font=("Segoe UI Semibold", 10), padx=6, cursor="hand2").pack(side=tk.RIGHT)

        tk.Label(
            box,
            text="Наведите камеру телефона на QR-код (в одной Wi-Fi сети).\nТелефон станет тачпадом, пультом и телепортом файлов на ПК:"
            if not is_en
            else "Scan QR code with your phone camera on the same Wi-Fi\nto use touchpad, remote voice control & instant file teleport:",
            bg=self.BG_CARD, fg="#8B949E", font=("Segoe UI", 9), justify=tk.CENTER
        ).pack(pady=(0, 8))

        if qrcode is not None:
            qr = qrcode.QRCode(box_size=6, border=2)
            qr.add_data(url)
            qr.make(fit=True)
            pil_qr = qr.make_image(fill_color="#FFFFFF", back_color="#0D1117").convert("RGB").resize((220, 220))
            self._qr_photo = ImageTk.PhotoImage(pil_qr)
            tk.Label(box, image=self._qr_photo, bg=self.BG_CARD).pack(pady=4)

        tk.Label(box, text=url, bg="#161B22", fg="#64FFDA", font=("Consolas", 10, "bold"), padx=12, pady=4).pack(pady=(8, 4))
        tk.Label(box, text="Без установки приложений и без интернета" if not is_en else "No app install & no cloud required", bg=self.BG_CARD, fg="#8B949E", font=("Segoe UI", 8)).pack()

        win.update_idletasks()
        apply_win11_round_corners(win)

        def _calc_xy():
            rw = self.root.winfo_width() or 1260
            rh = self.root.winfo_height() or 740
            nx = self.root.winfo_rootx() + (rw - win.winfo_reqwidth()) // 2
            ny = self.root.winfo_rooty() + (rh - win.winfo_reqheight()) // 2
            return (max(20, nx), max(20, ny))

        ix, iy = _calc_xy()
        win.geometry(f"+{ix}+{iy}")
        bind_child_window_to_parent(self.root, win, _calc_xy)
        win.lift()
        win.focus_force()


