import sys
if "--daemon-helper-tester" in sys.argv:
    from core.background_evolution_daemon import run_daemon_forever
    run_daemon_forever("models")
    sys.exit(0)
try:
    from core.background_evolution_daemon import ensure_background_daemon_started
    ensure_background_daemon_started("models")
except Exception:
    pass

# -*- coding: utf-8 -*-
import os as _os, sys as _sys
_exe_dir = _os.path.dirname(_os.path.abspath(_sys.executable)) if getattr(_sys, "frozen", False) else _os.path.dirname(_os.path.abspath(__file__))
for _cand in (_exe_dir, _os.path.join(_exe_dir, "_internal"), getattr(_sys, "_MEIPASS", "")):
    if _cand and _os.path.isdir(_cand) and _cand not in _sys.path:
        _sys.path.insert(0, _cand)

from core.companion_architect_spawner import CompanionArchitectManager
from core.autonomous_mod_system import AutonomousModSplitEngine
from core.autonomous_mod_system import AutonomousModSplitEngine
import sys as _sys_fix
if getattr(_sys_fix, 'frozen', False) and hasattr(_sys_fix, '_MEIPASS') and _sys_fix._MEIPASS not in _sys_fix.path:
    _sys_fix.path.insert(0, _sys_fix._MEIPASS)
from core.self_healing_identity import SelfHealingAndMemoryEngine
from core.game_cinema_mode import GameCinemaModeManager
import os as _diag_os, sys as _diag_sys, traceback as _diag_tb, datetime as _diag_dt
def _write_startup_diag(msg_txt):
    try:
        base_d = _diag_os.path.dirname(_diag_sys.executable) if getattr(_diag_sys, "frozen", False) else _diag_os.getcwd()
        log_p = _diag_os.path.join(base_d, "startup_diag.txt")
        with open(log_p, "a", encoding="utf-8") as _f:
            _f.write(f"[{_diag_dt.datetime.now()}] {msg_txt}\n")
    except Exception:
        pass
_diag_sys.excepthook = lambda exc_t, exc_v, exc_tb: _write_startup_diag("".join(_diag_tb.format_exception(exc_t, exc_v, exc_tb)))
_write_startup_diag("PROCESS STARTED (PID=" + str(_diag_os.getpid()) + ")")
from core.pc_symbiosis import PulsarPCSymbiosis, ensure_admin_and_privileges
from core.auto_routines import PulsarAutoRoutinesEngine
from core.anti_tamper import verify_and_protect_runtime
from core.auto_evolution import PulsarAutoEvolutionEngine
from core.super_pro_tools import PulsarSuperProTools
from core.unique_features import PulsarSecurityRadar, PulsarCryptoVault
from core.quantum_bridge import QuantumPhoneBridgeDialog
from core.pc_doctor import PulsarSystemDoctorAndClipboard
from core.app_guard import ensure_single_instance
# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru

import os
import re
import sys
import threading
import traceback

if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")


def _get_models_dir() -> str:
    exe_path = next(iter(sys.argv), __file__)
    base = os.path.dirname(os.path.abspath(exe_path)) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
    m_dir = os.path.join(base, "models")
    os.makedirs(m_dir, exist_ok=True)
    return m_dir


def _install_crash_shield(models_dir: str):
    log_path = os.path.join(models_dir, "aipulsar_crash.log")

    def _log_exc(exc_type, exc_value, exc_tb):
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write("\n--- CRASH SHIELD ---\n")
                traceback.print_exception(exc_type, exc_value, exc_tb, file=f)
        except Exception:
            pass

    sys.excepthook = _log_exc
    if hasattr(threading, "excepthook"):
        threading.excepthook = lambda args: _log_exc(args.exc_type, args.exc_value, args.exc_traceback)


import sys
try:
    import cv2
    if not hasattr(cv2, "__version__"):
        cv2.__version__ = "4.10.0"
except Exception:
    pass
from core.auto_updater import PulsarAutoUpdater
from core.brain_engine import BrainEngine
from core.doc_and_video import PulsarDocAndVideoTools
from core.ears import VoiceEars
from core.hands import HandsExecutor
from core.license_manager import AiPulsarLicenseManager
from core.local_rag import PulsarLocalKnowledgeBase
from core.macros_manager import PulsarMacrosManager
from core.memory_store import AgentMemory
import os as _os_p, sys as _sys_p, core as _core_pkg
if getattr(_sys_p, 'frozen', False) and hasattr(_sys_p, '_MEIPASS'):
    _cdir = _os_p.path.join(_sys_p._MEIPASS, 'core')
    if _cdir not in _core_pkg.__path__:
        _core_pkg.__path__.append(_cdir)

_write_startup_diag('IMP_1: ENV')
from core.aipulsar_environment import AiPulsarEnvironmentWindow
_write_startup_diag('IMP_2: PRO')
from core.pro_features import PulsarProExtraFeatures
_write_startup_diag('IMP_3: SCHED')
from core.scheduler_manager import PulsarScheduler
_write_startup_diag('IMP_4: TOOLS')
from core.smart_tools import PulsarSmartTools
_write_startup_diag('IMP_5: VOICE')
from core.voice import VoiceSpeaker
_write_startup_diag('IMP_6: ALL_IMPORTS_OK')


def main():
    _write_startup_diag('MAIN_TRACE_1: START')
    ensure_admin_and_privileges()
    _write_startup_diag('MAIN_TRACE_2: ADMIN_OK')
    ok_sig, sig_msg = verify_and_protect_runtime()
    _write_startup_diag(f'MAIN_TRACE_3: SIG={ok_sig} {sig_msg}')
    if not ok_sig:
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, sig_msg, "AiPulsar — Защита целостности VESKOR", 0x10)
        except Exception:
            pass
    pass
    _write_startup_diag('MAIN_TRACE_4B: MUTEX_PASSED')
    models_dir = _get_models_dir()
    _install_crash_shield(models_dir)

    memory = AgentMemory(models_dir=models_dir)
    macros = PulsarMacrosManager(models_dir=models_dir)
    _write_startup_diag('MAIN_TRACE_4C: INIT_BRAIN')
    brain = BrainEngine()
    lic_mgr = AiPulsarLicenseManager(models_dir=models_dir)
    updater = PulsarAutoUpdater()

    ui_holder = {"ui": None}
    speaker_holder = {"speaker": None}
    ears_holder = {"ears": None}
    free_chat_history = []
    cmd_lock = threading.Lock()
    chat_lock = threading.Lock()

    def _speak_safe(text: str):
        ui = ui_holder["ui"]
        spk = speaker_holder["speaker"]
        ears = ears_holder["ears"]
        if not text:
            return
        try:
            if spk and not getattr(spk, "muted", False):
                if ears:
                    ears.muted = True
                if ui:
                    ui.set_state("speaking")
                try:
                    spk.speak(str(text))
                finally:
                    if ears:
                        ears.muted = False
        except Exception:
            pass
        finally:
            if ui:
                ui.set_state("idle")

    hands = HandsExecutor(speak_callback=_speak_safe, models_dir=models_dir)
    smart_tools = PulsarSmartTools(brain=brain, vision=hands.vision)
    doc_vid = PulsarDocAndVideoTools(brain=brain)
    pro_extra = PulsarProExtraFeatures(vision=hands.vision, brain=brain)
    local_rag = PulsarLocalKnowledgeBase(brain=brain)
    sys_doc = PulsarSystemDoctorAndClipboard(brain=brain)
    super_pro = PulsarSuperProTools(vision=hands.vision, brain=brain, models_dir=models_dir)
    evo_engine = PulsarAutoEvolutionEngine(models_dir=models_dir, notify_cb=lambda s, m: ui_holder['ui'].log_free_chat(s, m) if ui_holder['ui'] else None)
    auto_routines = PulsarAutoRoutinesEngine(models_dir=models_dir, sys_doc=sys_doc, run_cmd_cb=lambda c: process_command(c), notify_cb=lambda s, m: ui_holder['ui'].log_free_chat(s, m) if ui_holder['ui'] else None)
    sec_radar = PulsarSecurityRadar(alert_cb=lambda m: (ui_holder['ui'].log_free_chat('AiPulsar', m) if ui_holder['ui'] else None, _speak_safe(m)))
    phone_bridge_holder = {'bridge': None}

    def _on_alarm_fired(alarm_text: str):
        if sys_doc.dnd_mode:
            sys_doc.missed_alarms.append(alarm_text)
            return
        if ui_holder["ui"]:
            ui_holder["ui"].log_free_chat("AiPulsar", f"⏰ Напоминание: {alarm_text}")
        _speak_safe(f"Внимание! Напоминание: {alarm_text}")

    scheduler = PulsarScheduler(models_dir=models_dir, trigger_cb=_on_alarm_fired)

    def _handle_quick_skills(text: str, log_fn) -> bool:
        low_s = text.lower()
        is_pro = lic_mgr.get_status().get("is_pro", False)
        pro_locked_msg = "Не могу выполнить: функция доступна только в Pro. Решение: включите бесплатный триал на 3 дня по кнопке «★ PRO ВЕРСИЯ»."

        if any(k in low_s for k in ("наведи порядок на рабочем столе", "разбери рабочий стол", "сортируй рабочий стол", "clean desktop")):
            org_res = auto_routines.organize_folder("desktop")
            log_fn("AiPulsar", org_res)
            _speak_safe("Готово.")
            return True

        if any(k in low_s for k in ("разбери загрузки", "разбери папку загрузки", "наведи порядок в загрузках", "clean downloads")):
            org_res = auto_routines.organize_folder("downloads")
            log_fn("AiPulsar", org_res)
            _speak_safe("Готово.")
            return True

        sched_res = auto_routines.try_schedule_routine(text)
        if sched_res:
            if not is_pro:
                log_fn("AiPulsar", pro_locked_msg)
                _speak_safe(pro_locked_msg)
                return True
            log_fn("AiPulsar", sched_res)
            _speak_safe("Готово.")
            return True
        learned_rule = evo_engine.try_learn_user_rule(text)
        if learned_rule:
            log_fn("AiPulsar", learned_rule)
            _speak_safe("Готово.")
            return True

        if any(k in low_s for k in ("чему ты научился", "статус самообучения", "что ты запомнил", "evolution status")):
            ev_msg = evo_engine.get_evolution_summary()
            log_fn("AiPulsar", ev_msg)
            _speak_safe(ev_msg)
            return True
        if any(k in low_s for k in ("включи машину времени", "запусти машину времени", "машина времени экрана", "enable screen time machine")):
            if not is_pro:
                log_fn("AiPulsar", pro_locked_msg)
                _speak_safe(pro_locked_msg)
                return True
            tm_msg = super_pro.start_screen_time_machine()
            log_fn("AiPulsar", tm_msg)
            _speak_safe("Готово.")
            return True

        if any(k in low_s for k in ("найди в памяти экрана", "найди на экране где", "что было на экране", "search screen memory")):
            if not is_pro:
                log_fn("AiPulsar", pro_locked_msg)
                _speak_safe(pro_locked_msg)
                return True
            tm_ans = super_pro.search_screen_time_machine(text)
            log_fn("AiPulsar", tm_ans)
            _speak_safe("Готово.")
            return True

        if any(k in low_s for k in ("включи суфлёр", "включи суфлер", "режим суфлёра", "режим суфлера", "enable prompter")):
            if not is_pro:
                log_fn("AiPulsar", pro_locked_msg)
                _speak_safe(pro_locked_msg)
                return True
            pr_msg = super_pro.toggle_invisible_prompter(True)
            log_fn("AiPulsar", pr_msg)
            _speak_safe("Готово.")
            return True

        if any(k in low_s for k in ("выключи суфлёр", "выключи суфлер", "disable prompter")):
            pr_msg = super_pro.toggle_invisible_prompter(False)
            log_fn("AiPulsar", pr_msg)
            _speak_safe("Готово.")
            return True

        if any(k in low_s for k in ("создай сайт", "сделай сайт", "сделай лендинг", "создай лендинг", "создай презентацию", "сделай презентацию", "create website", "create presentation")):
            if not is_pro:
                log_fn("AiPulsar", pro_locked_msg)
                _speak_safe(pro_locked_msg)
                return True
            site_msg = super_pro.generate_website_or_presentation(text)
            log_fn("AiPulsar", site_msg)
            _speak_safe("Готово.")
            return True
        if any(k in low_s for k in ("проверь безопасность", "радар безопасности", "кто использует камеру", "проверь камеру", "security radar")):
            r_msg = sec_radar.get_security_report()
            log_fn("AiPulsar", r_msg)
            _speak_safe(r_msg)
            return True

        if any(k in low_s for k in ("подключи телефон", "квантовый мост", "пульт на телефон", "qr код", "connect phone", "phone bridge")):
            if not is_pro:
                log_fn("AiPulsar", pro_locked_msg)
                _speak_safe(pro_locked_msg)
                return True
            if ui_holder["ui"]:
                if phone_bridge_holder["bridge"] is None:
                    phone_bridge_holder["bridge"] = QuantumPhoneBridgeDialog(
                        ui_holder["ui"].root,
                        on_remote_cmd=process_command,
                        on_notify=ui_holder["ui"].log_free_chat,
                    )
                ui_holder["ui"].root.after(0, phone_bridge_holder["bridge"].show)
            log_fn("AiPulsar", "Готово.")
            _speak_safe("Готово.")
            return True

        if any(k in low_s for k in ("спрячь секрет в картинку", "зашифруй в картинку", "hide secret in image")):
            if not is_pro:
                log_fn("AiPulsar", pro_locked_msg)
                _speak_safe(pro_locked_msg)
                return True
            sec_payload = text.split(":", 1)[-1].strip() if ":" in text else text
            v_msg = PulsarCryptoVault.hide_secret_in_image(sec_payload)
            log_fn("AiPulsar", v_msg)
            _speak_safe("Готово.")
            return True

        if any(k in low_s for k in ("достань секрет из картинки", "расшифруй картинку", "extract secret from image")):
            if not is_pro:
                log_fn("AiPulsar", pro_locked_msg)
                _speak_safe(pro_locked_msg)
                return True
            u_msg = PulsarCryptoVault.extract_secret_from_latest_image()
            log_fn("AiPulsar", u_msg)
            _speak_safe("Готово.")
            return True
        if any(k in low_s for k in ("я играю", "режим тишины", "не беспpulsarить", "игровой режим", "gaming mode", "do not disturb")):
            dnd_res = sys_doc.toggle_dnd(True)
            log_fn("AiPulsar", dnd_res)
            _speak_safe("Готово.")
            return True

        if any(k in low_s for k in ("закончил играть", "обычный режим", "выключи тишину", "выключи игровой", "exit gaming mode")):
            dnd_res = sys_doc.toggle_dnd(False)
            log_fn("AiPulsar", dnd_res)
            _speak_safe(dnd_res)
            return True

        if any(k in low_s for k in ("как чувствует себя компьютер", "как себя чувствует компьютер", "проверь нагрузку", "состояние пк", "состояние компьютера", "pc health")):
            h_res = sys_doc.check_pc_health()
            log_fn("AiPulsar", h_res)
            _speak_safe(h_res)
            return True

        if any(k in low_s for k in ("очисти память", "очисти временные", "почисти компьютер", "ускорь компьютер", "clean memory", "clean temp")):
            c_res = sys_doc.clean_temp_and_memory()
            log_fn("AiPulsar", c_res)
            _speak_safe(c_res)
            return True

        if any(k in low_s for k in ("разбери то, что я скопировал", "сделай выжимку из буфера", "разбери буфер", "напиши ответ на скопированное", "analyze clipboard")):
            if not is_pro:
                log_fn("AiPulsar", pro_locked_msg)
                _speak_safe(pro_locked_msg)
                return True
            mode = "reply" if "ответ" in low_s else "summary"
            cb_res = sys_doc.analyze_clipboard(mode=mode)
            log_fn("AiPulsar", cb_res)
            _speak_safe("Готово.")
            return True
        if any(k in low_s for k in ("проверь обновления", "обнови программу", "обновить pulsar", "check for updates")):
            has_u, new_v, url, msg = updater.check_for_updates()
            if has_u:
                log_fn("AiPulsar", f"Найдена версия v{new_v}. Запускаю обновление...")
                updater.download_and_apply_update(url)
            else:
                log_fn("AiPulsar", msg)
                _speak_safe(msg)
            return True

        if any(k in low_s for k in ("найди в моих документах", "поищи в документах", "что написано в моих файлах", "проверь документы", "search my documents", "find in my files")):
            if not is_pro:
                log_fn("AiPulsar", pro_locked_msg)
                return True
            rag_ans = local_rag.search_and_answer(text)
            log_fn("AiPulsar", rag_ans)
            _speak_safe(rag_ans[:220])
            return True

        if any(k in low_s for k in ("нажми на ", "кликни по ", "щёлкни по ", "нажми кнопку ", "click on ", "press ")):
            if not is_pro:
                log_fn("AiPulsar", pro_locked_msg)
                return True
            clk_res = pro_extra.click_text_on_screen(text)
            log_fn("AiPulsar", clk_res)
            _speak_safe(clk_res)
            return True

        if any(k in low_s for k in ("запиши разговор", "начни запись разговора", "включи диктофон", "record meeting")):
            if not is_pro:
                log_fn("AiPulsar", pro_locked_msg)
                return True
            m_res = pro_extra.start_meeting_recorder()
            log_fn("AiPulsar", m_res)
            _speak_safe(m_res)
            return True

        if any(k in low_s for k in ("останови запись разговора", "стоп запись разговора", "расшифруй разговор", "stop meeting recording")):
            if not is_pro:
                log_fn("AiPulsar", pro_locked_msg)
                return True
            t_res = pro_extra.stop_and_transcribe_meeting()
            log_fn("AiPulsar", t_res)
            _speak_safe("Расшифровка разговора готова.")
            return True

        if any(k in low_s for k in ("начни запись экрана", "запиши экран", "включи запись экрана", "start screen recording", "record screen")):
            if not is_pro:
                log_fn("AiPulsar", pro_locked_msg)
                return True
            rec_msg = doc_vid.start_screen_recording()
            log_fn("AiPulsar", rec_msg)
            _speak_safe(rec_msg)
            return True

        if any(k in low_s for k in ("останови запись", "стоп запись", "выключи запись экрана", "заверши запись", "stop screen recording", "stop recording")):
            if not is_pro:
                log_fn("AiPulsar", pro_locked_msg)
                return True
            stop_msg = doc_vid.stop_screen_recording()
            log_fn("AiPulsar", stop_msg)
            _speak_safe("Запись экрана сохранена.")
            return True

        if any(k in low_s for k in ("создай word", "создай ворд", "создай excel", "создай эксель", "создай таблицу", "сделай таблицу", "создай документ", "create word", "create excel", "create document", "create table")):
            if not is_pro:
                log_fn("AiPulsar", pro_locked_msg)
                return True
            doc_msg = doc_vid.create_office_document(text)
            log_fn("AiPulsar", doc_msg)
            _speak_safe(doc_msg)
            return True

        if any(k in low_s for k in ("переведи", "как будет по-", "как будет на ", "translate", "how do you say")):
            if not is_pro:
                log_fn("AiPulsar", pro_locked_msg)
                return True
            tr_res = smart_tools.translate_selection_or_text(text)
            log_fn("AiPulsar", tr_res)
            first_line = next(iter(tr_res.splitlines()), tr_res)
            _speak_safe(first_line)
            return True

        if any(k in low_s for k in ("извлеки текст", "текст с картинки", "прочитай картинку", "extract text", "read image")):
            if not is_pro:
                log_fn("AiPulsar", pro_locked_msg)
                return True
            ocr_res = smart_tools.ocr_image_or_screen()
            log_fn("AiPulsar", ocr_res)
            _speak_safe("Текст распознан.")
            return True
        if any(k in low_s for k in ("сделай pdf", "в pdf", "сожми папку", "сделай архив", "упакуй в архив")):
            conv_res = smart_tools.convert_to_pdf_or_zip(text)
            log_fn("AiPulsar", conv_res)
            _speak_safe(conv_res)
            return True

        if any(k in low_s for k in ("поставь на обои", "установи обои", "смени обои")):
            wp_res = smart_tools.set_desktop_wallpaper(text)
            log_fn("AiPulsar", wp_res)
            _speak_safe(wp_res)
            return True

        sched_reply = scheduler.try_schedule_from_text(text)
        if sched_reply:
            log_fn("AiPulsar", sched_reply)
            memory.remember_command(text, sched_reply)
            _speak_safe(sched_reply)
            return True

        learned = macros.try_learn_macro(text)
        if learned:
            log_fn("AiPulsar", learned)
            _speak_safe(learned)
            return True

        m_name, m_steps = macros.match_macro(text)
        if m_name and m_steps:
            for st in m_steps:
                t_name = st.get("tool")
                if t_name == "fullscreen_on" and ui_holder["ui"]:
                    ui_holder["ui"].set_fullscreen(True)
                elif t_name != "hide_to_tray":
                    hands.execute(t_name, st.get("args", {}))
            m_reply = "Готово."
            log_fn("AiPulsar", m_reply)
            _speak_safe(m_reply)
            return True

        return False

    def process_command(user_text: str):
        ui = ui_holder["ui"]
        cmd_txt = (user_text or "").strip()
        if not ui or not cmd_txt:
            return

        with cmd_lock:
            ui.log_message("Вы", cmd_txt)
            ui.set_state("thinking")
            try:
                if _handle_quick_skills(cmd_txt, ui.log_message):
                    return

                history = [{"role": "user", "content": f"ЗАДАЧА ПОЛЬЗОВАТЕЛЯ: {cmd_txt}"}]
                for _ in range(5):
                    step = brain.next_step(history)
                    tool = str(step.get("tool", "finish"))
                    args = step.get("args", {}) if isinstance(step.get("args"), dict) else {}

                    if tool == "finish":
                        raw_reply = str(args.get("reply") or "").strip()
                        low_rep = raw_reply.lower()
                        if any(err_w in low_rep for err_w in ("не удалось", "ошибка", "не найден", "нет доступа", "не могу", "доступно в версии")):
                            ui.log_message("AiPulsar", raw_reply)
                            _speak_safe(raw_reply)
                        else:
                            ui.log_message("AiPulsar", "Готово.")
                            memory.remember_command(cmd_txt, "Готово.")
                            _speak_safe("Готово.")
                        return

                    obs = hands.execute(tool, args)
                    history.append({"role": "assistant", "content": str(step)})
                    history.append({"role": "user", "content": f"[Результат {tool}]: {obs}"})

                ui.log_message("AiPulsar", "Готово."); _speak_safe("Готово.")
            except Exception as e:
                fail_txt = f"Не могу выполнить: {e}. Решение: проверьте название или права доступа."; ui.log_message("AiPulsar", fail_txt); _speak_safe(fail_txt)
            finally:
                ui.set_state("idle")

    def process_free_chat(user_text: str):
        ui = ui_holder["ui"]
        question = (user_text or "").strip()
        if not ui or not question:
            return

        with chat_lock:
            ui.log_free_chat("Вы", question)
            ui.set_state("thinking")
            try:
                if _handle_quick_skills(question, ui.log_free_chat):
                    return

                if any(w in question.lower() for w in ("посмотри на экран", "что на экране", "прочитай экран")):
                    scr = hands.vision.read_screen_summary()
                    question = f"{question}\n\n[ТЕКСТ С ЭКРАНА]:\n{scr}"

                free_chat_history.append({"role": "user", "content": question})
                mem_ctx = memory.build_memory_context(question) + evo_engine.get_learned_context()
                answer = brain.ask_free_chat(free_chat_history, memory_context=mem_ctx)
                if not answer:
                    answer = "Я на связи. Уточни, пожалуйста, вопрос или задачу."

                free_chat_history.append({"role": "assistant", "content": answer})
                ui.log_free_chat("AiPulsar", answer)
                memory.remember_chat(question, answer)
                if not super_pro.prompter_active: _speak_safe(answer)
            except Exception as e:
                ui.log_free_chat("AiPulsar", f"Ошибка ответа: {e}")
            finally:
                ui.set_state("idle")

    _write_startup_diag('MAIN_TRACE_4D: INIT_UI_WINDOW')

    def _unified_chat_and_command(raw_text: str):
        q = (raw_text or "").strip()
        if not q:
            return
        if ui_holder.get("ui"):
            ui_holder["ui"].append_log("Вы", q)
        low = q.lower()
        # 1. Проверяем живой поиск, свежие новости, самообучение и изолированные моды
        try:
            from core.live_web_and_self_learn import LiveWebAndSelfLearnEngine
            live_ans = LiveWebAndSelfLearnEngine().try_handle_request(q)
            if live_ans:
                if ui_holder.get("ui"):
                    ui_holder["ui"].append_log("AiPulsar", live_ans)
                threading.Thread(target=_speak_safe, args=(live_ans[:320],), daemon=True).start()
                return
        except Exception:
            pass

        # 2. Проверяем системные команды управления ПК
        sys_triggers = (
            "открой", "запусти", "закрой", "выключи", "перезагрузи", "громкость", "тише", "громче",
            "скриншот", "сверни", "разверни", "режим игры", "режим кино", "здоровье", "сканируй",
            "очисти", "проанализируй файл", "буфер", "напомни", "таймер", "будильник",
        )
        if any(low.startswith(t) or t in low for t in sys_triggers):
            process_command(q)
        else:
            # 3. Все остальные вопросы, диалог и рассуждения идут в умный ИИ-чат
            process_free_chat(q)


    ui = AiPulsarEnvironmentWindow(on_text_command=_unified_chat_and_command, on_free_chat=process_free_chat)
    ui_holder["ui"] = ui
    try:
        from core.auto_updater import GitHubAutoUpdater
        GitHubAutoUpdater(models_dir=models_dir).start_background_update_checker(ui_holder)
    except Exception:
        pass

    try:
        from core.ear import set_global_heard_callback
        def _heard_to_chat_and_exec(heard_txt: str):
            clean_h = (heard_txt or "").strip()
            if not clean_h:
                return
            if ui_holder.get("ui"):
                ui_holder["ui"].append_log("Вы", clean_h)
            _unified_chat_and_command(clean_h)
        set_global_heard_callback(_heard_to_chat_and_exec)
    except Exception:
        pass

    def background_worker():
        try:
            speaker = VoiceSpeaker(outputs_cb=ui.set_out_list)
            speaker.refresh_output_devices(initial=True)
            speaker_holder["speaker"] = speaker
            ui.on_out_selected = speaker.select_output_by_label
            ui.on_mute_toggled = speaker.set_muted
        except Exception:
            pass

        try:
            ears = VoiceEars(level_cb=ui.set_mic_level, devices_cb=ui.set_mic_list)
            ears_holder["ears"] = ears
            ui.on_mic_selected = ears.select_device_by_label
        except Exception:
            return

        while True:
            try:
                heard = ears.listen_phrase(silence_duration=1.0)
                if not heard:
                    continue
                ui.set_state("listening")
                cmd = re.sub(r"^(ассистент|компьютер|джарвис|помощник|pulsar|pulsar|пульсар)[,\s]*", "", heard, flags=re.I).strip() or heard.strip()
                gc_reply = GameCinemaModeManager.get_instance().handle_voice_command(cmd)
                if gc_reply:
                    if speaker_holder.get('speaker'): speaker_holder['speaker'].speak(gc_reply)
                    continue
                process_command(cmd)
            except Exception:
                pass

    threading.Thread(target=background_worker, daemon=True).start()
    _write_startup_diag('STEP: OPENING MAIN WINDOW')
    _write_startup_diag('MAIN_STEP_5: STARTING_UI_MAINLOOP')
    _write_startup_diag('MAIN_TRACE_5: RUN_MAINLOOP')
    ui.run_mainloop()


if __name__ == "__main__":
    main()









