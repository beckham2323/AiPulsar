from core.ui_widgets import attach_tab_popup_to_main
# -*- coding: utf-8 -*-
import datetime
import json
import os
import shutil
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional

try:
    import cv2
    import numpy as np
except Exception:
    cv2 = None
    np = None


def _get_vault_dir() -> str:
    """Постоянное хранилище памяти в %APPDATA%\\AiPulsar_SoulVault (переживает переустановку программы)."""
    appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
    vdir = os.path.join(appdata, "AiPulsar_SoulVault")
    os.makedirs(vdir, exist_ok=True)
    return vdir


def _get_app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class SelfHealingAndMemoryEngine:
    """Самовосстановление AiPulsar без переустановки + несгораемая память о владельце и распознавание по фото."""

    def __init__(self):
        self.app_dir = _get_app_dir()
        self.vault_dir = _get_vault_dir()
        self.vault_mem_path = os.path.join(self.vault_dir, "soul_memory.json")
        self.local_mem_path = os.path.join(self.app_dir, "models", "soul_memory.json")
        self.owner_photo_path = os.path.join(self.vault_dir, "owner_face.jpg")
        self.owner_sig_path = os.path.join(self.vault_dir, "owner_face_sig.json")

    def run_self_heal(self) -> list:
        """Автоматически проверяет и чинит конфиги, папки и память без переустановки."""
        actions = []
        models_dir = os.path.join(self.app_dir, "models")
        os.makedirs(models_dir, exist_ok=True)

        # 1. Проверка и автолечение JSON-конфигов
        defaults = {
            os.path.join(models_dir, "cloud_config.json"): {"mode": "auto"},
            os.path.join(models_dir, "audio_prefs.json"): {"voice": "ru-RU-DmitryNeural", "mic_name": "", "spk_name": ""},
        }
        for cfg_p, def_data in defaults.items():
            need_fix = False
            if not os.path.exists(cfg_p):
                need_fix = True
            else:
                try:
                    with open(cfg_p, "r", encoding="utf-8") as f:
                        json.load(f)
                except Exception:
                    need_fix = True
            if need_fix:
                with open(cfg_p, "w", encoding="utf-8") as f:
                    json.dump(def_data, f, ensure_ascii=False, indent=2)
                actions.append(f"Восстановлен повреждённый конфиг: {os.path.basename(cfg_p)}")

        # 2. Восстановление иконок из _internal при случайном удалении
        internal_dir = os.path.join(self.app_dir, "_internal")
        for res_name in ("aipulsar.ico", "aipulsar_icon.png"):
            dst = os.path.join(self.app_dir, res_name)
            src = os.path.join(internal_dir, res_name)
            if not os.path.exists(dst) and os.path.exists(src):
                shutil.copy2(src, dst)
                actions.append(f"Восстановлен системный ресурс: {res_name}")

        # 3. Синхронизация несгораемой памяти после переустановки
        if os.path.exists(self.vault_mem_path) and not os.path.exists(self.local_mem_path):
            shutil.copy2(self.vault_mem_path, self.local_mem_path)
            actions.append("Память о владельце автоматически восстановлена из защищённого хранилища!")
        elif os.path.exists(self.local_mem_path) and not os.path.exists(self.vault_mem_path):
            shutil.copy2(self.local_mem_path, self.vault_mem_path)

        return actions

    def load_memory(self) -> dict:
        for p in (self.vault_mem_path, self.local_mem_path):
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    continue
        return {
            "owner_name": "",
            "preferred_address": "",
            "about_owner": "",
            "notes": [],
            "face_enrolled": False,
            "updated_at": "",
        }

    def save_memory(self, data: dict):
        data["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        os.makedirs(os.path.dirname(self.local_mem_path), exist_ok=True)
        for p in (self.vault_mem_path, self.local_mem_path):
            with open(p, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def remember_fact(self, fact_text: str):
        mem = self.load_memory()
        notes = list(mem.get("notes") or [])
        clean = (fact_text or "").strip()
        if clean and clean not in notes:
            notes.append(clean)
            mem["notes"] = notes[-100:]
            self.save_memory(mem)
    def _extract_face_histogram(self, image_path: str):
        if cv2 is None or np is None or not os.path.exists(image_path):
            return None
        # Читаем файл через numpy.fromfile для поддержки русских путей Windows
        img_bytes = np.fromfile(image_path, dtype=np.uint8)
        img = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)
        if img is None:
            return None
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        cascade_path = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
        face_cascade = cv2.CascadeClassifier(cascade_path)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(40, 40))
        if len(faces) > 0:
            x, y, w, h = max(faces, key=lambda r: r[2] * r[3])
            roi = gray[y : y + h, x : x + w]
        else:
            roi = gray
        roi_resized = cv2.resize(roi, (128, 128))
        hist = cv2.calcHist([roi_resized], [0], None, [64], [0, 256])
        cv2.normalize(hist, hist)
        return hist.flatten().tolist()

    def enroll_owner_photo(self, photo_path: str) -> tuple:
        hist = self._extract_face_histogram(photo_path)
        if hist is None:
            return False, "Не удалось прочитать изображение. Выберите файл JPG или PNG."
        shutil.copy2(photo_path, self.owner_photo_path)
        with open(self.owner_sig_path, "w", encoding="utf-8") as f:
            json.dump({"hist": hist}, f)
        mem = self.load_memory()
        mem["face_enrolled"] = True
        self.save_memory(mem)
        return True, "Лицо владельца успешно запомнено и сохранено в защищённую память AiPulsar!"

    def recognize_person_from_photo(self, test_photo_path: str) -> tuple:
        if not os.path.exists(self.owner_sig_path) or cv2 is None or np is None:
            return False, 0.0, "Эталонное фото владельца ещё не загружено."
        test_hist = self._extract_face_histogram(test_photo_path)
        if test_hist is None:
            return False, 0.0, "Не удалось распознать изображение."
        with open(self.owner_sig_path, "r", encoding="utf-8") as f:
            ref_hist = json.load(f).get("hist", [])
        if not ref_hist:
            return False, 0.0, "Эталонный вектор пуст."
        h1 = np.array(ref_hist, dtype=np.float32)
        h2 = np.array(test_hist, dtype=np.float32)
        score = float(cv2.compareHist(h1, h2, cv2.HISTCMP_CORREL))
        mem = self.load_memory()
        owner = mem.get("preferred_address") or mem.get("owner_name") or "Владелец"
        if score >= 0.68:
            return True, score, f"Распознан владелец: {owner} (совпадение {score * 100:.0f}%)"
        return False, score, f"Незнакомый человек на фото (совпадение с {owner}: {max(0.0, score) * 100:.0f}%)"

    def open_acquaintance_dialog(self, parent: Optional[tk.Misc] = None):
        mem = self.load_memory()
        win = tk.Toplevel(parent) if parent else tk.Tk()
        win.title("👤 AiPulsar — Профиль, Память и Распознавание лица")
        win.geometry("500x430")
        win.resizable(False, False)
        win.configure(bg="#1E1E1E")

        tk.Label(win, text="👤 Профиль и несгораемая память AiPulsar", bg="#1E1E1E", fg="#00AFF0", font=("Segoe UI Semibold", 12)).pack(anchor="w", padx=20, pady=(16, 4))
        tk.Label(win, text="Эта память хранится в защищённом профиле Windows и сохраняется даже после переустановки.", bg="#1E1E1E", fg="#A8A8A8", wraplength=460, justify="left", font=("Segoe UI", 8)).pack(anchor="w", padx=20, pady=(0, 12))

        tk.Label(win, text="Ваше имя:", bg="#1E1E1E", fg="#E0E0E0", font=("Segoe UI", 9)).pack(anchor="w", padx=20)
        name_var = tk.StringVar(value=mem.get("owner_name", ""))
        tk.Entry(win, textvariable=name_var, bg="#2B2B2B", fg="#FFFFFF", insertbackground="#FFFFFF", relief=tk.FLAT, font=("Segoe UI", 9)).pack(fill=tk.X, padx=20, pady=(2, 8), ipady=4)

        tk.Label(win, text="Как к вам обращаться (например: Виктор, Шеф, Друг):", bg="#1E1E1E", fg="#E0E0E0", font=("Segoe UI", 9)).pack(anchor="w", padx=20)
        addr_var = tk.StringVar(value=mem.get("preferred_address", ""))
        tk.Entry(win, textvariable=addr_var, bg="#2B2B2B", fg="#FFFFFF", insertbackground="#FFFFFF", relief=tk.FLAT, font=("Segoe UI", 9)).pack(fill=tk.X, padx=20, pady=(2, 8), ipady=4)

        tk.Label(win, text="Что мне важно помнить о вас и ваших задачах:", bg="#1E1E1E", fg="#E0E0E0", font=("Segoe UI", 9)).pack(anchor="w", padx=20)
        about_var = tk.StringVar(value=mem.get("about_owner", ""))
        tk.Entry(win, textvariable=about_var, bg="#2B2B2B", fg="#FFFFFF", insertbackground="#FFFFFF", relief=tk.FLAT, font=("Segoe UI", 9)).pack(fill=tk.X, padx=20, pady=(2, 12), ipady=4)

        face_status = "✅ Фото владельца загружено и активно" if mem.get("face_enrolled") else "⚪ Фото владельца ещё не загружено"
        face_lbl = tk.Label(win, text=face_status, bg="#1E1E1E", fg="#8BE9FD", font=("Segoe UI Semibold", 9))
        face_lbl.pack(anchor="w", padx=20, pady=(0, 8))

        photo_row = tk.Frame(win, bg="#1E1E1E")
        photo_row.pack(fill=tk.X, padx=20, pady=(0, 14))

        def _upload_owner_photo():
            fp = filedialog.askopenfilename(title="Выберите ваше фото (JPG/PNG)", filetypes=[("Изображения", "*.jpg;*.jpeg;*.png")], parent=win)
            if fp:
                ok, msg = self.enroll_owner_photo(fp)
                if ok:
                    face_lbl.config(text="✅ Фото владельца загружено и активно")
                messagebox.showinfo("Распознавание лица AiPulsar", msg, parent=win)

        def _test_recognize_photo():
            fp = filedialog.askopenfilename(title="Выберите фото для проверки распознавания", filetypes=[("Изображения", "*.jpg;*.jpeg;*.png")], parent=win)
            if fp:
                ok, _sc, msg = self.recognize_person_from_photo(fp)
                messagebox.showinfo("Результат распознавания", msg, parent=win)

        tk.Button(photo_row, text="📷 Загрузить моё фото (Запомнить лицо)", command=_upload_owner_photo, bg="#2B2B2B", fg="#FFFFFF", relief=tk.FLAT, font=("Segoe UI", 8), padx=10, pady=5, cursor="hand2").pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(photo_row, text="🔍 Проверить лицо по фото", command=_test_recognize_photo, bg="#2B2B2B", fg="#8BE9FD", relief=tk.FLAT, font=("Segoe UI", 8), padx=10, pady=5, cursor="hand2").pack(side=tk.LEFT)

        def _save_all():
            cur = self.load_memory()
            cur["owner_name"] = name_var.get().strip()
            cur["preferred_address"] = addr_var.get().strip() or name_var.get().strip()
            cur["about_owner"] = about_var.get().strip()
            self.save_memory(cur)
            healed = self.run_self_heal()
            extra = ("\n\nАвтовосстановление выполнило:\n• " + "\n• ".join(healed)) if healed else ""
            messagebox.showinfo("Память сохранена", f"Приятно познакомиться, {cur['preferred_address'] or 'Друг'}! Я всё запомнил в постоянную память.{extra}", parent=win)
            win.destroy()

        tk.Button(win, text="Сохранить", command=_save_all, bg="#0078D4", fg="#FFFFFF", activebackground="#106EBE", relief=tk.FLAT, font=("Segoe UI Semibold", 9), pady=7, cursor="hand2").pack(fill=tk.X, padx=20)

        if parent:
            attach_tab_popup_to_main(parent, win)
        win.lift()
        win.focus_force()
