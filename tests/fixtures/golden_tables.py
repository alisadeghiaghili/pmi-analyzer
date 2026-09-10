"""Golden table snapshots captured from live ICCIMA Shamkh PDFs (2026).

Each fixture stores the raw `pdfplumber.extract_tables()` shape that the
parser must survive, plus the expected public metrics for the report month.

These are hand-curated from page-level dumps of:
  - khordad 1405
  - tir 1405
  - ordibehesht 1405
  - bahman 1404
  - farvardin 1405
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

# --- khordad 1405: summary table (page 4) ---------------------------------
# RTL layout: label in col 4, four comparison columns, multi-line cells.
KHORDAD_SUMMARY_TABLE: List[List[Optional[str]]] = [
    [
        "1405 دادرخ هب یهتنم هام ود رد داصتقا لک )خماش( دیر",
        "",
        "",
        "",
        "",
        "",
    ],
    [
        "هدش یلص ف١ل ٤ید٠عت٥ دادر",
        "",
        "خ هب يههدتنشمن هیالمص وفدل یرددعت داصتقا",
        "",
        "لك (خماش) ديرخ ناريدم صخاش :١ لودج\nصخاش",
        "",
    ],
    [
        "140 5ه دداشدرخ يل",
        "ص1ف4ل 05ي دتعشتهبیدرا",
        "1405 دادر خ ه د",
        "ش1ن4 ي05ل صتشفل هبيیددرعات",
        "",
        "",
    ],
    [
        "45.9\n١٤٠٥ دادرخ",
        "ت شهبيدرا\n41.8",
        "45.7\n١٤٠٥ داد",
        "ت ش\n48.8\nرخ",
        "هبيدرا صخاش\nداصتقا لک خماش",
        "خماش\nوت نازيم\nیلصا یاه هفلوم\nس نازيم ياههفل\nا تعرس",
    ],
    ["46.8", "١٤٠٥\n43.8", "47.9", "١٤\n54.8", "٠٥\nتمدخ هئارا ای لوصحم دیلوت نازیم", ""],
    [
        "45.9\n41.4\n46.8",
        "41.8\n40.4\n43.8",
        "45.7\n40.6\n47.9",
        "48\n49.4\n54",
        ".8 د اصتقا لك\nنایرتشم دیدج تاشرافس نازیم\n.8 ت مدخ ",
        "",
    ],
    ["4511..42", "424.07.4", "50.040.6", "45.7 49", ".4 شراف سن لايیروتحشتوم مدايجدجنا تتعاشرسراف", ""],
    ["51.2\n44.4", "42.7\n41.7", "50.0\n43.7", "45\n46.8", ".7 ش رافس ليوحتو ماجن\nهدش یرادیرخ مزاول ای هیلوا د", ""],
]

# --- farvardin 1405: industry cross-tab (page 9) ---------------------------
# Label last, industries as value columns. Aggregate is NOT a value column.
FARVARDIN_INDUSTRY_TABLE: List[List[Optional[str]]] = [
    [
        "1405 نیدرورف ،هدش یلصف لیدعت ،تعنص یاهش ",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
    ],
    [
        "سایر\nصنایع",
        "وسایل\nنقلیه\nو\nقطعات\nوابسته",
        "ماشین\nسازی\nو\nلوازم\nخانگی",
        "صنایع\nفلزی",
        "صنایع\nکانی\nغیر\nفلزی",
        "صنایع\nلاستیک\nو\nپلاستیک",
        "صنایع\nشیمیایی",
        "صنایع\nفراورده\nهای\nنفت\nو\nگاز",
        "چوب،\nکاغذ\nو\nمبلمان",
        "پوشاک\nو\nچرم",
        "صنایع\nنساجی",
        "صنایع\nغذایی",
        "صخاش",
    ],
    [
        "31.8",
        "41.6",
        "40.6",
        "29.2",
        "41.5",
        "43.2",
        "35.3",
        "39.4",
        "46.3",
        "30.5",
        "41.8",
        "37.4",
        "تیلاعف لک خماش",
    ],
    [
        "42.7",
        "47.0",
        "51.3",
        "29.2",
        "47.6",
        "43.9",
        "33.4",
        "40.3",
        "40.2",
        "33.9",
        "52.0",
        "38.9",
        "تلاوصحم دیلوت رادقم",
    ],
]

# Clean LTR summary used by existing unit-style expectations.
CLEAN_SUMMARY_TABLE: List[List[Optional[str]]] = [
    ["میزان تولید محصول", "45.0", "48.0", "50.0"],
    ["میزان سفارشات جدید مشتریان", "42.0", "44.0", "46.0"],
    ["شاخص کل اقتصاد", "44.5", "46.0", "45.9"],
]

GOLDEN_CASES: Dict[str, Any] = {
    "khordad-1405": {
        "expected_month": "1405-03",
        "title_hints": ["خرداد", "1405"],
        "summary_table": KHORDAD_SUMMARY_TABLE,
    },
    "farvardin-1405": {
        "expected_month": "1405-01",
        "title_hints": ["فروردین", "1405"],
        "industry_table": FARVARDIN_INDUSTRY_TABLE,
    },
}
