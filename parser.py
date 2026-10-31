from dataclasses import dataclass
from typing import Optional, List, Union
import re


class ParseError(Exception):
    """Ошибка разбора псевдокода с понятным сообщением."""
    pass


# ---------- AST ----------

@dataclass
class Assign:
    var: str
    val1: int
    op: str                      # '+', '-', '*' или '=' (простое присваивание)
    val2: Optional[int] = None

    def result(self) -> int:
        if self.op == '=':
            return self.val1
        if self.op == '+':
            return self.val1 + self.val2
        if self.op == '-':
            return self.val1 - self.val2
        if self.op == '*':
            return self.val1 * self.val2
        raise ParseError(f"Неизвестный оператор: {self.op}")


@dataclass
class Out:
    port: int
    data: int


Instruction = Union[Assign, Out]


# ---------- Утилиты ----------

OP_WORDS = {
    '+': ['плюс', '+'],
    '-': ['минус', '-'],
    '*': ['умножить на', 'умножить', '*'],
}

_IDENT_RE = re.compile(r'^[A-Za-zА-Яа-я_][A-Za-zА-Яа-я0-9_]*$')


def _check_ident(name: str) -> str:
    if not _IDENT_RE.match(name):
        raise ParseError(f"Недопустимое имя переменной: {name!r}")
    return name


def _parse_int(text: str, what: str) -> int:
    text = text.strip()
    try:
        return int(text, 0)
    except ValueError:
        raise ParseError(f"Ожидалось целое число в {what}, получено: {text!r}")


def _split_expr(expr: str):
    """Разбирает выражение: 10 * 5, 10 умножить на 5, 10 + 5, -5, 42."""
    expr = expr.strip().rstrip(';').strip()
    if not expr:
        raise ParseError("Пустое выражение")

    for op, words in OP_WORDS.items():
        for w in words:
            pattern = re.escape(w)
            if w in ('+', '-', '*'):
                m = re.search(
                    r'(?<!\S)' + pattern + r'(?!\S)|(?<=\d)' + pattern + r'(?=\d)',
                    expr
                )
            else:
                m = re.search(r'\b' + pattern + r'\b', expr, flags=re.IGNORECASE)
            if m:
                left = expr[:m.start()].strip()
                right = expr[m.end():].strip()
                if not left or not right:
                    continue
                val1 = _parse_int(left, "левом операнде")
                val2 = _parse_int(right, "правом операнде")
                return val1, op, val2

    val1 = _parse_int(expr, "выражении")
    return val1, '=', None


# ---------- Русский псевдокод ----------

_RU_LET_RE = re.compile(r'пусть\s+([A-Za-zА-Яа-я_]\w*)\s*=\s*(.+)$', re.IGNORECASE)
_RU_OUT_RE = re.compile(r'отправить\s+(-?\d+)\s+в\s+порт\s+(\d+)', re.IGNORECASE)


def parse_russian(source: str) -> List[Instruction]:
    instrs: List[Instruction] = []
    for raw in source.splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        m = _RU_OUT_RE.search(line)
        if m:
            instrs.append(Out(port=int(m.group(2)), data=int(m.group(1))))
            continue
        m = _RU_LET_RE.match(line)
        if m:
            var = _check_ident(m.group(1))
            val1, op, val2 = _split_expr(m.group(2))
            instrs.append(Assign(var, val1, op, val2))
            continue
        if line.endswith(':'):
            continue
    if not any(isinstance(i, Assign) for i in instrs):
        raise ParseError("Не найдено ни одного присваивания (пусть x = ...)")
    return instrs


# ---------- Sov ----------

_SOV_LET_RE = re.compile(r'let\s+([A-Za-z_]\w*)\s*=\s*(.+?);', re.IGNORECASE)
_SOV_OUT_RE = re.compile(r'out\s+(\d+)\s*,\s*(\d+)\s*;', re.IGNORECASE)


def parse_sov(source: str) -> List[Instruction]:
    instrs: List[Instruction] = []
    for m in _SOV_LET_RE.finditer(source):
        var = _check_ident(m.group(1))
        val1, op, val2 = _split_expr(m.group(2))
        instrs.append(Assign(var, val1, op, val2))
    for m in _SOV_OUT_RE.finditer(source):
        instrs.append(Out(port=int(m.group(1)), data=int(m.group(2))))
    if not any(isinstance(i, Assign) for i in instrs):
        raise ParseError("В коде Sov не найдено ни одной инструкции let")
    return instrs


# ---------- Python-псевдокод ----------

_PY_ASSIGN_RE = re.compile(r'^([A-Za-zА-Яа-я_]\w*)\s*=\s*(.+)$')
_PY_OUT_RE = re.compile(r'^out\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)\s*;?$', re.IGNORECASE)


def parse_python(source: str) -> List[Instruction]:
    instrs: List[Instruction] = []
    for raw in source.splitlines():
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        m = _PY_OUT_RE.match(line)
        if m:
            instrs.append(Out(port=int(m.group(1)), data=int(m.group(2))))
            continue
        m = _PY_ASSIGN_RE.match(line)
        if m:
            var = _check_ident(m.group(1))
            val1, op, val2 = _split_expr(m.group(2))
            instrs.append(Assign(var, val1, op, val2))
            continue
        raise ParseError(f"Не удалось разобрать строку (Python-псевдокод): {line!r}")
    if not any(isinstance(i, Assign) for i in instrs):
        raise ParseError("В Python-псевдокоде не найдено ни одного присваивания")
    return instrs


# ---------- C++-псевдокод ----------

_CPP_DECL_RE = re.compile(r'(?:int|long|short)\s+([A-Za-zА-Яа-я_]\w*)\s*=\s*(.+?);', re.IGNORECASE)
_CPP_OUT_RE = re.compile(r'out\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)\s*;', re.IGNORECASE)


def parse_cpp(source: str) -> List[Instruction]:
    instrs: List[Instruction] = []
    for m in _CPP_DECL_RE.finditer(source):
        var = _check_ident(m.group(1))
        val1, op, val2 = _split_expr(m.group(2))
        instrs.append(Assign(var, val1, op, val2))
    for m in _CPP_OUT_RE.finditer(source):
        instrs.append(Out(port=int(m.group(1)), data=int(m.group(2))))
    if not any(isinstance(i, Assign) for i in instrs):
        raise ParseError("В C++-псевдокоде не найдено ни одного объявления переменной")
    return instrs


# ---------- HTML-псевдокод ----------

_HTML_LET_RE = re.compile(
    r'<let\s+name\s*=\s*"([A-Za-zА-Яа-я_]\w*)"\s+expr\s*=\s*"([^"]+)"\s*/?>',
    re.IGNORECASE
)
_HTML_OUT_RE = re.compile(
    r'<out\s+port\s*=\s*"(\d+)"\s+data\s*=\s*"(\d+)"\s*/?>',
    re.IGNORECASE
)


def parse_html(source: str) -> List[Instruction]:
    instrs: List[Instruction] = []
    for m in _HTML_LET_RE.finditer(source):
        var = _check_ident(m.group(1))
        val1, op, val2 = _split_expr(m.group(2))
        instrs.append(Assign(var, val1, op, val2))
    for m in _HTML_OUT_RE.finditer(source):
        instrs.append(Out(port=int(m.group(1)), data=int(m.group(2))))
    if not any(isinstance(i, Assign) for i in instrs):
        raise ParseError("В HTML-псевдокоде не найдено ни одного тега <let>")
    return instrs


# ---------- Dispatch ----------

PARSERS = {
    "russian": parse_russian,
    "sov": parse_sov,
    "python": parse_python,
    "cpp": parse_cpp,
    "html": parse_html,
}


def parse(source: str, mode: str) -> List[Instruction]:
    if mode not in PARSERS:
        raise ParseError(f"Неизвестный режим: {mode}")
    return PARSERS[mode](source)
