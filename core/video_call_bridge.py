from core.ui_widgets import attach_tab_popup_to_main
# -*- coding: utf-8 -*-
import os
import random
import string
import tempfile
import tkinter as tk
import webbrowser
from typing import Optional


def _generate_room_code() -> str:
    part1 = "".join(random.choices(string.digits, k=4))
    part2 = "".join(random.choices(string.ascii_uppercase, k=3))
    return f"AIPULSAR-{part1}-{part2}"


def _build_skype_webrtc_html(room_id: str, user_name: str, is_host: bool) -> str:
    safe_room = "".join(ch for ch in room_id if ch.isalnum() or ch in "-_")
    safe_name = user_name.replace('"', "").replace("<", "").replace(">", "")
    role_flag = "true" if is_host else "false"
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<title>AiPulsar Video — Комната {safe_room}</title>
<script src="https://unpkg.com"></script>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', sans-serif; }}
  body {{ background: #14171A; color: #FFFFFF; height: 100vh; display: flex; flex-direction: column; overflow: hidden; }}
  .topbar {{ height: 48px; background: #1C2024; border-bottom: 1px solid #2C3238; display: flex; align-items: center; justify-content: space-between; padding: 0 20px; }}
  .brand {{ font-weight: 600; font-size: 15px; color: #00AFF0; display: flex; align-items: center; gap: 10px; }}
  .room-badge {{ background: #262C33; border: 1px solid #38414A; padding: 4px 12px; border-radius: 14px; font-size: 13px; color: #E1E8ED; cursor: pointer; }}
  .room-badge:hover {{ background: #313840; }}
  .main {{ flex: 1; display: flex; overflow: hidden; }}
  .stage {{ flex: 1; position: relative; background: #0E1012; display: flex; align-items: center; justify-content: center; }}
  #remoteVideo {{ width: 100%; height: 100%; object-fit: contain; background: #0E1012; }}
  #localVideo {{ position: absolute; right: 20px; bottom: 20px; width: 240px; height: 150px; object-fit: cover; border-radius: 12px; border: 2px solid #00AFF0; background: #1E2328; box-shadow: 0 8px 24px rgba(0,0,0,0.6); }}
  .status-overlay {{ position: absolute; top: 20px; left: 20px; background: rgba(20,23,26,0.82); padding: 8px 14px; border-radius: 8px; font-size: 13px; color: #8BE9FD; border: 1px solid #2C3238; }}
  .chat-panel {{ width: 310px; background: #1A1E22; border-left: 1px solid #2C3238; display: flex; flex-direction: column; }}
  .chat-hdr {{ padding: 12px 16px; font-weight: 600; font-size: 13px; border-bottom: 1px solid #2C3238; color: #CBD5E1; }}
  .chat-msgs {{ flex: 1; padding: 12px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; font-size: 13px; }}
  .msg {{ background: #252B31; padding: 8px 12px; border-radius: 10px; max-width: 90%; line-height: 1.4; }}
  .msg.me {{ align-self: flex-end; background: #0078D4; color: #FFFFFF; }}
  .chat-input-row {{ padding: 10px; border-top: 1px solid #2C3238; display: flex; gap: 6px; }}
  .chat-input-row input {{ flex: 1; background: #252B31; border: 1px solid #38414A; border-radius: 8px; padding: 8px 10px; color: #FFF; outline: none; font-size: 13px; }}
  .chat-input-row button {{ background: #0078D4; border: none; border-radius: 8px; color: #FFF; padding: 0 14px; cursor: pointer; font-weight: 600; }}
  .controls {{ height: 74px; background: #1C2024; border-top: 1px solid #2C3238; display: flex; align-items: center; justify-content: center; gap: 18px; }}
  .ctl-btn {{ width: 48px; height: 48px; border-radius: 50%; border: none; background: #2C3238; color: #FFF; font-size: 19px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: 0.15s; }}
  .ctl-btn:hover {{ background: #3B434B; }}
  .ctl-btn.off {{ background: #D83B01; }}
  .ctl-btn.hangup {{ background: #E81123; width: 62px; border-radius: 24px; }}
  .ctl-btn.hangup:hover {{ background: #C50F1F; }}
</style>
</head>
<body>
  <div class="topbar">
    <div class="brand">📹 AiPulsar Video Call — Связь между городами (P2P WebRTC)</div>
    <div class="room-badge" onclick="copyRoom()" title="Нажмите, чтобы скопировать код комнаты">Комната: <b>{safe_room}</b> 📋</div>
  </div>
  <div class="main">
    <div class="stage">
      <div class="status-overlay" id="statusBox">Инициализация камеры и микрофона...</div>
      <video id="remoteVideo" autoplay playsinline></video>
      <video id="localVideo" autoplay muted playsinline></video>
    </div>
    <div class="chat-panel">
      <div class="chat-hdr">💬 Чат во время звонка</div>
      <div class="chat-msgs" id="chatMsgs"></div>
      <div class="chat-input-row">
        <input id="chatInp" type="text" placeholder="Написать сообщение..." onkeydown="if(event.key==='Enter')sendMsg()">
        <button onclick="sendMsg()">➤</button>
      </div>
    </div>
  </div>
  <div class="controls">
    <button class="ctl-btn" id="btnMic" onclick="toggleMic()" title="Микрофон вкл/выкл">🎤</button>
    <button class="ctl-btn" id="btnCam" onclick="toggleCam()" title="Камера вкл/выкл">📷</button>
    <button class="ctl-btn hangup" onclick="hangUp()" title="Завершить звонок">📞</button>
  </div>
<script>
const ROOM_ID = "{safe_room}";
const USER_NAME = "{safe_name}";
const IS_HOST = {role_flag};
let localStream = null;
let dataConn = null;
let activeCall = null;

function setStatus(txt) {{ document.getElementById('statusBox').innerText = txt; }}
function copyRoom() {{ navigator.clipboard.writeText(ROOM_ID); setStatus("Код комнаты скопирован: " + ROOM_ID); }}
function addMsg(sender, text, isMe) {{
  const box = document.getElementById('chatMsgs');
  const d = document.createElement('div');
  d.className = 'msg' + (isMe ? ' me' : '');
  d.innerHTML = '<b>' + sender + ':</b> ' + text;
  box.appendChild(d);
  box.scrollTop = box.scrollHeight;
}}

function sendMsg() {{
  const inp = document.getElementById('chatInp');
  const t = inp.value.trim();
  if (!t) return;
  addMsg(USER_NAME, t, true);
  if (dataConn && dataConn.open) dataConn.send({{ sender: USER_NAME, text: t }});
  inp.value = '';
}}

function toggleMic() {{
  if (!localStream) return;
  const track = next_item(localStream.getAudioTracks());
  if (track) {{
    track.enabled = !track.enabled;
    document.getElementById('btnMic').classList.toggle('off', !track.enabled);
  }}
}}

function toggleCam() {{
  if (!localStream) return;
  const track = next_item(localStream.getVideoTracks());
  if (track) {{
    track.enabled = !track.enabled;
    document.getElementById('btnCam').classList.toggle('off', !track.enabled);
  }}
}}

function next_item(arr) {{ return arr && arr.length > 0 ? arr.at(0) : null; }}

function hangUp() {{
  if (activeCall) activeCall.close();
  if (localStream) localStream.getTracks().forEach(t => t.stop());
  setStatus("Звонок завершён. Вы можете закрыть это окно.");
}}

async function startCall() {{
  try {{
    localStream = await navigator.mediaDevices.getUserMedia({{ video: true, audio: true }});
    document.getElementById('localVideo').srcObject = localStream;
  }} catch (e1) {{
    try {{
      localStream = await navigator.mediaDevices.getUserMedia({{ video: false, audio: true }});
      setStatus("🎙️ Камера не найдена — подключён голосовой режим по микрофону");
    }} catch (e2) {{
      const actx = new (window.AudioContext || window.webkitAudioContext)();
      const dest = actx.createMediaStreamDestination();
      localStream = dest.stream;
      setStatus("💬 Режим текстового чата и приёма звонка (микрофон не обнаружен)");
    }}
  }}

  const peerId = IS_HOST ? (ROOM_ID + "-HOST") : (ROOM_ID + "-GUEST-" + Math.floor(Math.random()*9000+1000));
  const peer = new Peer(peerId, {{
    config: {{ iceServers: [{{ urls: 'stun:://google.com' }}, {{ urls: 'stun:://google.com' }}] }}
  }});

  peer.on('open', (id) => {{
    if (IS_HOST) {{
      setStatus("Ожидание собеседника... Передайте ему код: " + ROOM_ID);
    }} else {{
      setStatus("Подключение к собеседнику в комнате " + ROOM_ID + "...");
      const hostId = ROOM_ID + "-HOST";
      dataConn = peer.connect(hostId);
      dataConn.on('data', (d) => addMsg(d.sender, d.text, false));
      const call = peer.call(hostId, localStream);
      activeCall = call;
      call.on('stream', (remoteStream) => {{
        document.getElementById('remoteVideo').srcObject = remoteStream;
        setStatus("На связи • Защищённый видеозвонок AiPulsar");
      }});
    }}
  }});

  peer.on('connection', (conn) => {{
    dataConn = conn;
    conn.on('data', (d) => addMsg(d.sender, d.text, false));
  }});

  peer.on('call', (call) => {{
    activeCall = call;
    call.answer(localStream);
    call.on('stream', (remoteStream) => {{
      document.getElementById('remoteVideo').srcObject = remoteStream;
      setStatus("На связи • Защищённый видеозвонок AiPulsar");
    }});
  }});

  peer.on('error', (e) => setStatus("Статус сети: " + e.type));
}}

startCall();
</script>
</body>
</html>"""


class VideoCallLauncherDialog:
    """Окно запуска видеозвонка между городами (создание комнаты или вход по коду с открытием интерфейса Skype)."""

    def __init__(self, parent: Optional[tk.Misc] = None):
        self.parent = parent

    def show(self):
        win = tk.Toplevel(self.parent) if self.parent else tk.Tk()
        win.title("AiPulsar — Видеозвонок между городами")
        win.geometry("460x290")
        win.resizable(False, False)
        win.configure(bg="#1E1E1E")

        tk.Label(win, text="📹 Видеосвязь AiPulsar (Между городами)", bg="#1E1E1E", fg="#00AFF0", font=("Segoe UI Semibold", 12)).pack(anchor="w", padx=20, pady=(16, 4))
        tk.Label(win, text="Прямой шифрованный видеозвонок, звук и чат (P2P WebRTC).\nРаботает через интернет без настройки роутера.", bg="#1E1E1E", fg="#BDBDBD", justify="left", font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=(0, 12))

        tk.Label(win, text="Ваше имя в звонке:", bg="#1E1E1E", fg="#E0E0E0", font=("Segoe UI", 9)).pack(anchor="w", padx=20)
        name_var = tk.StringVar(value=os.environ.get("USERNAME", "Пользователь AiPulsar"))
        tk.Entry(win, textvariable=name_var, bg="#2B2B2B", fg="#FFFFFF", insertbackground="#FFFFFF", relief=tk.FLAT, font=("Segoe UI", 9)).pack(fill=tk.X, padx=20, pady=(3, 10), ipady=4)

        tk.Label(win, text="Код комнаты (создайте новый или вставьте код собеседника):", bg="#1E1E1E", fg="#E0E0E0", font=("Segoe UI", 9)).pack(anchor="w", padx=20)
        room_row = tk.Frame(win, bg="#1E1E1E")
        room_row.pack(fill=tk.X, padx=20, pady=(3, 14))
        room_var = tk.StringVar(value=_generate_room_code())
        tk.Entry(room_row, textvariable=room_var, bg="#2B2B2B", fg="#8BE9FD", insertbackground="#FFFFFF", relief=tk.FLAT, font=("Segoe UI Semibold", 10)).pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4, padx=(0, 8))
        tk.Button(room_row, text="Новый код", command=lambda: room_var.set(_generate_room_code()), bg="#333333", fg="#FFFFFF", relief=tk.FLAT, font=("Segoe UI", 9), padx=10, pady=4, cursor="hand2").pack(side=tk.RIGHT)

        def _launch(is_host: bool):
            r_code = room_var.get().strip() or _generate_room_code()
            u_name = name_var.get().strip() or "Пользователь"
            html_content = _build_skype_webrtc_html(r_code, u_name, is_host)
            out_html = os.path.join(tempfile.gettempdir(), f"aipulsar_call_{r_code}.html")
            with open(out_html, "w", encoding="utf-8") as f:
                f.write(html_content)
            webbrowser.open(f"file:///{out_html.replace(os.sep, '/')}")
            win.destroy()

        btn_row = tk.Frame(win, bg="#1E1E1E")
        btn_row.pack(fill=tk.X, padx=20)
        tk.Button(btn_row, text="📞 Создать звонок (Я организатор)", command=lambda: _launch(True), bg="#0078D4", fg="#FFFFFF", activebackground="#106EBE", relief=tk.FLAT, font=("Segoe UI Semibold", 9), pady=7, cursor="hand2").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        tk.Button(btn_row, text="🔗 Войти по коду собеседника", command=lambda: _launch(False), bg="#2B2B2B", fg="#FFFFFF", activebackground="#3A3A3A", relief=tk.FLAT, font=("Segoe UI Semibold", 9), pady=7, cursor="hand2").pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(6, 0))

        if self.parent:
            attach_tab_popup_to_main(self.parent, win)
        win.lift()
        win.focus_force()
