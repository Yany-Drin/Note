import math
import tomllib
import pandas as pd
import hanzidentifier
from opencc_purepy import OpenCC
import jieba


cc_t2tw = OpenCC('t2tw')
cc_s2tw = OpenCC('s2tw')


def load_data(config: dict) -> pd.DataFrame:
    df = pd.read_csv(
        f'data/{config["info"]["name"]}.csv',
        sep=config['sep'][0],
        names=['char', *config['columns']],
    )

    def parse_parentheses(text: str) -> list[str]:
        if config['com'][0] in text and config['com'][1] in text:
            return text[:-1].split(config['com'][0])
        return [text, '']

    def process_cell(x):
        items = x if isinstance(x, list) else [x]
        parsed = [parse_parentheses(s) for s in items]
        if any(len(p) > 1 and p[1] for p in parsed):
            return {
                'note': [p[0] for p in parsed],
                'comment': [p[1] if len(p) > 1 else '' for p in parsed],
            }
        return x

    for column in config['columns']:
        df[column] = df[column].str.strip()
        if df[column].str.contains(config['sep'][1], na=False).any():
            df[column] = df[column].str.split(config['sep'][1])
        mask = df[column].notna()
        df.loc[mask, column] = df.loc[mask, column].map(process_cell)

    df = df[df.char.map(
        lambda x: hanzidentifier.identify(x) != 2
    )].reset_index(drop=True)

    df['char'] = df.char.map(lambda x:
        (x_tw := cc_t2tw.convert(x)) != x and
        x_tw not in df.char.values and
        x_tw or x
    )
    return df


def get_value(df: pd.DataFrame, char: str, column: str) -> str | list | dict | None:
    def get_value_(df: pd.DataFrame, char: str, column: str):
        row = df[df.char == char]
        if row.empty:
            return None
        value = row.iloc[0][column]
        if value is None:
            return None
        if isinstance(value, float) and math.isnan(value):
            return None
        if isinstance(value, (list, tuple)) and not any(v for v in value if v):
            return None
        return value
    value = get_value_(df, char, column)
    if value is None:
        alt = cc_s2tw.convert(char)
        if alt != char:
            value = get_value_(df, alt, column)
    return value


def get_note(df: pd.DataFrame, char: str, column: str) -> dict:
    value = get_value(df, char, column)
    if value is None and len(char) > 1:
        return {c: get_value(df, c, column) for c in char}
    if len(char) > 1 and isinstance(value, list):
        return {c: [v] for c, v in zip(char, value)}
    return {char: value}


def get_note_with_comment(df: pd.DataFrame, char: str, column: str) -> dict:
    value = get_value(df, char, column)
    if len(char) > 1:
        return {c: get_value(df, c, column) for c in char}
    return {char: value}


def get_function(df: pd.DataFrame, column: str):
    if df[column].map(lambda x: isinstance(x, dict)).any():
        return get_note_with_comment
    return get_note