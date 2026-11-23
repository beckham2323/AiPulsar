# -*- coding: utf-8 -*-
import ctypes, json, os, threading, time, tkinter as tk, cv2
from PIL import Image, ImageTk

class PulsarVisionSystem:
    _EYES_ENABLED = False
    _VISION_WIN = None
    _WORKING_CAM_SPEC = None

    def __init__(self, models_dir: str = "models"):
        self.models_dir = models_dir
        self.faces_dir = os.path.join(models_dir, "faces_db")
        self.sec_dir = os.path.join(models_dir, "security_shots")
        os.makedirs(self.faces_dir, exist_ok=True)
        os.makedirs(self.sec_dir, exist_ok=True)
        self.meta_path = os.path.join(self.faces_dir, "faces_index.json")
        self.cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    @classmethod
    def set_eyes_enabled(cls, state: bool) -> str:
        cls._EYES_ENABLED = bool(state)
        return "🟢 Зрение включено." if cls._EYES_ENABLED else "🙈 Зрение выключено."

    @classmethod
    def auto_discover_camera(cls):
        backends = [("DirectShow", getattr(cv2, "CAP_DSHOW", 700)), ("MSMF", getattr(cv2, "CAP_MSMF", 1400)), ("Auto", 0)]
        specs = ([cls._WORKING_CAM_SPEC] if cls._WORKING_CAM_SPEC else []) + [(i, b, n) for i in range(6) for n, b in backends]
        for idx, b_code, b_name in specs:
            cap = None
            try:
                cap = cv2.VideoCapture(idx, b_code) if b_code else cv2.VideoCapture(idx)
                if cap and cap.isOpened():
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                    for _ in range(3):
                        ok, fr = cap.read()
                        if ok and fr is not None and fr.size > 0:
                            cls._WORKING_CAM_SPEC = (idx, b_code, b_name)
                            return cap, f"Камера #{idx} ({b_name})"
            except Exception:
                pass
            if cap:
                cap.release()
        return None, "Камера не найдена"

    def _extract_face_crop(self, frame):
        gray = cv2.equalizeHist(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
        faces = self.cascade.detectMultiScale(gray, 1.15, 5, minSize=(70, 70))
        if len(faces) == 0:
            return None, None
        x, y, w, h = sorted(faces, key=lambda r: r * r, reverse=True)
        return cv2.resize(gray[y:y + h, x:x + w], (128, 128)), (int(x), int(y), int(w), int(h))

    def toggle_guard_mode(self, enable: bool = True, ui_callback=None):
        return "🛡️ Охрана обновлена."

    def toggle_presence_autopause(self, enable: bool = True, ui_callback=None):
        return "👁️ Автопауза обновлена."

    def open_resizable_vision_window(self, parent_tk, on_state_changed=None):
        if self.__class__._VISION_WIN and self.__class__._VISION_WIN.winfo_exists():
            self.__class__._VISION_WIN.lift()
            return
        self.__class__.set_eyes_enabled(True)
        if on_state_changed:
            on_state_changed(True)

        win = tk.Toplevel(parent_tk)
        win.title("👁️ AiPulsar — Зрение включено")
        win.geometry("680x520")
        win.minsize(420, 320)
        win.configure(bg="#202020")
        win.resizable(True, True)
        self.__class__._VISION_WIN = win

        top = tk.Frame(win, bg="#2B2B2B", height=34)
        top.pack(fill=tk.X)
        lbl_st = tk.Label(top, text="⏳ Автопоиск камеры Windows...", bg="#2B2B2B", fg="#64FFDA", font=("Segoe UI Semibold", 9), padx=10, pady=5)
        lbl_st.pack(side=tk.LEFT)

        v_lbl = tk.Label(win, bg="#141414", text="⏳ Подключение к веб-камере...", fg="#A6A6A6", font=("Segoe UI", 11))
        v_lbl.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        bot = tk.Frame(win, bg="#202020")
        bot.pack(fill=tk.X, padx=10, pady=(0, 10))
        st = {"on": True, "cap": None, "info": ""}

        def _close_all():
            if not st["on"]:
                return
            st["on"] = False
            if st["cap"]:
                st["cap"].release()
            self.__class__.set_eyes_enabled(False)
            self.__class__._VISION_WIN = None
            if on_state_changed:
                on_state_changed(False)
            if win.winfo_exists():
                win.destroy()

        tk.Button(bot, text="⛔ Отключить зрение", command=_close_all, bg="#C42B1C", fg="#FFFFFF", relief=tk.FLAT, font=("Segoe UI Semibold", 10), padx=16, pady=6, cursor="hand2").pack(side=tk.RIGHT)
        win.protocol("WM_DELETE_WINDOW", _close_all)

        def _init_cam():
            c, inf = self.__class__.auto_discover_camera()
            if not st["on"] and c:
                c.release()
                return
            st["cap"], st["info"] = c, inf

        threading.Thread(target=_init_cam, daemon=True).start()

        def _tick():
            if not st["on"] or not win.winfo_exists():
                return
            cap = st["cap"]
            if cap and cap.isOpened():
                ok, fr = cap.read()
                if ok and fr is not None:
                    gray = cv2.equalizeHist(cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY))
                    faces = self.cascade.detectMultiScale(gray, 1.15, 5, minSize=(70, 70))
                    for (x, y, w, h) in faces:
                        cv2.rectangle(fr, (x, y), (x + w, y + h), (96, 205, 255), 2)
                    lbl_st.config(text=f"🟢 {st['info']} • Лиц в кадре: {len(faces)}")
                    tw, th = max(240, v_lbl.winfo_width() - 4), max(180, v_lbl.winfo_height() - 4)
                    im = ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)).resize((tw, th)))
                    v_lbl.imgtk = im
                    v_lbl.config(image=im, text="")
            elif st["info"] == "Камера не найдена":
                lbl_st.config(text="⚠️ Камера не найдена в Windows", fg="#FF6E6E")
                v_lbl.config(text="📷 Камера не обнаружена. Проверьте USB или шторку ноутбука.", image="")
            win.after(35, _tick)

        win.after(100, _tick)
