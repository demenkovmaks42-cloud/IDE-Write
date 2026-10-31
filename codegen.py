"""
Генерация целевого кода (Python / C++ / HTML), Sov-кода, машинного кода x86
и ассемблерного листинга из списка инструкций AST.
"""

from typing import List, Tuple
from parser import Assign, Out, Instruction, ParseError

# Ограничения ISA
MAX_DATA = 0xFF
MAX_PORT = 0xFFFF
MAX_VAL = 0x7FFFFFFF
MIN_VAL = -MAX_VAL - 1


# ---------- Транслитерация ----------

_TRANSLIT = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
}


def _safe_name(name: str) -> str:
    """Транслитерирует кириллицу, оставляет латиницу как есть."""
    out = []
    for ch in name:
        low = ch.lower()
        if low in _TRANSLIT:
            tr = _TRANSLIT[low]
            out.append(tr.capitalize() if ch.isupper() else tr)
        elif ch.isalnum() or ch == '_':
            out.append(ch)
        else:
            out.append('_')
    result = ''.join(out) or 'var'
    if result[0].isdigit():
        result = '_' + result
    return result


def _op_cpp(op: str) -> str:
    return {'+': '+', '-': '-', '*': '*'}.get(op, '+')


# ---------- Валидация ----------

def validate(instrs: List[Instruction]) -> None:
    for ins in instrs:
        if isinstance(ins, Assign):
            for v in (ins.val1, ins.val2):
                if v is None:
                    continue
                if not (MIN_VAL <= v <= MAX_VAL):
                    raise ParseError(f"Число {v} не влезает в 32-bit signed")
        elif isinstance(ins, Out):
            if not (0 <= ins.port <= MAX_PORT):
                raise ParseError(f"Порт {ins.port} вне диапазона 0..{MAX_PORT}")
            if not (0 <= ins.data <= MAX_DATA):
                raise ParseError(
                    f"Данные {ins.data} вне диапазона 0..{MAX_DATA} (8-bit OUT)"
                )


# ---------- Генератор Sov ----------

def to_sov(instrs: List[Instruction]) -> str:
    lines = ["fn main() {"]
    last_var = "result"
    for ins in instrs:
        if isinstance(ins, Assign):
            last_var = _safe_name(ins.var)
            if ins.op == '=':
                lines.append(f"    let {last_var} = {ins.val1};")
            else:
                lines.append(f"    let {last_var} = {ins.val1} {ins.op} {ins.val2};")
        elif isinstance(ins, Out):
            lines.append(f"    out {ins.port}, {ins.data};")
    lines.append(f"    return {last_var};")
    lines.append("}")
    return "\n".join(lines)


# ---------- Генератор Python ----------

def to_python(instrs: List[Instruction]) -> str:
    lines = ["# Сгенерировано из русского псевдокода WRITE", ""]
    last_var = None
    for ins in instrs:
        if isinstance(ins, Assign):
            last_var = _safe_name(ins.var)
            if ins.op == '=':
                lines.append(f"{last_var} = {ins.val1}")
            else:
                lines.append(f"{last_var} = {ins.val1} {ins.op} {ins.val2}")
        elif isinstance(ins, Out):
            lines.append(f"# отправить {ins.data} в порт {ins.port}")
            lines.append(f"out({ins.port}, {ins.data})")
    if last_var:
        lines.append("")
        lines.append(f"print({last_var})")
    return "\n".join(lines)


# ---------- Генератор C++ ----------

def to_cpp(instrs: List[Instruction]) -> str:
    lines = [
        "// Сгенерировано из русского псевдокода WRITE",
        "#include <iostream>",
        "",
        "void out(int port, int data) {",
        '    std::cout << "out " << port << ", " << data << std::endl;',
        "}",
        "",
        "int main() {",
    ]
    last_var = None
    for ins in instrs:
        if isinstance(ins, Assign):
            last_var = _safe_name(ins.var)
            if ins.op == '=':
                lines.append(f"    int {last_var} = {ins.val1};")
            else:
                lines.append(
                    f"    int {last_var} = {ins.val1} {_op_cpp(ins.op)} {ins.val2};"
                )
        elif isinstance(ins, Out):
            lines.append(f"    out({ins.port}, {ins.data});")
    if last_var:
        lines.append(f'    std::cout << {last_var} << std::endl;')
    lines.append("    return 0;")
    lines.append("}")
    return "\n".join(lines)


# ---------- Генератор HTML ----------

def to_html(instrs: List[Instruction]) -> str:
    lines = [
        "<!DOCTYPE html>",
        "<html lang=\"ru\">",
        "<head>",
        "  <meta charset=\"UTF-8\">",
        "  <title>WRITE output</title>",
        "</head>",
        "<body>",
        "  <h1>Результат выполнения</h1>",
        "  <table border=\"1\" cellpadding=\"6\">",
        "    <tr><th>Инструкция</th><th>Значение</th></tr>",
    ]
    for ins in instrs:
        if isinstance(ins, Assign):
            lines.append(
                f"    <tr><td>пусть {ins.var} = ...</td>"
                f"<td>{ins.result()}</td></tr>"
            )
        elif isinstance(ins, Out):
            lines.append(
                f"    <tr><td>отправить в порт {ins.port}</td>"
                f"<td>{ins.data}</td></tr>"
            )
    lines += [
        "  </table>",
        "</body>",
        "</html>",
    ]
    return "\n".join(lines)


# ---------- x86 генерация ----------

def _emit_assign(machine: bytearray, listing: List[str], ins: Assign) -> None:
    start = len(machine)
    machine.append(0xB8)
    machine.extend(ins.val1.to_bytes(4, 'little', signed=True))
    listing.append(
        f"{start:08X}  B8{ins.val1.to_bytes(4, 'little', signed=True).hex().upper():<8}  "
        f"mov eax, {ins.val1}"
    )
    if ins.op == '+':
        start = len(machine)
        machine.append(0x05)
        machine.extend(ins.val2.to_bytes(4, 'little', signed=True))
        listing.append(
            f"{start:08X}  05{ins.val2.to_bytes(4, 'little', signed=True).hex().upper():<8}  "
            f"add eax, {ins.val2}"
        )
    elif ins.op == '-':
        start = len(machine)
        machine.append(0x2D)
        machine.extend(ins.val2.to_bytes(4, 'little', signed=True))
        listing.append(
            f"{start:08X}  2D{ins.val2.to_bytes(4, 'little', signed=True).hex().upper():<8}  "
            f"sub eax, {ins.val2}"
        )
    elif ins.op == '*':
        start = len(machine)
        machine.extend([0x69, 0xC0])
        machine.extend(ins.val2.to_bytes(4, 'little', signed=True))
        listing.append(
            f"{start:08X}  69C0{ins.val2.to_bytes(4, 'little', signed=True).hex().upper():<6}  "
            f"imul eax, eax, {ins.val2}"
        )


def _emit_out(machine: bytearray, listing: List[str], ins: Out) -> None:
    start = len(machine)
    machine.extend([0x66, 0xBA])
    machine.extend(ins.port.to_bytes(2, 'little', signed=False))
    listing.append(
        f"{start:08X}  66BA{ins.port.to_bytes(2, 'little').hex().upper():<6}  "
        f"mov dx, {ins.port}"
    )
    start = len(machine)
    machine.append(0xB0)
    machine.append(ins.data & 0xFF)
    listing.append(
        f"{start:08X}  B0{ins.data & 0xFF:02X}{'':<6}  mov al, {ins.data & 0xFF}"
    )
    start = len(machine)
    machine.append(0xEE)
    listing.append(f"{start:08X}  EE{'':<10}  out dx, al")


def generate_x86(instrs: List[Instruction]) -> Tuple[bytes, str, int]:
    """Возвращает (machine_code, asm_listing, eax_value)."""
    validate(instrs)
    machine = bytearray()
    listing: List[str] = []
    eax_value = 0
    for ins in instrs:
        if isinstance(ins, Assign):
            _emit_assign(machine, listing, ins)
            eax_value = ins.result()
        elif isinstance(ins, Out):
            _emit_out(machine, listing, ins)
    start = len(machine)
    machine.append(0xC3)
    listing.append(f"{start:08X}  C3{'':<10}  ret")
    return bytes(machine), "\n".join(listing), eax_value


# ---------- Универсальный генератор ----------

TARGETS = {
    "python": to_python,
    "cpp": to_cpp,
    "html": to_html,
    "sov": to_sov,
}


def generate(instrs: List[Instruction], target: str) -> str:
    if target not in TARGETS:
        raise ParseError(f"Неизвестный целевой язык: {target}")
    return TARGETS[target](instrs)
