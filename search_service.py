import re
from typing import Optional, Tuple, List, Dict
from db_connection import get_connection


class ParsedQuery:
    def __init__(self, *, kind: str, length_mm: Optional[float], profile: Optional[str], width_mm: Optional[float]):
        self.kind = kind  # "synchronous" | "vbelt"
        self.length_mm = length_mm
        self.profile = profile
        self.width_mm = width_mm


EXCEPT_PREFIXES_STRUNINO = ("3V", "5V", "8V", "3VX", "5VX")
KNOWN_SYNC_PROFILES = [
    # Сначала более длинные для корректного суффиксного совпадения
    "14M", "T10", "T5", "8M", "L", "H"
]


def parse_query(q: str) -> ParsedQuery:
    # Не допускаем пробелы/табуляции во входе
    text_raw = q.strip().upper()
    if any(ch.isspace() for ch in text_raw):
        return ParsedQuery(kind="unknown", length_mm=None, profile=None, width_mm=None)

    text = text_raw

    # Ширина как =NN (мм)
    width = None
    if "=" in text:
        base, width_part = text.split("=", 1)
        if not width_part.isdigit():
            return ParsedQuery(kind="unknown", length_mm=None, profile=None, width_mm=None)
        try:
            width = float(width_part)
        except ValueError:
            return ParsedQuery(kind="unknown", length_mm=None, profile=None, width_mm=None)
        text = base

    # Специальные исключения: 3V/5V/8V/3VX/5VX → клиновые, профиль в префиксе
    m_exc = re.match(r"^(3VX|5VX|3V|5V|8V)(\d+)$", text)
    if m_exc:
        profile = m_exc.group(1)
        length = float(m_exc.group(2))
        return ParsedQuery(kind="vbelt", length_mm=length, profile=profile, width_mm=width)

    # Если начинается с цифр → синхронные (length+profile), профиль берём из известного суффикса
    if re.match(r"^\d", text):
        profile = None
        for p in KNOWN_SYNC_PROFILES:
            if text.endswith(p):
                profile = p
                prefix = text[:-len(p)]
                try:
                    length = float(prefix)
                except ValueError:
                    length = None
                return ParsedQuery(kind="synchronous", length_mm=length, profile=profile, width_mm=width)
        # если профиль не распознан, используем общее разбиение как раньше
        m = re.match(r"^(\d+)([A-Z0-9]+)$", text)
        length = float(m.group(1)) if m else None
        profile = m.group(2) if m else None
        return ParsedQuery(kind="synchronous", length_mm=length, profile=profile, width_mm=width)

    # Если начинается с букв → клиновые (profile+length)
    m = re.match(r"^([A-Z]+)(\d+)$", text)
    if m:
        profile = m.group(1)
        length = float(m.group(2))
        return ParsedQuery(kind="vbelt", length_mm=length, profile=profile, width_mm=width)

    # Фолбэк: неизвестно
    return ParsedQuery(kind="unknown", length_mm=None, profile=None, width_mm=None)


def route_warehouse(original_text: str) -> str:
    t = original_text.strip().upper().replace(" ", "")
    # Сначала проверяем исключения
    for pref in EXCEPT_PREFIXES_STRUNINO:
        if t.startswith(pref):
            return "Струнино"
    # Начинается с цифр → Москва
    if re.match(r"^\d", t):
        return "Москва"
    # Начинается с букв → Струнино
    return "Струнино"


def search_products(query: str) -> List[Dict]:
    parsed = parse_query(query)
    warehouse = route_warehouse(query)

    # Конвертация для клиновых ремней, где длина задаётся в дюймах (классические профили)
    # Конвертируем дюймы только для классических профилей A/B/C/D/E.
    # Для 3V/5V/8V/3VX/5VX длина в БД и запросах используем в мм без конвертации.
    INCH_PROFILES = {"A", "B", "C", "D", "E"}
    eff_length = parsed.length_mm
    if parsed.kind == "vbelt" and parsed.profile in INCH_PROFILES and eff_length is not None:
        eff_length = eff_length * 25.4  # дюймы → мм

    sql = "SELECT * FROM products WHERE TRIM(warehouse) = %s AND quantity_free > 0"
    params: List = [warehouse]

    # Фильтры по профилю
    if parsed.profile:
        sql += " AND UPPER(TRIM(profile)) = %s"
        params.append(parsed.profile.upper())

    # Фильтры по длине
    if eff_length is not None:
        if parsed.kind == "vbelt":
            # Допуск ±1.5%
            delta = eff_length * 0.015
            sql += " AND length BETWEEN %s AND %s"
            params.extend([eff_length - delta, eff_length + delta])
        else:
            # Для синхронных применим строгую проверку с небольшим допуском на округление
            sql += " AND ABS(length - %s) < 0.5"
            params.append(eff_length)

    # Фильтр по ширине (если задана)
    if parsed.width_mm is not None:
        sql += " AND width = %s"
        params.append(parsed.width_mm)

    # Порядок: по цене, затем по бренду/названию
    sql += " ORDER BY price_per_unit NULLS LAST, name"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            return rows


def format_search_results(rows: List[Dict]) -> str:
    if not rows:
        return "Ничего не найдено по заданным критериям."

    lines = []
    for r in rows[:20]:  # ограничим до 20 строк на сообщение
        name = r.get("name")
        length = r.get("length")
        profile = r.get("profile")
        width = r.get("width")
        qty = r.get("quantity_free")
        price = r.get("price_per_unit") or r.get("price_per_mm") or 0
        warehouse = r.get("warehouse")

        # Формат близкий к примерам
        if width:
            line = f"{name} остаток {qty} шт. цена {price} руб"
        else:
            # Для синхронных примерах были мм — оставим общий формат
            line = f"{name} остаток {qty} шт. цена {price} руб"
        lines.append("· " + line)

    return "\n".join(lines)


