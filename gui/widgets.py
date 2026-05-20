"""Shared widget factories for Lexi GUI pages. No page-specific state."""

import flet as ft
from .theme import C, FONT_FAMILY, MONO_FAMILY


def mk_field(val, readonly=True):
    return ft.TextField(value=val, read_only=readonly, bgcolor=C["bg_input"],
                        border_color=C["border"], border_radius=4, dense=True,
                        text_size=13, color=C["text_body"])


def mk_dropdown(value, options):
    return ft.Dropdown(
        value=value, options=[ft.dropdown.Option(o) for o in options],
        bgcolor=C["bg_input"], border_color=C["border"], border_radius=4,
        dense=True, text_size=13, color=C["text_body"])


def mk_card(title, body):
    return ft.Container(
        content=ft.Column([ft.Text(title, size=12, weight=ft.FontWeight.W_600, color=C["text_dim"]), body], spacing=8),
        padding=ft.Padding(20, 16, 20, 16), bgcolor=C["bg_card"],
        border=ft.Border.all(1, C["border"]), border_radius=6)


def mk_form_row(label, field, on_browse):
    return ft.Row([
        ft.Text(label, width=70, size=13, color=C["text_muted"]),
        field,
        ft.OutlinedButton(content="浏览", on_click=on_browse,
                          style=ft.ButtonStyle(color=C["text_muted"], side=ft.BorderSide(1, C["border"]),
                                               shape=ft.RoundedRectangleBorder(radius=4),
                                               text_style=ft.TextStyle(size=12))),
    ], spacing=10)


def mk_filled_btn(label, on_click, bg, fg, size=13):
    return ft.FilledButton(
        content=label, on_click=on_click,
        style=ft.ButtonStyle(bgcolor=bg, color=fg,
                             shape=ft.RoundedRectangleBorder(radius=4),
                             padding=ft.Padding(20, 12, 20, 12) if size > 13 else ft.Padding(12, 8, 12, 8),
                             text_style=ft.TextStyle(size=size, weight=ft.FontWeight.W_600 if size > 13 else ft.FontWeight.W_500)))


def mk_outline_btn(label, on_click, fg):
    return ft.OutlinedButton(
        content=label, on_click=on_click,
        style=ft.ButtonStyle(color=fg, side=ft.BorderSide(1, fg),
                             shape=ft.RoundedRectangleBorder(radius=4),
                             text_style=ft.TextStyle(size=12)))


def mk_chip(label, active, on_toggle):
    return ft.Container(
        content=ft.Text(label, size=12, weight=ft.FontWeight.W_500,
                        color=C["text_primary"] if active else C["text_muted"]),
        padding=ft.Padding(6, 14, 6, 14), border_radius=14,
        bgcolor=C["accent"] if active else C["bg_input"],
        border=ft.Border.all(1, C["accent"] if active else C["border"]),
        data={"active": active, "label": label},
        on_click=on_toggle)
