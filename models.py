import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jieba
import pandas as pd

import data_loader

DATA_DIR: Path = Path(__file__).parent / 'data'


@dataclass
class AppState:
    schemes: list[tuple[str, str]] = field(default_factory=list)
    selected_pinyin_idx: dict[tuple[str, str, str], int] = field(default_factory=dict)
    show_comment: bool = False
    df_cache: dict[str, pd.DataFrame] = field(default_factory=dict)


def discover_schemes() -> list[tuple[str, str]]:
    result: list[tuple[str, str]] = []
    for toml_path in sorted(DATA_DIR.glob('*.config.toml')):
        try:
            with toml_path.open('rb') as f:
                config = tomllib.load(f)
            lang = config['info']['name']
            for scheme in config['columns']:
                result.append((lang, scheme))
        except Exception:
            continue
    return result


def get_df(state: AppState, lang: str) -> pd.DataFrame | None:
    if lang in state.df_cache:
        return state.df_cache[lang]
    try:
        with open(DATA_DIR / f'{lang}.config.toml', 'rb') as f:
            config = tomllib.load(f)
        df = data_loader.load_data(config)
        state.df_cache[lang] = df
        return df
    except Exception:
        return None


def get_result_for_scheme(
    state: AppState, lang: str, scheme: str, text: str,
) -> dict[str, Any]:
    """返回 {單字: 值}，值為 list 或 {'note': [...], 'comment': [...]}。"""
    df = get_df(state, lang)
    if df is None:
        return {}
    func = data_loader.get_function(df, scheme)
    result: dict[str, Any] = {}
    import jieba
    for word in jieba.cut(text, cut_all=False):
        if word.strip():
            result.update(func(df, word, scheme))
    print(result)
    return result


def has_any_comment_scheme(state: AppState) -> bool:
    """當前勾選方案中是否有任一方案返回字典值（含註解）。"""
    for lang, scheme in state.schemes:
        df = get_df(state, lang)
        if df is None:
            continue
        try:
            if df[scheme].map(lambda x: isinstance(x, dict)).any():
                return True
        except Exception:
            continue
    return False
