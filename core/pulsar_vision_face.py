# -*- coding: utf-8 -*-
import json
import os
import threading
import time
import cv2
import numpy as np


class PulsarVisionSystem:
    """Система компьютерного зрения AiPulsar: распознавание и запоминание лиц, охранник, QR-сканер."""

    def __init__(self, models_dir: str = "models"):
        self.models_dir = models_dir
        self.faces_dir = os.path.join(models_dir, "faces_db")
        self.sec_dir = os.path.join(models_dir, "security_shots")
        os.makedirs(self.faces_dir, exist_ok=True)
        os.makedirs(self.sec_dir, exist_ok=True)
        self.meta_path = os.path.join(self.faces_dir, "faces_index.json")
        self.cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self._guard_active = False

    def _load_index(self) -> dict:
        if os.path.exists(self.meta_path):
            try:
                with open(self.meta_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_index(self, data: dict):
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _grab_frame(self):
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            return None
        try:
            for _ in range(4):
                cap.read()
            ok, frame = cap.read()
            return frame if ok else None
        finally:
            cap.release()

    def _extract_face_crop(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        faces = self.cascade.detectMultiScale(gray, scaleFactor=1.15, minNeighbors=5, minSize=(70, 70))
        if len(faces) == 0:
            return None, None
        x, y, w, h = sorted(faces, key=lambda r: r[2] * r[3], reverse=True)[0]
        crop = cv2.resize(gray[y:y + h, x:x + w], (128, 128))
        return crop, (int(x), int(y), int(w), int(h))

    def remember_person(self, person_name: str = "Создатель") -> str:
        name = (person_name or "Создатель").strip().capitalize()
        frame = self._grab_frame()
        if frame is None:
            return "📷 Не удалось получить кадр с веб-камеры (проверьте, подключена ли камера)."

        crop, _ = self._extract_face_crop(frame)
        if crop is None:
            return "👤 Лицо в кадре не обнаружено. Посмотрите прямо в камеру при хорошем освещении и повторите команду."

        idx = self._load_index()
        safe_id = f"face_{int(time.time())}"
        img_path = os.path.join(self.faces_dir, f"{safe_id}.png")
        cv2.imwrite(img_path, crop)
        idx[safe_id] = {"name": name, "file": f"{safe_id}.png", "created": time.strftime("%Y-%m-%d %H:%M:%S")}
        self._save_index(idx)
        return f"✅ Я запомнил лицо: **{name}**! Теперь я буду узнавать этого человека перед камерой."

    def recognize_now(self) -> str:
        frame = self._grab_frame()
        if frame is None:
            return "📷 Камера недоступна или не подключена к ПК."

        # Проверяем, нет ли в кадре QR-кода
        qr_det = cv2.QRCodeDetector()
        qr_data, _, _ = qr_det.detectAndDecode(frame)
        qr_note = f"\n🔗 В кадре обнаружен QR-код: {qr_data}" if qr_data else ""

        crop, _ = self._extract_face_crop(frame)
        if crop is None:
            return f"👁️ Я смотрю в камеру, но сейчас перед монитором никого нет.{qr_note}"

        idx = self._load_index()
        if not idx:
            return f"👤 Я вижу человека перед камерой, но моя база лиц пока пуста. Скажите: «запомни моё лицо».{qr_note}"

        best_name = None
        best_score = -1.0
        hist_cur = cv2.calcHist([crop], [0], None, [64], [0, 256])
        cv2.normalize(hist_cur, hist_cur)

        for item in idx.values():
            fp = os.path.join(self.faces_dir, item.get("file", ""))
            if not os.path.exists(fp):
                continue
            ref = cv2.imread(fp, cv2.IMREAD_GRAYSCALE)
            if ref is None:
                continue
            hist_ref = cv2.calcHist([ref], [0], None, [64], [0, 256])
            cv2.normalize(hist_ref, hist_ref)
            corr = float(cv2.compareHist(hist_cur, hist_ref, cv2.HISTCMP_CORREL))
            res_tm = float(cv2.matchTemplate(crop, ref, cv2.TM_CCOEFF_NORMED)[0][0])
            score = 0.55 * corr + 0.45 * res_tm
            if score > best_score:
                best_score = score
                best_name = item.get("name", "Знакомый")

        if best_name and best_score >= 0.48:
            conf = min(99, int(best_score * 100))
            return f"👁️ Я узнал вас! Перед камерой: **{best_name}** (совпадение {conf}%).{qr_note}"
        return f"🚨 Перед камерой **незнакомый человек** (не найден в моей базе лиц).{qr_note}"

    def toggle_guard_mode(self, enable: bool = True, ui_callback=None) -> str:
        if not enable:
            self._guard_active = False
            return "🛡️ Режим визуальной охраны выключен."
        if self._guard_active:
            return "🛡️ Режим визуальной охраны уже активен."
        self._guard_active = True

        def _guard_loop():
            while self._guard_active:
                try:
                    frame = self._grab_frame()
                    if frame is not None:
                        crop, _ = self._extract_face_crop(frame)
                        if crop is not None:
                            res = self.recognize_now()
                            if "незнакомый человек" in res.lower():
                                shot = os.path.join(self.sec_dir, f"intruder_{time.strftime('%Y%m%d_%H%M%S')}.jpg")
                                cv2.imwrite(shot, frame)
                                if ui_callback:
                                    ui_callback(f"🚨 ОХРАНА: Обнаружен посторонний у ПК! Снимок сохранён: {shot}")
                except Exception:
                    pass
                time.sleep(4.0)

        threading.Thread(target=_guard_loop, daemon=True).start()
        return "🛡️ Режим визуальной охраны включён! Если к ПК подойдёт незнакомец, я сохраню его фото и предупрежу вас."


    def read_document_from_camera(self) -> str:
        """Делает снимок с камеры и считывает текст с листа, чека или книги через RapidOCR."""
        frame = self._grab_frame()
        if frame is None:
            return "📷 Камера недоступна или не подключена к ПК."
        tmp_img = os.path.join(self.sec_dir, "cam_ocr_last.jpg")
        cv2.imwrite(tmp_img, frame)
        try:
            from rapidocr_onnxruntime import RapidOCR
            ocr = RapidOCR()
            res, _ = ocr(tmp_img)
            if not res:
                return "📄 Я посмотрел в камеру, но чёткого печатного текста в кадре не увидел. Поднесите лист ближе и ровнее."
            lines = [item for item in res if len(item) > 1 and str(item).strip()]
            joined = "\n".join(lines)
            return f"📄 Вот что я прочитал с камеры:\n\n{joined}"
        except Exception as e:
            return f"⚠️ Не удалось распознать текст с камеры: {e}"

    def toggle_presence_autopause(self, enable: bool = True, ui_callback=None) -> str:
        """Автоматически ставит медиа на паузу, когда пользователь отходит от ПК."""
        if not enable:
            self._presence_active = False
            return "⏸️ Режим автопаузы при уходе от экрана выключен."
        if getattr(self, "_presence_active", False):
            return "👁️ Режим контроля присутствия уже активен."
        self._presence_active = True

        def _presence_loop():
            import ctypes
            absent_ticks = 0
            paused_by_me = False
            while getattr(self, "_presence_active", False):
                try:
                    frame = self._grab_frame()
                    if frame is not None:
                        crop, _ = self._extract_face_crop(frame)
                        if crop is None:
                            absent_ticks += 1
                            if absent_ticks >= 4 and not paused_by_me:
                                # Нажимаем системную клавишу Media Play/Pause (VK_MEDIA_PLAY_PAUSE = 0xB3)
                                ctypes.windll.user32.keybd_event(0xB3, 0, 0, 0)
                                ctypes.windll.user32.keybd_event(0xB3, 0, 2, 0)
                                paused_by_me = True
                                if ui_callback:
                                    ui_callback("⏸️ Вы отошли от монитора — я поставил воспроизведение на паузу.")
                        else:
                            if paused_by_me:
                                ctypes.windll.user32.keybd_event(0xB3, 0, 0, 0)
                                ctypes.windll.user32.keybd_event(0xB3, 0, 2, 0)
                                paused_by_me = False
                                if ui_callback:
                                    ui_callback("▶️ С возвращением! Воспроизведение продолжено.")
                            absent_ticks = 0
                except Exception:
                    pass
                time.sleep(3.5)

        threading.Thread(target=_presence_loop, daemon=True).start()
        return "👁️ Контроль присутствия включён! Если вы отойдёте от монитора, я поставлю видео/музыку на паузу, а когда вернётесь — продолжу."
