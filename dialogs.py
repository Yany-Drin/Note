import flet as ft
from typing import Any, Callable

from theme import (
    LIGHT_PINK, PRIMARY_ROSE, BORDER_PINK, TEXT_PRIMARY, TEXT_SECONDARY,
)
from models import AppState


def show_pinyin_picker(
    page: ft.Page,
    word: str,
    lang: str,
    scheme: str,
    options: list[str],
    current_idx: int,
    on_selected: Callable[[int], None],
) -> None:
    def make_select(pi: int):
        def on_click(e) -> None:
            on_selected(pi)
            page.pop_dialog()
        return on_click

    items: list[ft.Control] = []
    for pi, py in enumerate(options):
        selected = (pi == current_idx)
        items.append(
            ft.Container(
                content=ft.Row(
                    [
                        ft.Text(
                            py, size=18,
                            color=PRIMARY_ROSE if selected else TEXT_PRIMARY,
                            weight=ft.FontWeight.W_600 if selected else ft.FontWeight.W_400,
                        ),
                        ft.Icon(ft.Icons.CHECK, size=18, color=PRIMARY_ROSE)
                        if selected else ft.Container(width=18),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                padding=ft.Padding.symmetric(horizontal=16, vertical=12),
                border_radius=10,
                bgcolor=LIGHT_PINK if selected else ft.Colors.TRANSPARENT,
                on_click=make_select(pi),
            )
        )

    page.show_dialog(
        ft.BottomSheet(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(f'{word} · {lang}・{scheme}', size=14, color=TEXT_SECONDARY),
                        ft.Column(items, spacing=4),
                    ],
                    spacing=12, tight=True,
                ),
                padding=20,
            ),
        )
    )


ITEM_HEIGHT: int = 48


def open_scheme_dialog(
    page: ft.Page,
    state: AppState,
    available: list[tuple[str, str]],
    on_change: Callable[[], None],
) -> None:
    selected = state.schemes

    def label(pair: tuple[str, str]) -> str:
        return f'{pair[0]}・{pair[1]}'

    def build_item(pair: tuple[str, str], is_selected: bool, top: int):
        icon = ft.Icon(
            ft.Icons.CHECK_CIRCLE if is_selected else ft.Icons.RADIO_BUTTON_UNCHECKED,
            size=18,
            color=PRIMARY_ROSE if is_selected else BORDER_PINK,
        )
        text = ft.Text(
            label(pair), size=15,
            color=TEXT_PRIMARY if is_selected else TEXT_SECONDARY,
            weight=ft.FontWeight.W_500 if is_selected else ft.FontWeight.W_400,
        )
        c = ft.Container(
            content=ft.Row([icon, text], spacing=8,
                           vertical_alignment=ft.CrossAxisAlignment.CENTER),
            top=top, left=0, right=0,
            height=ITEM_HEIGHT - 6,
            padding=ft.Padding.symmetric(horizontal=12),
            bgcolor=LIGHT_PINK if is_selected else ft.Colors.with_opacity(0.3, LIGHT_PINK),
            border_radius=10,
            on_click=lambda e, p=pair: toggle(p),
            animate_position=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
        )
        return c, icon, text

    def positions() -> dict[tuple[str, str], int]:
        ordered = list(selected) + [p for p in available if p not in selected]
        return {p: i * ITEM_HEIGHT for i, p in enumerate(ordered)}

    items: dict[tuple[str, str], tuple] = {}

    def refresh() -> None:
        pos = positions()
        for pair, (c, icon, text) in items.items():
            c.top = pos[pair]
            if pair in selected:
                icon.icon = ft.Icons.CHECK_CIRCLE
                icon.color = PRIMARY_ROSE
                text.color = TEXT_PRIMARY
                text.weight = ft.FontWeight.W_500
                c.bgcolor = LIGHT_PINK
            else:
                icon.icon = ft.Icons.RADIO_BUTTON_UNCHECKED
                icon.color = BORDER_PINK
                text.color = TEXT_SECONDARY
                text.weight = ft.FontWeight.W_400
                c.bgcolor = ft.Colors.with_opacity(0.3, LIGHT_PINK)
        page.update()

    def toggle(pair: tuple[str, str]) -> None:
        if pair in selected:
            if len(selected) <= 1:
                return
            selected.remove(pair)
        else:
            selected.append(pair)
        on_change()
        refresh()

    pos = positions()
    stack_children = []
    for pair in available:
        c, icon, text = build_item(pair, pair in selected, pos[pair])
        items[pair] = (c, icon, text)
        stack_children.append(c)

    stack = ft.Stack(
        controls=stack_children,
        height=len(available) * ITEM_HEIGHT,
    )

    # 列表最大高度：方案少時自適應，方案多時限制並滾動
    list_height: int = min(len(available) * ITEM_HEIGHT, 320)
    list_container = ft.Container(
        content=ft.Column(
            [stack],
            scroll=ft.ScrollMode.AUTO,
            tight=True,
        ),
        height=list_height,
    )

    def load_schemes(e) -> None:
        print('載入方案文件')

    page.show_dialog(
        ft.AlertDialog(
            title=ft.Text('設置方案', color=PRIMARY_ROSE, size=18, weight=ft.FontWeight.W_600),
            content=ft.Container(
                width=340,
                content=ft.Column(
                    [
                        ft.Button(
                            '載入方案', icon=ft.Icons.UPLOAD_FILE, on_click=load_schemes,
                            style=ft.ButtonStyle(
                                bgcolor=LIGHT_PINK, color=PRIMARY_ROSE,
                                shape=ft.RoundedRectangleBorder(radius=10),
                                padding=ft.Padding.symmetric(horizontal=16, vertical=10),
                            ),
                        ),
                        ft.Divider(height=1, color=BORDER_PINK),
                        list_container,
                    ],
                    spacing=8, tight=True,
                ),
            ),
        )
    )


def open_copy_dialog(
    page: ft.Page,
    state: AppState,
    input_field: ft.TextField,
    compute_variants: Callable[[str], list[tuple[str, str]]],
) -> None:
    current_mode: list[str] = ['無']

    def make_item(label: str, value: str) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(label, size=13, color=PRIMARY_ROSE, weight=ft.FontWeight.W_600),
                    ft.Text(value if value else '（空）', size=14, color=TEXT_PRIMARY, selectable=True),
                ],
                spacing=4, tight=True,
            ),
            padding=ft.Padding.symmetric(horizontal=16, vertical=12),
            border_radius=10,
            bgcolor=LIGHT_PINK,
            action=ft.CopyToClipboard(value),
            on_click=lambda e: page.pop_dialog(),
        )

    column = ft.Column(spacing=8, tight=True)

    def rebuild() -> None:
        column.controls.clear()
        for label, value in compute_variants(current_mode[0]):
            column.controls.append(make_item(label, value))
        page.update()

    def on_convert(e) -> None:
        current_mode[0] = dropdown.value or '無'
        rebuild()

    dropdown = ft.Dropdown(
        options=[ft.DropdownOption(key=k, text=k) for k in ['無', '正體', '繁體', '簡體']],
        value=current_mode[0],
        width=110,
        text_size=13,
        content_padding=ft.Padding.symmetric(horizontal=10, vertical=6),
        border=ft.OutlineInputBorder(
            border_radius=8, side=ft.BorderSide(color=BORDER_PINK),
        ),
        on_select=on_convert,
    )

    rebuild()

    # 內容區最大高度 360，超出滾動
    content_container = ft.Container(
        width=420,
        height=360,
        content=ft.Column(
            [column],
            scroll=ft.ScrollMode.AUTO,
        ),
    )

    page.show_dialog(
        ft.AlertDialog(
            title=ft.Row(
                [
                    ft.Text('複製文本', color=PRIMARY_ROSE, size=18, weight=ft.FontWeight.W_600),
                    ft.Container(expand=True),
                    ft.Text('轉換：', size=13, color=TEXT_SECONDARY),
                    dropdown,
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            title_padding=ft.Padding.symmetric(horizontal=20, vertical=12),
            content=content_container,
            actions=[ft.TextButton('取消', on_click=lambda e: page.pop_dialog())],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    )