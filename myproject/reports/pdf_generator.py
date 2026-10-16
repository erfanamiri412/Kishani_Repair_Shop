import base64
import math
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe


class PDFReportGenerator:
    template_name = "reports/report_print.html"

    COLORS = (
        "#001973",
        "#1976d2",
        "#16836b",
        "#c8a45d",
        "#7c4dff",
        "#d95d39",
        "#64748b",
        "#0f766e",
        "#9b4d96",
    )

    def __init__(self):
        self.static_dir = Path(settings.BASE_DIR) / "static"

    @staticmethod
    def _number(value):
        try:
            if value is None:
                return 0.0
            return float(value)
        except (TypeError, ValueError, OverflowError):
            return 0.0

    @staticmethod
    def _safe_text(value, limit=48):
        if value is None or value == "":
            return "—"
        return escape(str(value).strip()[:limit])

    @staticmethod
    def _wrap_label(value, max_chars=22, max_lines=2):
        raw = str(value or "—").strip()
        words = raw.split()
        lines = []
        current = ""

        for word in words:
            if len(word) > max_chars:
                word = word[:max_chars - 1] + "…"

            candidate = f"{current} {word}".strip()

            if current and len(candidate) > max_chars:
                lines.append(current)
                current = word
            else:
                current = candidate

        if current:
            lines.append(current)

        lines = lines or ["—"]

        if len(lines) > max_lines:
            lines = lines[:max_lines]
            lines[-1] = lines[-1][:max_chars - 1].rstrip() + "…"

        return [escape(line) for line in lines]

    @staticmethod
    def _tick(value):
        value = PDFReportGenerator._number(value)

        if abs(value) >= 1_000_000:
            return f"{value / 1_000_000:,.1f}م"

        if abs(value) >= 1_000:
            return f"{value / 1_000:,.0f}هزار"

        return f"{value:,.0f}"

    @staticmethod
    def _find_browser():
        candidates = [
            os.environ.get("BROWSER", "").strip(),
            shutil.which("chrome"),
            shutil.which("msedge"),
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        ]

        local_app_data = os.environ.get("LOCALAPPDATA")

        if local_app_data:
            candidates.extend([
                os.path.join(
                    local_app_data,
                    "Google",
                    "Chrome",
                    "Application",
                    "chrome.exe",
                ),
                os.path.join(
                    local_app_data,
                    "Microsoft",
                    "Edge",
                    "Application",
                    "msedge.exe",
                ),
            ])

        seen = set()

        for candidate in candidates:
            if not candidate:
                continue

            candidate = os.path.abspath(candidate)
            key = candidate.lower()

            if key in seen:
                continue

            seen.add(key)

            if os.path.isfile(candidate):
                return candidate

        return None

    def _empty_chart(
        self,
        title,
        detail="برای این دوره داده‌ای از منبع مربوط ثبت نشده است.",
    ):
        return (
            '<div class="report-chart-empty">'
            f'<strong>{escape(str(title))}</strong>'
            f'<span>{escape(str(detail))}</span>'
            "</div>"
        )

    @staticmethod
    def _svg_title(title, width, y=27):
        """
        تیتر نمودار را با جهت فارسی و تراز مناسب SVG تولید می‌کند.
        نقطه شروع متن فارسی در سمت راست قرار می‌گیرد.
        """
        safe_title = escape(str(title or ""))
        x = width - 14

        return (
            f'<text x="{x}" y="{y}" '
            'text-anchor="start" '
            'direction="rtl" '
            'unicode-bidi="plaintext" '
            'class="chart-title">'
            f"{safe_title}"
            "</text>"
        )

    def _horizontal_bar_chart(
        self,
        items,
        label_key,
        value_key,
        title,
        value_format="number",
        limit=10,
    ):
        rows = [
            dict(row)
            for row in (items or [])
            if isinstance(row, dict)
        ][:limit]

        if not rows:
            return self._empty_chart(title)

        values = [
            self._number(row.get(value_key, 0))
            for row in rows
        ]

        max_value = max(
            [max(value, 0) for value in values] or [0]
        ) or 1

        width = 620
        row_height = 46
        top = 54
        bottom = 30
        height = top + len(rows) * row_height + bottom

        plot_left = 18
        plot_right = 432
        plot_width = plot_right - plot_left

        svg = [
            (
                f'<svg class="report-chart-svg" '
                f'viewBox="0 0 {width} {height}" '
                f'role="img" aria-label="{escape(title)}">'
            ),
            self._svg_title(title, width),
            (
                f'<text x="{plot_left}" y="42" '
                'class="chart-unit">'
                f'{"مبالغ به تومان" if value_format == "money" else "مقدار"}'
                "</text>"
            ),
        ]

        for idx in range(5):
            tick = max_value * idx / 4
            x = plot_left + plot_width * idx / 4

            svg.append(
                f'<line x1="{x:.1f}" y1="{top - 6}" '
                f'x2="{x:.1f}" y2="{height - bottom + 1}" '
                'class="chart-grid"/>'
            )

            tick_text = (
                self._tick(tick)
                if value_format == "money"
                else f"{tick:,.0f}"
            )

            svg.append(
                f'<text x="{x:.1f}" y="{height - 6}" '
                'text-anchor="middle" '
                'direction="ltr" '
                'unicode-bidi="bidi-override" '
                'class="chart-y-label">'
                f"{escape(tick_text)}"
                "</text>"
            )

        for index, (row, value) in enumerate(zip(rows, values)):
            y = top + index * row_height

            bar_width = (
                plot_width * max(value, 0) / max_value
            )
            color = self.COLORS[index % len(self.COLORS)]

            label_lines = self._wrap_label(
                row.get(label_key, "—"),
                max_chars=19,
                max_lines=2,
            )

            label_y = (
                y + 17
                if len(label_lines) == 1
                else y + 11
            )

            tspans = "".join(
                (
                    f'<tspan x="{width - 10}" '
                    f'dy="{0 if line_index == 0 else 15}">'
                    f"{line}</tspan>"
                )
                for line_index, line in enumerate(label_lines)
            )

            svg.append(
                f'<text x="{width - 10}" y="{label_y}" '
                'text-anchor="end" '
                'direction="rtl" '
                'unicode-bidi="plaintext" '
                'class="chart-label">'
                f"{tspans}"
                "</text>"
            )

            svg.append(
                f'<rect x="{plot_left}" y="{y + 10}" '
                f'width="{bar_width:.1f}" height="24" '
                f'rx="4" fill="{color}"/>'
            )

            value_text = (
                self._tick(value)
                if value_format == "money"
                else f"{value:,.0f}"
            )

            estimated_text_width = max(
                25,
                len(value_text) * 8,
            )

            if bar_width >= estimated_text_width + 12:
                text_x = plot_left + bar_width - 8
                anchor = "end"
                style = ' style="fill:#fff"'
            else:
                text_x = min(
                    plot_left + bar_width + 6,
                    plot_right - 3,
                )
                anchor = "start"
                style = ""

            svg.append(
                f'<text x="{text_x:.1f}" y="{y + 27}" '
                f'text-anchor="{anchor}" '
                'direction="ltr" '
                'unicode-bidi="bidi-override" '
                'class="chart-bar-value"'
                f'{style}>'
                f"{escape(value_text)}"
                "</text>"
            )

        svg.append("</svg>")
        return "".join(svg)

    def _grouped_bar_chart(self, items, label_key, series, title):
        rows = [
            dict(row)
            for row in (items or [])
            if isinstance(row, dict)
        ]

        if not rows:
            return self._empty_chart(title)

        width, height = 620, 350
        left, right, top, bottom = 48, 16, 58, 76

        plot_width = width - left - right
        plot_height = height - top - bottom

        values = [
            max(0, self._number(row.get(key, 0)))
            for row in rows
            for _, key in series
        ]

        max_value = max(values or [0]) or 1

        slot = plot_width / max(len(rows), 1)
        group_width = min(56, slot * 0.72)
        bar_width = group_width / max(len(series), 1)
        baseline = height - bottom

        svg = [
            (
                f'<svg class="report-chart-svg" '
                f'viewBox="0 0 {width} {height}" '
                f'role="img" aria-label="{escape(title)}">'
            ),
            self._svg_title(title, width),
        ]

        for tick_idx in range(5):
            tick = max_value * tick_idx / 4
            y = baseline - tick / max_value * plot_height

            svg.append(
                f'<line x1="{left}" y1="{y:.1f}" '
                f'x2="{width - right}" y2="{y:.1f}" '
                'class="chart-grid"/>'
            )

            tick_text = self._tick(tick)

            svg.append(
                f'<text x="{left - 8}" y="{y + 4:.1f}" '
                'text-anchor="end" '
                'direction="ltr" '
                'unicode-bidi="bidi-override" '
                'class="chart-y-label">'
                f"{escape(tick_text)}"
                "</text>"
            )

        for idx, row in enumerate(rows):
            group_x = (
                left
                + idx * slot
                + (slot - group_width) / 2
            )

            for series_idx, (series_label, key) in enumerate(series):
                value = max(
                    0,
                    self._number(row.get(key, 0)),
                )

                bar_height = value / max_value * plot_height
                x = group_x + series_idx * bar_width
                y = baseline - bar_height
                color = self.COLORS[
                    series_idx % len(self.COLORS)
                ]

                svg.append(
                    f'<rect x="{x:.1f}" y="{y:.1f}" '
                    f'width="{max(bar_width - 3, 2):.1f}" '
                    f'height="{bar_height:.1f}" '
                    f'rx="3" fill="{color}"/>'
                )

            label = self._safe_text(
                row.get(label_key, "—"),
                12,
            )

            cx = left + idx * slot + slot / 2

            svg.append(
                f'<text x="{cx:.1f}" y="{baseline + 20}" '
                'text-anchor="middle" '
                'class="chart-label">'
                f"{label}"
                "</text>"
            )

        legend_y = height - 15

        item_width = min(
            280,
            (width - 32) / max(len(series), 1),
        )

        total_legend_width = len(series) * item_width
        start_x = (width - total_legend_width) / 2

        for idx, (name, _) in enumerate(series):
            x = start_x + idx * item_width
            color = self.COLORS[idx % len(self.COLORS)]

            svg.append(
                f'<rect x="{x:.1f}" y="{legend_y - 10}" '
                'width="12" height="12" rx="2" '
                f'fill="{color}"/>'
            )

            svg.append(
                f'<text x="{x + 18:.1f}" y="{legend_y}" '
                'class="chart-legend">'
                f"{escape(name)}"
                "</text>"
            )

        svg.append("</svg>")
        return "".join(svg)

    def _signed_bar_chart(self, items, label_key, value_key, title):
        rows = [
            dict(row)
            for row in (items or [])
            if isinstance(row, dict)
        ]

        if not rows:
            return self._empty_chart(title)

        values = [
            self._number(row.get(value_key, 0))
            for row in rows
        ]

        max_abs = max(
            [abs(value) for value in values] or [0]
        ) or 1

        width = 620
        row_h = 44
        top = 52
        bottom = 24
        height = top + row_h * len(rows) + bottom

        left, right = 18, 190
        plot_width = width - left - right

        min_value = min(values, default=0)
        max_value = max(values, default=0)

        if min_value < 0 < max_value:
            center = (
                left
                + plot_width
                * (-min_value)
                / (max_value - min_value)
            )
        elif min_value >= 0:
            center = left
        elif max_value <= 0:
            center = left + plot_width
        else:
            center = left + plot_width / 2

        svg = [
            (
                f'<svg class="report-chart-svg" '
                f'viewBox="0 0 {width} {height}" '
                f'role="img" aria-label="{escape(title)}">'
            ),
            self._svg_title(title, width),
        ]

        svg.append(
            f'<line x1="{center:.1f}" y1="{top - 5}" '
            f'x2="{center:.1f}" y2="{height - bottom + 1}" '
            'class="chart-axis"/>'
        )

        for i, (row, value) in enumerate(zip(rows, values)):
            y = top + i * row_h

            if min_value < 0 < max_value:
                if value < 0:
                    length = (
                        abs(value)
                        / abs(min_value)
                        * (center - left)
                    )
                    x = center - length
                else:
                    length = (
                        value
                        / max_value
                        * (left + plot_width - center)
                    )
                    x = center
            elif max_value <= 0:
                length = (
                    abs(value)
                    / max(abs(min_value), 1)
                    * plot_width
                )
                x = center - length
            else:
                length = (
                    value
                    / max(max_value, 1)
                    * plot_width
                )
                x = center

            color = "#16836b" if value >= 0 else "#d95d39"

            svg.append(
                f'<rect x="{x:.1f}" y="{y + 3}" '
                f'width="{length:.1f}" height="24" '
                f'rx="3" fill="{color}"/>'
            )

            label_lines = self._wrap_label(
                row.get(label_key, "—"),
                max_chars=22,
                max_lines=2,
            )

            label_y = (
                y + 18
                if len(label_lines) == 1
                else y + 12
            )

            tspans = "".join(
                (
                    f'<tspan x="{width - 10}" '
                    f'dy="{0 if line_index == 0 else 15}">'
                    f"{line}</tspan>"
                )
                for line_index, line in enumerate(label_lines)
            )

            svg.append(
                f'<text x="{width - 10}" y="{label_y}" '
                'text-anchor="end" '
                'direction="rtl" '
                'unicode-bidi="plaintext" '
                'class="chart-label">'
                f"{tspans}"
                "</text>"
            )

            value_text = self._tick(value)
            text_width = max(24, len(value_text) * 7)

            if length > text_width + 14:
                text_x = x + length - 8
                anchor = "end"
                style = ' style="fill:#fff"'
            elif value < 0:
                text_x = min(
                    center - 3,
                    x + length + 7,
                )
                anchor = "end"
                style = ""
            else:
                text_x = min(
                    width - right - 2,
                    x + length + 7,
                )
                anchor = "start"
                style = ""

            svg.append(
                f'<text x="{text_x:.1f}" y="{y + 20}" '
                f'text-anchor="{anchor}" '
                'direction="ltr" '
                'unicode-bidi="bidi-override" '
                'class="chart-bar-value"'
                f'{style}>'
                f"{escape(value_text)}"
                "</text>"
            )

        svg.append("</svg>")
        return "".join(svg)

    def _donut_chart(self, items, label_key, value_key, title):
        rows = [
            dict(row)
            for row in (items or [])
            if self._number(row.get(value_key, 0)) > 0
        ]

        if not rows:
            return self._empty_chart(title)

        rows.sort(
            key=lambda row: self._number(
                row.get(value_key, 0)
            ),
            reverse=True,
        )

        if len(rows) > 6:
            rows = rows[:6] + [{
                label_key: "سایر",
                value_key: sum(
                    self._number(row.get(value_key, 0))
                    for row in rows[6:]
                ),
            }]

        total = sum(
            self._number(row.get(value_key, 0))
            for row in rows
        )

        if total <= 0:
            return self._empty_chart(title)

        width, height = 620, 340
        cx, cy, radius = 118, 184, 96
        circumference = 2 * math.pi * radius

        svg = [
            (
                f'<svg class="report-chart-svg" '
                f'viewBox="0 0 {width} {height}" '
                f'role="img" aria-label="{escape(title)}">'
            ),
            self._svg_title(title, width),
            (
                f'<circle cx="{cx}" cy="{cy}" r="{radius}" '
                'fill="none" stroke="#e8edf4" '
                'stroke-width="34"/>'
            ),
        ]

        offset = 0.0

        for idx, row in enumerate(rows):
            value = self._number(row.get(value_key, 0))
            arc = circumference * value / total
            color = self.COLORS[idx % len(self.COLORS)]

            svg.append(
                f'<circle cx="{cx}" cy="{cy}" r="{radius}" '
                'fill="none" '
                f'stroke="{color}" '
                'stroke-width="34" '
                f'stroke-dasharray="{arc:.2f} '
                f'{circumference - arc:.2f}" '
                f'stroke-dashoffset="{-offset:.2f}" '
                f'transform="rotate(-90 {cx} {cy})"/>'
            )

            offset += arc
            legend_y = 62 + idx * 37

            label_lines = self._wrap_label(
                row.get(label_key, "—"),
                max_chars=20,
                max_lines=1,
            )

            label = label_lines[0]
            percent = value / total * 100

            svg.append(
                f'<rect x="{width - 250}" '
                f'y="{legend_y - 10}" '
                'width="12" height="12" rx="3" '
                f'fill="{color}"/>'
            )

            svg.append(
                f'<text x="{width - 230}" y="{legend_y}" '
                'class="chart-legend" '
                'direction="rtl">'
                f"{label}"
                "</text>"
            )

            svg.append(
                f'<text x="{width - 230}" y="{legend_y + 16}" '
                'direction="ltr" '
                'unicode-bidi="bidi-override" '
                'class="chart-bar-value">'
                f'{percent:.1f}% · {escape(self._tick(value))}'
                "</text>"
            )

        svg.append(
            f'<text x="{cx}" y="{cy - 3}" '
            'text-anchor="middle" '
            'direction="ltr" '
            'unicode-bidi="bidi-override" '
            'class="chart-donut-total">'
            f"{escape(self._tick(total))}"
            "</text>"
        )

        svg.append(
            f'<text x="{cx}" y="{cy + 21}" '
            'text-anchor="middle" '
            'class="chart-label">'
            "جمع"
            "</text>"
        )

        svg.append("</svg>")
        return "".join(svg)

    def _build_chart_svgs(self, report_data):
        charts = report_data.get("charts", {}) or {}
        report_type = report_data.get("report_type", "monthly")

        cashflow_items = (
            charts.get("monthly_cashflow", [])
            if report_type == "yearly"
            else charts.get("weekly_cashflow", [])
        )

        customer_rows = []

        for row in charts.get("top_customers", []) or []:
            customer_rows.append({
                "customer": row.get("customer", "—"),
                "count": row.get(
                    "frequency_count",
                    row.get(
                        "visit_count",
                        row.get("repair_count", 0),
                    ),
                ),
            })

        supplier_rows = charts.get("supplier_purchases", []) or []

        return {
            "cashflow": self._grouped_bar_chart(
                cashflow_items,
                "label",
                [
                    ("دریافتی + درآمد روزانه", "income"),
                    ("هزینه روزانه + حقوق", "expense"),
                ],
                "مقایسه درآمد و هزینه ثبت‌شده",
            ),
            "net": self._signed_bar_chart(
                cashflow_items,
                "label",
                "net",
                "خالص جریان نقدی ثبت‌شده (تومان)",
            ),
            "revenue_mix": self._donut_chart(
                charts.get("revenue_mix", []),
                "label",
                "value",
                "ترکیب درآمد فاکتور و درآمدهای دیگر",
            ),
            "services": self._horizontal_bar_chart(
                charts.get("service_frequency", []),
                "service_title",
                "count",
                "پرتکرارترین خدمات",
                "number",
                6,
            ),
            "service_revenue": self._horizontal_bar_chart(
                charts.get("service_frequency", []),
                "service_title",
                "amount",
                "درآمد ثبت‌شده خدمات",
                "money",
                6,
            ),
            "mechanics": self._horizontal_bar_chart(
                charts.get("mechanic_performance", []),
                "employee",
                "labor_income",
                "اجرت فاکتورشده به نام هر تعمیرکار",
                "money",
                6,
            ),
            "mechanic_hours": self._horizontal_bar_chart(
                charts.get("mechanic_hours", []),
                "employee",
                "hours",
                "ساعات حضور ثبت‌شده پرسنل",
                "number",
                6,
            ),
            "parts": self._horizontal_bar_chart(
                charts.get("top_parts", []),
                "part",
                "quantity",
                "پرتکرارترین قطعات ثبت‌شده",
                "number",
                6,
            ),
            "vehicles": self._horizontal_bar_chart(
                charts.get("vehicle_popularity", []),
                "vehicle",
                "chart_count",
                "خودروهای پرتکرار بر اساس کار ثبت‌شده",
                "number",
                6,
            ),
            "customers": self._horizontal_bar_chart(
                customer_rows,
                "customer",
                "count",
                "مشتریان پرتکرار",
                "number",
                6,
            ),
            "expenses": self._horizontal_bar_chart(
                charts.get("expense_breakdown", []),
                "category",
                "amount",
                "بیشترین هزینه‌های ثبت‌شده",
                "money",
                6,
            ),
            "suppliers": self._horizontal_bar_chart(
                supplier_rows,
                "supplier",
                "amount",
                "تأمین‌کنندگان بر اساس قطعات ثبت‌شده برای تعمیر",
                "money",
                6,
            ),
        }

    def build_context(self, report_data, auto_print=False):
        report_data = dict(report_data or {})

        css_path = (
            self.static_dir
            / "assets"
            / "css"
            / "invoice-print.css"
        )

        invoice_css = (
            css_path.read_text(encoding="utf-8")
            if css_path.exists()
            else ""
        )

        logo_path = (
            self.static_dir
            / "assets"
            / "img"
            / "logo01.png"
        )

        logo_src = ""

        if logo_path.exists():
            encoded = base64.b64encode(
                logo_path.read_bytes()
            ).decode("ascii")

            logo_src = "data:image/png;base64," + encoded

        report_type = report_data.get("report_type", "monthly")

        if report_type == "yearly":
            report_title = (
                report_data.get("title")
                or f"گزارش جامع سالانه - {report_data.get('year', '')}"
            )
        elif report_type == "custom":
            report_title = (
                report_data.get("title")
                or "گزارش مدیریتی سفارشی"
            )
        else:
            report_title = (
                report_data.get("title")
                or (
                    "گزارش جامع ماهانه - "
                    f"{report_data.get('month_label', '')}"
                )
            )

        report_data["chart_svgs"] = {
            key: mark_safe(value)
            for key, value in self._build_chart_svgs(
                report_data
            ).items()
        }

        financial = report_data.get("financial", {}) or {}
        inventory = report_data.get("inventory", {}) or {}

        report_data["display"] = {
            "financial": {
                key: self._currency(financial.get(key, 0))
                for key in (
                    "total_income",
                    "cash_collected",
                    "cash_income",
                    "invoiced_revenue",
                    "daily_expenses",
                    "salary_paid",
                    "parts_cost",
                    "cash_outflow",
                    "management_profit",
                    "receivables",
                    "average_invoice",
                    "cash_surplus",
                )
            },
            "inventory": {
                key: self._currency(inventory.get(key, 0))
                for key in (
                    "purchase_value",
                    "sale_value",
                    "potential_profit",
                    "purchased_part_cost",
                )
            },
            "ml": {
                "next_month_income_prediction": self._currency(
                    (
                        report_data.get("ml", {})
                        or {}
                    ).get("next_month_income_prediction", 0)
                ),
            },
        }

        return {
            "report": report_data,
            "report_type": report_type,
            "report_title": report_title,
            "logo_src": logo_src,
            "report_css": mark_safe(invoice_css),
            "auto_print": auto_print,
        }

    @staticmethod
    def _currency(value):
        number = PDFReportGenerator._number(value)
        return f"{number:,.0f} تومان"

    def render_html(self, report_data):
        return render_to_string(
            self.template_name,
            self.build_context(report_data),
        )

    def generate(self, report_data):
        browser_path = self._find_browser()

        if not browser_path:
            raise RuntimeError(
                "برای تولید خودکار PDF، مرورگر Microsoft Edge "
                "یا Google Chrome روی سیستم پیدا نشد."
            )

        html_content = self.render_html(report_data)

        with tempfile.TemporaryDirectory() as temp_dir:
            html_path = Path(temp_dir) / "report.html"
            pdf_path = Path(temp_dir) / "report.pdf"

            html_path.write_text(
                html_content,
                encoding="utf-8",
            )

            command = [
                browser_path,
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                "--disable-software-rasterizer",
                "--no-pdf-header-footer",
                f"--print-to-pdf={pdf_path}",
                f"--user-data-dir={Path(temp_dir) / 'browser-profile'}",
                html_path.as_uri(),
            ]

            result = subprocess.run(
                command,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=(
                    subprocess.CREATE_NO_WINDOW
                    if os.name == "nt"
                    else 0
                ),
            )

            if result.returncode != 0:
                error = result.stderr.decode(
                    "utf-8",
                    errors="ignore",
                ).strip()

                raise RuntimeError(
                    "تولید PDF گزارش ناموفق بود. "
                    + (
                        error
                        or "خطای نامشخص مرورگر"
                    )
                )

            if not pdf_path.exists():
                raise RuntimeError(
                    "مرورگر اجرا شد اما فایل PDF گزارش تولید نشد."
                )

            return pdf_path.read_bytes()

    def generate_monthly_report(self, report_data):
        return self.generate(report_data)

    def generate_yearly_report(self, report_data):
        return self.generate(report_data)


class ManagementReportPDFGenerator(PDFReportGenerator):
    pass