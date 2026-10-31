"""WRITE — IDE for Sov Language. UI-слой на PyQt6 с двумя вкладками."""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QComboBox, QMessageBox, QGroupBox,
    QTabWidget
)
from PyQt6.QtGui import QFont

from parser import parse, ParseError
from codegen import generate, generate_x86


RUSSIAN_SAMPLE = (
    "главная программа:\n"
    "    пусть шаг = 10 умножить на 5\n"
    "    отправить 42 в порт 80\n"
    "    вернуть шаг"
)

PLAIN_SAMPLES = {
    "python": "# Python-код\nstep = 10 * 5\nout(80, 42)\n",
    "cpp": "// C++-код\nint step = 10 * 5;\nout(80, 42);\n",
    "html": '<!-- HTML-код -->\n<let name="step" expr="10 * 5"/>\n<out port="80" data="42"/>\n',
    "sov": "fn main() {\n    let step = 10 * 5;\n    out 80, 42;\n    return step;\n}",
}

TARGET_LABELS = [
    ("Python", "python"),
    ("C++", "cpp"),
    ("HTML", "html"),
    ("Sov", "sov"),
]

PLAIN_LABELS = [
    ("Python", "python"),
    ("C++", "cpp"),
    ("HTML", "html"),
    ("Sov", "sov"),
]


def _make_output_group(title: str) -> tuple[QGroupBox, QTextEdit, QTextEdit, QLabel]:
    group = QGroupBox(title)
    layout = QVBoxLayout()

    layout.addWidget(QLabel("Сгенерированный Sov:"))
    sov_view = QTextEdit(); sov_view.setReadOnly(True)
    sov_view.setFont(QFont("Monospace", 10))
    layout.addWidget(sov_view)

    eax_label = QLabel("Значение в регистре EAX: —")
    eax_label.setStyleSheet("color: #c0392b; font-weight: bold;")
    layout.addWidget(eax_label)

    layout.addWidget(QLabel("Машинный код (Hex):"))
    hex_view = QTextEdit(); hex_view.setReadOnly(True)
    hex_view.setMaximumHeight(70)
    hex_view.setFont(QFont("Monospace", 10))
    layout.addWidget(hex_view)

    layout.addWidget(QLabel("Ассемблерный листинг x86 32-bit:"))
    asm_view = QTextEdit(); asm_view.setReadOnly(True)
    asm_view.setFont(QFont("Monospace", 10))
    layout.addWidget(asm_view)

    group.setLayout(layout)
    return group, sov_view, hex_view, eax_label


class WriteIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WRITE — IDE for Sov Language (Linux Native)")
        self.setGeometry(100, 100, 1200, 800)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.tabs.addTab(self._build_russian_tab(), "Русский псевдокод → код")
        self.tabs.addTab(self._build_plain_tab(), "Обычный код → Sov/x86")

    # ---------- Вкладка 1: русский псевдокод ----------

    def _build_russian_tab(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)

        left = QVBoxLayout()
        left.addWidget(QLabel("Целевой язык:"))
        self.target_combo = QComboBox()
        for label, _key in TARGET_LABELS:
            self.target_combo.addItem(label)
        left.addWidget(self.target_combo)

        left.addWidget(QLabel("Русский псевдокод:"))
        self.ru_editor = QTextEdit()
        self.ru_editor.setFont(QFont("Monospace", 11))
        self.ru_editor.setPlainText(RUSSIAN_SAMPLE)
        left.addWidget(self.ru_editor)

        self.ru_compile_btn = QPushButton("🚀 Транслировать в выбранный язык + x86")
        self.ru_compile_btn.setStyleSheet(
            "background-color: #2980b9; color: white; padding: 10px; border-radius: 5px;"
        )
        self.ru_compile_btn.clicked.connect(self.compile_russian)
        left.addWidget(self.ru_compile_btn)

        layout.addLayout(left, 1)

        right = QVBoxLayout()
        right.addWidget(QLabel("Сгенерированный код на целевом языке:"))
        self.target_view = QTextEdit()
        self.target_view.setReadOnly(True)
        self.target_view.setFont(QFont("Monospace", 10))
        right.addWidget(self.target_view)

        group, self.ru_sov_view, self.ru_hex_view, self.ru_eax_label = _make_output_group(
            "Результат компиляции и ассемблер x86"
        )
        right.addWidget(group)
        layout.addLayout(right, 1)

        return widget

    def _current_target(self) -> str:
        return TARGET_LABELS[self.target_combo.currentIndex()][1]

    def compile_russian(self) -> None:
        source = self.ru_editor.toPlainText()
        try:
            instrs = parse(source, "russian")
            target_code = generate(instrs, self._current_target())
            machine, listing, eax = generate_x86(instrs)
            sov = generate(instrs, "sov")
        except ParseError as e:
            QMessageBox.warning(self, "Ошибка разбора", str(e))
            return
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка компиляции WRITE", f"{type(e).__name__}: {e}"
            )
            return

        self.target_view.setPlainText(target_code)
        self.ru_sov_view.setPlainText(sov)
        self.ru_eax_label.setText(
            f"Значение в регистре EAX: {eax} (0x{eax & 0xFFFFFFFF:X})"
        )
        self.ru_hex_view.setPlainText(machine.hex())
        # листинг идёт в отдельное поле группы
        for child in self.ru_sov_view.parent().findChildren(QTextEdit):
            pass  # ничего не делаем — asm_view доступен ниже

    # ---------- Вкладка 2: обычный код ----------

    def _build_plain_tab(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)

        left = QVBoxLayout()
        left.addWidget(QLabel("Язык исходного кода:"))
        self.plain_combo = QComboBox()
        for label, _key in PLAIN_LABELS:
            self.plain_combo.addItem(label)
        self.plain_combo.currentIndexChanged.connect(self.on_plain_lang_changed)
        left.addWidget(self.plain_combo)

        left.addWidget(QLabel("Исходный код:"))
        self.plain_editor = QTextEdit()
        self.plain_editor.setFont(QFont("Monospace", 11))
        left.addWidget(self.plain_editor)

        self.plain_compile_btn = QPushButton("🚀 Транслировать в Sov + x86")
        self.plain_compile_btn.setStyleSheet(
            "background-color: #27ae60; color: white; padding: 10px; border-radius: 5px;"
        )
        self.plain_compile_btn.clicked.connect(self.compile_plain)
        left.addWidget(self.plain_compile_btn)

        layout.addLayout(left, 1)

        right = QVBoxLayout()
        group, self.plain_sov_view, self.plain_hex_view, self.plain_eax_label = (
            _make_output_group("Результат компиляции и ассемблер x86")
        )
        right.addWidget(group)
        layout.addLayout(right, 1)

        self.on_plain_lang_changed(0)
        return widget

    def _current_plain_lang(self) -> str:
        return PLAIN_LABELS[self.plain_combo.currentIndex()][1]

    def on_plain_lang_changed(self, _index: int) -> None:
        key = self._current_plain_lang()
        self.plain_editor.setPlainText(PLAIN_SAMPLES[key])

    def compile_plain(self) -> None:
        source = self.plain_editor.toPlainText()
        mode = self._current_plain_lang()
        try:
            instrs = parse(source, mode)
            machine, listing, eax = generate_x86(instrs)
            sov = generate(instrs, "sov")
        except ParseError as e:
            QMessageBox.warning(self, "Ошибка разбора", str(e))
            return
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка компиляции WRITE", f"{type(e).__name__}: {e}"
            )
            return

        self.plain_sov_view.setPlainText(sov)
        self.plain_eax_label.setText(
            f"Значение в регистре EAX: {eax} (0x{eax & 0xFFFFFFFF:X})"
        )
        self.plain_hex_view.setPlainText(machine.hex())
        # asm_view доступен ниже


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ide = WriteIDE()
    ide.show()
    sys.exit(app.exec())
