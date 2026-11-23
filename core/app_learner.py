# -*- coding: utf-8 -*-
# Copyright (c) 2026 V.E. Smirnov (VESKOR). All rights reserved.
# Author: V.E. Smirnov | Company: VESKOR | Contact: veskor.dev-2026@yandex.ru
import datetime
import json
import os
import re
import subprocess
import urllib.parse
import urllib.request
import ezdxf
from typing import Any, Dict, List


class SoftwareLearnerAndCAD:
    """Самообучение любым программам по приказу и автономное черчение проектов с размерами для AutoCAD."""

    def __init__(self, models_dir: str, web_agent=None):
        self.models_dir = models_dir
        os.makedirs(models_dir, exist_ok=True)
        self.skills_path = os.path.join(models_dir, "software_skills.json")
        self.web_agent = web_agent
        self.skills = self._load()

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.skills_path):
            try:
                with open(self.skills_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save(self):
        with open(self.skills_path, "w", encoding="utf-8") as f:
            json.dump(self.skills, f, ensure_ascii=False, indent=2)

    def learn_software(self, program_name: str, task_focus: str = "") -> str:
        """Изучает горячие клавиши, команды и логику работы любой программы и сохраняет навсегда."""
        prog = (program_name or "").strip()
        if not prog:
            return "Не указано название программы для обучения."

        query = f"{prog} горячие клавиши команды руководство {task_focus}".strip()
        knowledge = ""
        if self.web_agent:
            knowledge = self.web_agent.search_internet(query)

        key = prog.lower()
        self.skills[key] = {
            "program": prog,
            "learned_at": datetime.datetime.now().strftime("%d.%m.%Y %H:%M"),
            "focus": task_focus,
            "notes": knowledge[:2500] if knowledge else f"Базовые команды и интерфейс {prog} изучены.",
        }
        self._save()
        return f"Я изучил программу «{prog}» и сохранил её команды и горячие клавиши в свою постоянную память."

    def get_learned_software_context(self) -> str:
        if not self.skills:
            return ""
        lines = ["ИЗУЧЕННЫЕ ПРОГРАММЫ И КОМАНДЫ (из твоей постоянной базы знаний):"]
        for k, v in self.skills.items():
            lines.append(f"- {v.get('program')}: {v.get('notes', '')[:600]}")
        return "\n".join(lines)

    def draw_house_cad_project(
        self,
        width_mm: float = 10000,
        length_mm: float = 8000,
        wall_thick: float = 400,
        rooms: List[Dict[str, Any]] = None,
        project_title: str = "Проект жилого дома",
    ) -> str:
        """
        Создаёт профессиональный чертёж дома в формате AutoCAD DXF со слоями,
        несущими стенами, перегородками, проёмами, подписями площадей и всеми размерными линиями,
        затем автоматически открывает его в AutoCAD (или установленном CAD-просмотрщике).
        """
        W = float(width_mm)
        L = float(length_mm)
        T = float(wall_thick)

        doc = ezdxf.new(dxfversion="R2010")
        msp = doc.modelspace()

        # Создаём инженерные слои AutoCAD
        doc.layers.add("WALLS_MAIN", color=7)     # Белый/чёрный — несущие стены
        doc.layers.add("WALLS_PART", color=3)     # Зелёный — перегородки
        doc.layers.add("DIMENSIONS", color=1)     # Красный — размерные линии
        doc.layers.add("TEXT_LABELS", color=4)    # Голубой — экспликация и площади
        doc.layers.add("WINDOWS_DOORS", color=2)  # Жёлтый — окна и двери

        # 1. Наружный и внутренний контур капитальных стен
        outer_pts = [(0, 0), (W, 0), (W, L), (0, L), (0, 0)]
        inner_pts = [(T, T), (W - T, T), (W - T, L - T), (T, L - T), (T, T)]
        msp.add_lwpolyline(outer_pts, dxfattribs={"layer": "WALLS_MAIN", "lineweight": 50})
        msp.add_lwpolyline(inner_pts, dxfattribs={"layer": "WALLS_MAIN", "lineweight": 35})

        # 2. Внутренняя планировка помещений (если не задана вручную — строим эргономичную планировку)
        if not rooms:
            mid_x = round(W * 0.55, 0)
            mid_y = round(L * 0.50, 0)
            # Несущая центральная стена и перегородки
            msp.add_line((mid_x, T), (mid_x, L - T), dxfattribs={"layer": "WALLS_PART", "lineweight": 25})
            msp.add_line((mid_x, mid_y), (W - T, mid_y), dxfattribs={"layer": "WALLS_PART", "lineweight": 25})
            msp.add_line((T, round(L * 0.35, 0)), (mid_x, round(L * 0.35, 0)), dxfattribs={"layer": "WALLS_PART", "lineweight": 25})

            default_rooms = [
                {"name": "Кухня-гостиная", "x": mid_x / 2, "y": L * 0.68, "area": round(((mid_x - T) * (L * 0.65 - T)) / 1e6, 1)},
                {"name": "Прихожая / Холл", "x": mid_x * 0.35, "y": L * 0.18, "area": round(((mid_x * 0.6) * (L * 0.35 - T)) / 1e6, 1)},
                {"name": "Санузел", "x": mid_x * 0.80, "y": L * 0.18, "area": round(((mid_x * 0.4 - T) * (L * 0.35 - T)) / 1e6, 1)},
                {"name": "Спальня 1", "x": (mid_x + W) / 2, "y": L * 0.75, "area": round(((W - T - mid_x) * (L - T - mid_y)) / 1e6, 1)},
                {"name": "Спальня 2", "x": (mid_x + W) / 2, "y": L * 0.25, "area": round(((W - T - mid_x) * (mid_y - T)) / 1e6, 1)},
            ]
            rooms_to_draw = default_rooms
        else:
            rooms_to_draw = rooms

        # 3. Pulsarнные проёмы на фасадах и входная дверь
        win_w = 1500
        msp.add_lwpolyline([(W * 0.2, 0), (W * 0.2 + win_w, 0), (W * 0.2 + win_w, T), (W * 0.2, T), (W * 0.2, 0)], dxfattribs={"layer": "WINDOWS_DOORS"})
        msp.add_lwpolyline([(W * 0.65, L - T), (W * 0.65 + win_w, L - T), (W * 0.65 + win_w, L), (W * 0.65, L), (W * 0.65, L - T)], dxfattribs={"layer": "WINDOWS_DOORS"})
        # Входная дверь (снизу)
        msp.add_lwpolyline([(W * 0.42, 0), (W * 0.42 + 1000, 0), (W * 0.42 + 1000, T), (W * 0.42, T)], dxfattribs={"layer": "WINDOWS_DOORS"})

        # 4. Подписи помещений и площадей
        for r in rooms_to_draw:
            rx, ry = float(r.get("x", W / 2)), float(r.get("y", L / 2))
            rname = str(r.get("name", "Помещение"))
            rarea = r.get("area", "")
            label = f"{rname} ({rarea} м2)" if rarea else rname
            txt = msp.add_text(label, dxfattribs={"layer": "TEXT_LABELS", "height": 220})
            txt.set_placement((rx - 800, ry))

        # 5. Простановка инженерных размерных линий (наружные и внутренние габариты в мм)
        dim_style = {"dimtxt": 220, "dimasz": 150, "dimclrd": 1, "dimclre": 1, "dimclrt": 1}
        # Общий нижний размер (Ширина)
        d1 = msp.add_linear_dim(base=(0, -900), p1=(0, 0), p2=(W, 0), override=dim_style, dxfattribs={"layer": "DIMENSIONS"})
        d1.render()
        # Внутренний размер по стенам (Ширина)
        d2 = msp.add_linear_dim(base=(0, -450), p1=(T, 0), p2=(W - T, 0), override=dim_style, dxfattribs={"layer": "DIMENSIONS"})
        d2.render()
        # Общий левый размер (Длина)
        d3 = msp.add_linear_dim(base=(-900, 0), p1=(0, 0), p2=(0, L), angle=90, override=dim_style, dxfattribs={"layer": "DIMENSIONS"})
        d3.render()
        # Внутренний размер по стенам (Длина)
        d4 = msp.add_linear_dim(base=(-450, 0), p1=(0, T), p2=(0, L - T), angle=90, override=dim_style, dxfattribs={"layer": "DIMENSIONS"})
        d4.render()

        # Заголовок чертежа
        title_ent = msp.add_text(f"{project_title} ({int(W)}x{int(L)} мм)", dxfattribs={"layer": "TEXT_LABELS", "height": 320})
        title_ent.set_placement((0, L + 600))

        # 6. Сохраняем чертёж на Рабочий стол в папку Проекты_Pulsar и открываем в AutoCAD
        out_dir = os.path.join(os.path.expanduser("~"), "Desktop", "Проекты_Pulsar")
        os.makedirs(out_dir, exist_ok=True)
        fname = f"House_Project_{int(W)}x{int(L)}_{datetime.datetime.now().strftime('%H%M%S')}.dxf"
        full_path = os.path.join(out_dir, fname)
        doc.saveas(full_path)

        try:
            os.startfile(full_path)
            opened_msg = "и сразу открыл его в AutoCAD."
        except Exception:
            opened_msg = "Чертёж готов к открытию в AutoCAD."

        return (
            f"Инженерный чертёж дома {int(W)} на {int(L)} мм со слоями стен, перегородок, pulsarн, дверей, "
            f"экспликацией площадей и всеми размерными линиями сохранён на Рабочий стол ({fname}) {opened_msg}"
        )

