# -*- coding: utf-8 -*-
import datetime
import hashlib
import json
import os
import sys

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
except Exception:
    openpyxl = None


def _get_base_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_excel_registry_path() -> str:
    return os.path.join(_get_base_dir(), "AiPulsar_Licenses_Registry.xlsx")


def record_license_to_excel(
    hwid: str,
    plan_name: str,
    days: int,
    amount_str: str,
    license_key: str,
    email: str = "",
    expires_at: str = "",
    status: str = "АКТИВНА (HWID ПРИВЯЗАН)",
) -> str:
    xlsx_path = get_excel_registry_path()
    if not openpyxl:
        return xlsx_path

    headers = [
        "Дата операции",
        "HWID оборудования",
        "Тарифный план",
        "Срок (дней)",
        "Стоимость",
        "Лицензионный ключ",
        "E-mail покупателя",
        "Действует до",
        "Статус лицензии",
    ]

    if os.path.exists(xlsx_path):
        wb = openpyxl.load_workbook(xlsx_path)
        ws = wb.active
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Реестр лицензий AiPulsar"
        ws.append(headers)
        hdr_fill = PatternFill(start_color="0078D4", end_color="0078D4", fill_type="solid")
        hdr_font = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.fill = hdr_fill
            cell.font = hdr_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
        col_widths = (20, 22, 28, 14, 18, 24, 26, 16, 26)
        for idx, w in enumerate(col_widths, 1):
            ws.column_dimensions[openpyxl.utils.get_column_letter(idx)].width = w

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not expires_at and days > 0:
        expires_at = (datetime.datetime.now() + datetime.timedelta(days=int(days))).strftime("%Y-%m-%d")

    updated_row = None
    for r in range(2, ws.max_row + 1):
        if str(ws.cell(row=r, column=2).value or "").strip() == str(hwid).strip():
            updated_row = r
            break

    row_values = [now_str, hwid, plan_name, int(days), amount_str, license_key, email, expires_at, status]
    if updated_row:
        for c_i, val in enumerate(row_values, 1):
            ws.cell(row=updated_row, column=c_i, value=val)
    else:
        ws.append(row_values)

    wb.save(xlsx_path)
    return xlsx_path


def find_license_by_hwid_in_excel(hwid: str) -> dict:
    xlsx_path = get_excel_registry_path()
    if not openpyxl or not os.path.exists(xlsx_path):
        return {}
    try:
        wb = openpyxl.load_workbook(xlsx_path, data_only=True)
        ws = wb.active
        for r in range(ws.max_row, 1, -1):
            row_hwid = str(ws.cell(row=r, column=2).value or "").strip()
            if row_hwid == str(hwid).strip():
                return {
                    "hwid": row_hwid,
                    "plan_name": str(ws.cell(row=r, column=3).value or "AiPulsar Pro"),
                    "days": int(ws.cell(row=r, column=4).value or 30),
                    "amount": str(ws.cell(row=r, column=5).value or ""),
                    "key": str(ws.cell(row=r, column=6).value or ""),
                    "email": str(ws.cell(row=r, column=7).value or ""),
                    "expires_at": str(ws.cell(row=r, column=8).value or ""),
                }
    except Exception:
        pass
    return {}


def export_backup_license_file(target_path: str, hwid: str, key: str, days: int = 365, email: str = "") -> str:
    payload = {
        "product": "AiPulsar Pro",
        "hwid": hwid,
        "key": key,
        "days": int(days),
        "email": email,
        "exported_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    raw_sig = f"VESKOR-AIPULSAR-BACKUP|{hwid}|{key}|{days}".encode("utf-8")
    payload["signature"] = hashlib.sha256(raw_sig).hexdigest()
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return target_path


def verify_backup_license_file(file_path: str, current_hwid: str) -> tuple:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        hwid = str(data.get("hwid", "")).strip()
        key = str(data.get("key", "")).strip()
        days = int(data.get("days", 30))
        sig = str(data.get("signature", "")).strip()
        expected = hashlib.sha256(f"VESKOR-AIPULSAR-BACKUP|{hwid}|{key}|{days}".encode("utf-8")).hexdigest()
        if sig != expected:
            return False, "Недействительная цифровая подпись файла лицензии.", {}
        if hwid != str(current_hwid).strip():
            return False, f"Файл привязан к другому оборудованию ({hwid}). Текущий HWID: {current_hwid}.", {}
        return True, "Лицензия успешно подтверждена по HWID оборудования!", data
    except Exception as e:
        return False, f"Ошибка чтения файла лицензии: {e}", {}
