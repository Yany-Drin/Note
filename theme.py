import flet as ft

BG_COLOR: str        = '#FFF5F6'
CARD_BG: str         = '#FFFFFF'
PRIMARY_ROSE: str    = '#C2185B'
SOFT_PINK: str       = '#F8BBD0'
LIGHT_PINK: str      = '#FCE4EC'
DEEP_PINK: str       = '#EC407A'
BORDER_PINK: str     = '#F48FB1'
TEXT_PRIMARY: str    = '#4A1528'
TEXT_SECONDARY: str  = '#8D6E7A'
HIGHLIGHT_GREEN: str = '#2E7D32'
HIGHLIGHT_RED: str   = '#C62828'


def build_theme() -> ft.Theme:
    return ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=PRIMARY_ROSE,
            secondary=DEEP_PINK,
            surface=CARD_BG,
            on_primary=ft.Colors.WHITE,
            on_surface=TEXT_PRIMARY,
        ),
    )