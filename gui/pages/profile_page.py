"""个人仪表盘页面 — 热力图."""

import flet as ft
from datetime import date, timedelta
from ..widgets import C


def build_profile_page(app, page: ft.Page) -> ft.Column:
    db = app.learned_db
    active_days = len(set(ws.last_reviewed for ws in db.words.values() if ws.last_reviewed))

    # ── Build heatmap ──
    today = date.today()
    weeks = 20  # Show ~5 months
    heatmap = ft.Row(spacing=3, wrap=True)

    # Collect daily review counts
    daily_counts = {}
    for ws in db.words.values():
        for ev in ws.review_log:
            d = ev.get("timestamp", "")[:10]
            if d:
                daily_counts[d] = daily_counts.get(d, 0) + 1

    max_count = max(daily_counts.values()) if daily_counts else 1

    def _color(count):
        if count == 0:
            return "#1e1f23"
        ratio = min(count / max_count, 1.0)
        if ratio < 0.25:
            return "#1a3a2a"
        elif ratio < 0.5:
            return "#2a5a3a"
        elif ratio < 0.75:
            return "#3a7a4a"
        return C["green"]

    for w in range(weeks):
        col = ft.Column(spacing=3)
        for d in range(7):
            day = today - timedelta(days=w * 7 + (6 - d))
            ds = day.isoformat()
            count = daily_counts.get(ds, 0)
            cell = ft.Container(
                width=13, height=13, border_radius=2,
                bgcolor=_color(count),
                tooltip=f"{ds}: {count} 次复习",
            )
            col.controls.append(cell)
        heatmap.controls.append(col)

    return ft.Column(spacing=0, expand=True, scroll=ft.ScrollMode.AUTO, controls=[
        ft.Container(content=ft.Row([ft.Text("个人", size=15, weight=ft.FontWeight.W_600, color=C["text_primary"]),
                                     ft.Text("v3.3", size=11, color=C["text_dim"])],
                                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                     padding=ft.Padding(24, 16, 24, 16), bgcolor=C["bg_panel"],
                     border=ft.Border.only(bottom=ft.BorderSide(1, C["border"]))),
        ft.Container(content=ft.Column([
            ft.Row([
                ft.Text(f"学习天数: {active_days}", size=14, weight=ft.FontWeight.W_600, color=C["text_primary"]),
                ft.Text(f"学习时长: {app.stats.display}", size=14, color=C["text_dim"]),
            ], spacing=16),
            ft.Text("", size=16),
            ft.Text("复习热力图", size=12, weight=ft.FontWeight.W_600, color=C["text_dim"]),
            ft.Text("", size=8),
            heatmap,
            ft.Text("", size=8),
            ft.Row([ft.Text("少", size=10, color=C["text_dim"]),
                    ft.Container(width=13, height=13, border_radius=2, bgcolor="#1e1f23"),
                    ft.Container(width=13, height=13, border_radius=2, bgcolor="#1a3a2a"),
                    ft.Container(width=13, height=13, border_radius=2, bgcolor="#2a5a3a"),
                    ft.Container(width=13, height=13, border_radius=2, bgcolor="#3a7a4a"),
                    ft.Container(width=13, height=13, border_radius=2, bgcolor=C["green"]),
                    ft.Text("多", size=10, color=C["text_dim"])], spacing=4),
        ], spacing=4), padding=ft.Padding(24, 20, 24, 24), expand=True),
    ])
