import re
from typing import Optional, List, Dict
from db_connection import get_connection


class ParsedQuery:
    def __init__(self, *, kind: str, length_mm: Optional[float], profile: Optional[str], width_mm: Optional[float]):
        self.kind = kind 
        self.length_mm = length_mm
        self.profile = profile
        self.width_mm = width_mm


EXCEPT_PREFIXES_STRUNINO = ("3V", "5V", "8V", "3VX", "5VX")
KNOWN_SYNC_PROFILES = [
    "14M", "T10", "T5", "8M", "L", "H"
]


def parse_query(q: str) -> ParsedQuery:
    text_raw = q.strip().upper()
    if any(ch.isspace() for ch in text_raw):
        return ParsedQuery(kind="unknown", length_mm=None, profile=None, width_mm=None)

    text = text_raw

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
        eff_length = eff_length * 25.4 

    sql = "SELECT * FROM products WHERE TRIM(warehouse) = %s AND quantity_free > 0"
    params: List = [warehouse]

    # Фильтры по профилю
    if parsed.profile:
        sql += " AND UPPER(TRIM(profile)) = %s"
        params.append(parsed.profile.upper())

    # Фильтры по длине
    if eff_length is not None:
        if parsed.kind == "vbelt":
            delta = eff_length * 0.015
            sql += " AND length BETWEEN %s AND %s"
            params.extend([eff_length - delta, eff_length + delta])
        else:
            sql += " AND ABS(length - %s) < 0.5"
            params.append(eff_length)

    # Фильтр по ширине (если задана)
    if parsed.width_mm is not None:
        sql += " AND width = %s"
        params.append(parsed.width_mm)

    if parsed.kind == "vbelt" and eff_length is not None:
        sql += (
            " ORDER BY ABS(length - %s) NULLS LAST, "
            " CASE "
            "  WHEN UPPER(name) LIKE '%% FNR%%' THEN 1 "
            "  WHEN UPPER(name) LIKE '%% PIX MUSCLE XS3%%' THEN 2 "
            "  WHEN UPPER(name) LIKE '%% PIX XSET%%' THEN 3 "
            "  WHEN UPPER(name) LIKE '%% MEGADYNE EXTRA%%' THEN 4 "
            "  ELSE 5 END, "
            " price_per_unit NULLS LAST, name"
        )
        params.append(eff_length)
    else:
        sql += (
            " ORDER BY "
            " CASE "
            "  WHEN UPPER(name) LIKE '%% CFNR%%' THEN 1 "
            "  WHEN UPPER(name) LIKE '%% CONTITECH%%' AND UPPER(name) NOT LIKE '%%CXP%%' THEN 2 "
            "  WHEN UPPER(name) LIKE '%%CXP CONTITECH%%' THEN 3 "
            "  WHEN UPPER(name) LIKE '%% MEGADYNE%%' THEN 4 "
            "  ELSE 5 END, "
            " price_per_unit NULLS LAST, name"
        )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            return rows


def search_products_structured(*, kind: str, length_mm: Optional[float], profile: Optional[str], width_mm: Optional[float], original_text: str) -> List[Dict]:
    """Search using structured parameters (from AI).
    """
    if profile and profile.upper() in EXCEPT_PREFIXES_STRUNINO:
        warehouse = "Струнино"
    elif kind == "synchronous":
        warehouse = "Москва"
    elif kind == "vbelt":
        warehouse = "Струнино"
    else:
        warehouse = route_warehouse(original_text)
    # print(f"[SEARCH] Параметры поиска: kind={kind}, length={length_mm}, profile={profile}, width={width_mm}, warehouse={warehouse}")

    INCH_PROFILES = {"A", "B", "C", "D", "E"}
    eff_length = length_mm
    if kind == "vbelt" and (profile or "").upper() in INCH_PROFILES and eff_length is not None:
        eff_length = eff_length * 25.4
        # print(f"[SEARCH] Конвертация дюймов в мм: {length_mm} -> {eff_length}")

    sql = "SELECT * FROM products WHERE TRIM(warehouse) = %s AND quantity_free > 0"
    params: List = [warehouse]

    if profile:
        sql += " AND UPPER(TRIM(profile)) = %s"
        params.append(profile.upper())

    if eff_length is not None:
        if kind == "vbelt":
            delta = eff_length * 0.015
            sql += " AND length BETWEEN %s AND %s"
            params.extend([eff_length - delta, eff_length + delta])
        else:
            sql += " AND ABS(length - %s) < 0.5"
            params.append(eff_length)

    if width_mm is not None:
        sql += " AND width = %s"
        params.append(width_mm)

    # Reuse same ordering rules as above
    if kind == "vbelt" and eff_length is not None:
        sql += (
            " ORDER BY ABS(length - %s) NULLS LAST, "
            " CASE "
            "  WHEN UPPER(name) LIKE '%% FNR%%' THEN 1 "
            "  WHEN UPPER(name) LIKE '%% PIX MUSCLE XS3%%' THEN 2 "
            "  WHEN UPPER(name) LIKE '%% PIX XSET%%' THEN 3 "
            "  WHEN UPPER(name) LIKE '%% MEGADYNE EXTRA%%' THEN 4 "
            "  ELSE 5 END, "
            " price_per_unit NULLS LAST, name"
        )
        params.append(eff_length)
    else:
        sql += (
            " ORDER BY "
            " CASE "
            "  WHEN UPPER(name) LIKE '%% CFNR%%' THEN 1 "
            "  WHEN UPPER(name) LIKE '%% CONTITECH%%' AND UPPER(name) NOT LIKE '%%CXP%%' THEN 2 "
            "  WHEN UPPER(name) LIKE '%%CXP CONTITECH%%' THEN 3 "
            "  WHEN UPPER(name) LIKE '%% MEGADYNE%%' THEN 4 "
            "  ELSE 5 END, "
            " price_per_unit NULLS LAST, name"
        )

    # print(f"[SEARCH] SQL запрос: {sql}")
    # print(f"[SEARCH] Параметры: {params}")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            # print(f"[SEARCH] Найдено строк в БД: {len(rows)}")
            return rows


def format_search_results(rows: List[Dict]) -> str:
    if not rows:
        return "Ничего не найдено по заданным критериям."

    lines = []
    for r in rows[:20]: 
        name = r.get("name")
        length = r.get("length")
        profile = r.get("profile")
        width = r.get("width")
        qty = r.get("quantity_free")
        price = r.get("price_per_unit") or r.get("price_per_mm") or 0
        warehouse = r.get("warehouse")

        if width:
            line = f"{name} остаток {qty} шт. цена {price} руб"
        else:
            line = f"{name} остаток {qty} шт. цена {price} руб"
        lines.append("· " + line)

    return "\n".join(lines)


