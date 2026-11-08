import math
import flet as ft
from typing import Any, Callable

from theme import (
    CARD_BG, BORDER_PINK, TEXT_PRIMARY, TEXT_SECONDARY,
    HIGHLIGHT_GREEN, HIGHLIGHT_RED, PRIMARY_ROSE, LIGHT_PINK,
)


def _is_nan(v: Any) -> bool:
    return isinstance(v, float) and math.isnan(v)


def _clean(items: Any) -> list[str]:
    if not items:
        return []
    if not isinstance(items, (list, tuple)):
        items = [items]
    return [str(v) for v in items if v is not None and not _is_nan(v) and str(v)]


def build_char_unit(
    char: str,
    schemes: list[tuple[str, str]],
    results: dict[tuple[str, str], dict[str, Any]],
    selected_idx: dict[tuple[str, str, str], int],
    show_comment: bool,
    on_pinyin_click: Callable[[str, str, str, list[str]], None],
) -> ft.Container:
    pinyin_rows: list[ft.Control] = []
    comments: list[str] = []

    for lang, scheme in schemes:
        value = results.get((lang, scheme), {}).get(char)

        if value is None or _is_nan(value):
            pinyin_rows.append(ft.Text(' ', size=12))
            continue

        if isinstance(value, dict):
            note = _clean(value.get('note'))
            comment = _clean(value.get('comment'))
        else:
            note = _clean(value)
            comment = []

        if not note:
            pinyin_rows.append(ft.Text(' ', size=12))
            continue

        key = (char, lang, scheme)
        idx = selected_idx.get(key, 0)
        if idx >= len(note):
            idx = 0
        current = note[idx]
        is_multi = len(note) > 1

        if is_multi:
            ctrl: ft.Control = ft.Container(
                content=ft.Text(current, size=12, color=HIGHLIGHT_GREEN),
                padding=ft.Padding.symmetric(horizontal=2, vertical=0),
                on_click=lambda e, c=char, l=lang, s=scheme, n=list(note): on_pinyin_click(c, l, s, n),
            )
        else:
            ctrl = ft.Text(current, size=12, color=TEXT_SECONDARY)

        pinyin_rows.append(ctrl)

        if show_comment and comment and idx < len(comment) and comment[idx]:
            comments.append(comment[idx])

    hanzi_text = ft.Text(
        char, size=28, color=TEXT_PRIMARY,
        font_family="Noto Sans Mono CJK",
        font_family_fallback=["Noto Sans Mono CJK"],
        weight=ft.FontWeight.W_500, text_align=ft.TextAlign.CENTER,
    )

    children: list[ft.Control] = []
    children.extend(pinyin_rows)
    children.append(hanzi_text)
    if comments:
        children.append(
            ft.Container(
                content=ft.Text('｜'.join(comments), size=10, color=TEXT_SECONDARY),
                padding=ft.Padding.only(top=2, bottom=2),
            )
        )

    return ft.Container(
        content=ft.Column(
            children, spacing=2,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            tight=True,
        ),
        padding=ft.Padding.symmetric(horizontal=4, vertical=6),
    )


def build_bottom_panel(
    input_field: ft.TextField,
    comment_checkbox: ft.Checkbox,
    on_settings: Callable,
    on_copy: Callable,
) -> ft.Container:
    buttons = ft.Row(
        [
            ft.Container(
                content=ft.Button(
                    '設置方案', icon=ft.Icons.SETTINGS, on_click=on_settings,
                    style=ft.ButtonStyle(
                        bgcolor=LIGHT_PINK, color=PRIMARY_ROSE,
                        shape=ft.RoundedRectangleBorder(radius=12),
                        padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                    ),
                ),
                expand=True,
            ),
            ft.Container(
                content=ft.Button(
                    '複製文本', icon=ft.Icons.COPY, on_click=on_copy,
                    style=ft.ButtonStyle(
                        bgcolor=PRIMARY_ROSE, color=ft.Colors.WHITE,
                        shape=ft.RoundedRectangleBorder(radius=12),
                        padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                    ),
                ),
                expand=True,
            ),
        ],
        spacing=12,
    )

    return ft.Container(
        content=ft.Column(
            [comment_checkbox, input_field, buttons],
            spacing=4, tight=True,
        ),
        bgcolor=CARD_BG,
        border=ft.Border.all(1, BORDER_PINK),
        border_radius=16,
        padding=ft.Padding.symmetric(horizontal=12, vertical=8),
        shadow=ft.BoxShadow(
            blur_radius=12,
            color=ft.Colors.with_opacity(0.3, PRIMARY_ROSE),
        ),
    )
