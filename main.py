import sys
import flet as ft
from typing import Any
from opencc_purepy import OpenCC

# 判断运行环境：Emscripten = 浏览器/Pyodide，其他 = 本地 Python
IS_EMSCRIPTEN = sys.platform == "emscripten"

if not IS_EMSCRIPTEN:
    import os
    os.environ['FLET_WEBSOCKET_HANDLER_ENDPOINT'] = '/note/ws'
    from fastapi import FastAPI
    import flet.fastapi as flet_fastapi

from theme import (
    BG_COLOR, CARD_BG, PRIMARY_ROSE, BORDER_PINK, TEXT_PRIMARY,
    TEXT_SECONDARY, build_theme,
)
from models import (
    AppState, discover_schemes, get_result_for_scheme,
    has_any_comment_scheme,
)
from widgets import build_char_unit, build_bottom_panel
from dialogs import show_pinyin_picker, open_scheme_dialog, open_copy_dialog

_cc_modes = {
    '正體': OpenCC('s2tw'),
    '繁體': OpenCC('s2hk'),
    '簡體': OpenCC('t2s'),
}

def convert_text(text: str, mode: str) -> str:
    cc = _cc_modes.get(mode)
    return cc.convert(text) if cc else text


async def main(page: ft.Page) -> None:
    if IS_EMSCRIPTEN:
        import micropip
        await micropip.install("jieba")

    page.title = '字音標註'
    page.bgcolor = BG_COLOR
    page.padding = ft.Padding.symmetric(horizontal=16, vertical=12)
    page.theme = build_theme()

    available = discover_schemes()
    state = AppState(schemes=available[:1] if available else [])

    annotation_row = ft.Row(
        spacing=10,
        run_spacing=24,
        wrap=True,
        vertical_alignment=ft.CrossAxisAlignment.START,  # ← 新增
    )
    annotation_card = ft.Container(
        content=ft.Column([annotation_row], scroll=ft.ScrollMode.AUTO, expand=True),
        bgcolor=CARD_BG,
        border=ft.Border.all(1, BORDER_PINK),
        border_radius=16,
        padding=ft.Padding.symmetric(horizontal=12, vertical=8),
        shadow=ft.BoxShadow(
            blur_radius=12,
            color=ft.Colors.with_opacity(0.3, PRIMARY_ROSE),
        ),
        expand=True,
    )

    input_field = ft.TextField(
        hint_text='輸入要標註的文字…',
        multiline=True, min_lines=1, max_lines=2,
        border=ft.NoInputBorder(),
        filled=False,
        cursor_color=PRIMARY_ROSE,
        content_padding=ft.Padding.symmetric(horizontal=8, vertical=6),
        text_style=ft.TextStyle(size=16, color=TEXT_PRIMARY),
        on_change=lambda e: rebuild_annotation(e.control.value),
    )

    comment_checkbox = ft.Checkbox(
        label='註解',
        value=False,
        visible=False,
        active_color=PRIMARY_ROSE,
        check_color=ft.Colors.WHITE,
        fill_color=ft.Colors.with_opacity(0.3, '#FCE4EC'),
        border_side=ft.BorderSide(1.5, BORDER_PINK),
        on_change=lambda e: on_comment_toggle(e.control.value),
    )

    def on_comment_toggle(value: bool) -> None:
        state.show_comment = value
        rebuild_annotation()

    def on_pinyin_click(char: str, lang: str, scheme: str, options: list[str]) -> None:
        key = (char, lang, scheme)
        current = state.selected_pinyin_idx.get(key, 0)

        def on_selected(pi: int) -> None:
            state.selected_pinyin_idx[key] = pi
            rebuild_annotation()

        show_pinyin_picker(page, char, lang, scheme, options, current, on_selected)

    def rebuild_annotation(input_text: str | None = None) -> None:
        text = input_text if input_text is not None else (input_field.value or '')
        annotation_row.controls.clear()

        # 註解勾選僅在選中方案含字典值時顯示
        has_comment = has_any_comment_scheme(state)
        comment_checkbox.visible = has_comment
        if not has_comment and state.show_comment:
            state.show_comment = False
            comment_checkbox.value = False

        if not text.strip():
            annotation_row.controls.append(
                ft.Text('輸入文字後，這裡會顯示標註結果…', color=TEXT_SECONDARY, size=14)
            )
            page.update()
            return

        results: dict[tuple[str, str], dict[str, Any]] = {}
        for lang, scheme in state.schemes:
            results[(lang, scheme)] = get_result_for_scheme(state, lang, scheme, text)

        for ch in text:
            annotation_row.controls.append(
                build_char_unit(
                    ch,
                    state.schemes,
                    results,
                    state.selected_pinyin_idx,
                    state.show_comment,
                    on_pinyin_click,
                )
            )
        page.update()

    def compute_variants(mode: str) -> list[tuple[str, str]]:
        text = input_field.value or ''
        if not text.strip():
            return [('漢字', ''), ('漢字與註音', ''), ('註音', '')]

        converted = convert_text(text, mode)
        primary = state.schemes[0] if state.schemes else None
        result_map: dict[str, Any] = {}
        if primary:
            result_map = get_result_for_scheme(state, primary[0], primary[1], text)

        with_pinyin_parts: list[str] = []
        pinyin_only_parts: list[str] = []
        for ch in text:
            value = result_map.get(ch)
            note: list[str] = []
            if isinstance(value, dict):
                note = [n for n in (value.get('note') or []) if n]
            elif isinstance(value, list):
                note = [n for n in value if n]
            elif value:
                note = [str(value)]

            if note:
                key = (ch, primary[0], primary[1]) if primary else None
                idx = state.selected_pinyin_idx.get(key, 0) if key else 0
                if idx >= len(note):
                    idx = 0
                py = note[idx]
                with_pinyin_parts.append(f'{ch}({py})')
                pinyin_only_parts.append(py)
            else:
                with_pinyin_parts.append(ch)

        return [
            ('漢字', converted),
            ('漢字與註音', ''.join(with_pinyin_parts)),
            ('註音', ' '.join(pinyin_only_parts)),
        ]

    def on_settings(e) -> None:
        open_scheme_dialog(page, state, available, rebuild_annotation)

    def on_copy(e) -> None:
        open_copy_dialog(page, state, input_field, compute_variants)

    bottom_panel = build_bottom_panel(
        input_field, comment_checkbox, on_settings, on_copy,
    )

    page.add(
        ft.Column(
            [annotation_card, ft.Container(height=8), bottom_panel],
            spacing=0,
            expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )
    )

    rebuild_annotation()

if not IS_EMSCRIPTEN:
    app = FastAPI()
    app.mount('/note', flet_fastapi.app(main))

    if __name__ == '__main__':
        import uvicorn
        uvicorn.run(app, host='localhost', port=8080)
