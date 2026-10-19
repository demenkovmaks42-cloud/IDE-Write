import sys
import re
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QComboBox, QMessageBox, QGroupBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt

class WriteIDE(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("WRITE — IDE for Sov Language (Linux Mint Native)")
        self.setGeometry(100, 100, 1000, 700)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # --- ЛЕВАЯ КОЛОНКА: Редактор кода ---
        left_layout = QVBoxLayout()

        mode_label = QLabel("Режим ввода:")
        mode_label.setFont(QFont("Sans Serif", 10, QFont.Weight.Bold))
        left_layout.addWidget(mode_label)

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Псевдокод (Русский v0.3)", "Классический Sov v0.3"])
        self.mode_combo.currentIndexChanged.connect(self.on_mode_changed)
        left_layout.addWidget(self.mode_combo)

        editor_label = QLabel("Исходный код / Псевдокод WRITE:")
        editor_label.setFont(QFont("Sans Serif", 10, QFont.Weight.Bold))
        left_layout.addWidget(editor_label)

        self.editor = QTextEdit()
        self.editor.setFont(QFont("Monospace", 11))
        self.editor.setPlainText(
            "главная программа:\n"
            "    пусть шаг = 10 умножить на 5\n"
            "    отправить 42 в порт 80\n"
            "    вернуть шаг"
        )
        left_layout.addWidget(self.editor)

        self.compile_btn = QPushButton("🚀 Транслировать и скомпилировать в x86")
        self.compile_btn.setFont(QFont("Sans Serif", 10, QFont.Weight.Bold))
        self.compile_btn.setStyleSheet("background-color: #2980b9; color: white; padding: 10px; border-radius: 5px;")
        self.compile_btn.clicked.connect(self.compile_code)
        left_layout.addWidget(self.compile_btn)

        main_layout.addLayout(left_layout, 1)

        # --- ПРАВАЯ КОЛОНКА: Результаты ---
        right_layout = QVBoxLayout()
        output_group = QGroupBox("Результат компиляции и ассемблер x86")
        output_group.setFont(QFont("Sans Serif", 10, QFont.Weight.Bold))
        output_layout = QVBoxLayout()

        output_layout.addWidget(QLabel("Сгенерированный код Sov v0.3:"))
        self.sov_code_view = QTextEdit()
        self.sov_code_view.setFont(QFont("Monospace", 10))
        self.sov_code_view.setReadOnly(True)
        output_layout.addWidget(self.sov_code_view)

        self.eax_label = QLabel("Значение в регистре EAX: —")
        self.eax_label.setFont(QFont("Sans Serif", 11, QFont.Weight.Bold))
        self.eax_label.setStyleSheet("color: #c0392b;")
        output_layout.addWidget(self.eax_label)

        output_layout.addWidget(QLabel("Машинный код (Hex):"))
        self.hex_view = QTextEdit()
        self.hex_view.setFont(QFont("Monospace", 10))
        self.hex_view.setMaximumHeight(70)
        self.hex_view.setReadOnly(True)
        output_layout.addWidget(self.hex_view)

        output_layout.addWidget(QLabel("Ассемблерный листинг x86 32-bit:"))
        self.asm_view = QTextEdit()
        self.asm_view.setFont(QFont("Monospace", 10))
        self.asm_view.setReadOnly(True)
        output_layout.addWidget(self.asm_view)

        output_group.setLayout(output_layout)
        right_layout.addWidget(output_group)

        main_layout.addLayout(right_layout, 1)

    def on_mode_changed(self):
        if "Русский" in self.mode_combo.currentText():
            self.editor.setPlainText(
                "главная программа:\n"
                "    пусть шаг = 10 умножить на 5\n"
                "    отправить 42 в порт 80\n"
                "    вернуть шаг"
            )
        else:
            self.editor.setPlainText(
                "fn main() {\n"
                "    let step = 10 * 5;\n"
                "    out 80, 42;\n"
                "    return step;\n"
                "}"
            )

    def compile_code(self):
        source_code = self.editor.toPlainText()
        mode = self.mode_combo.currentText()

        try:
            sov_code = ""
            val1, val2, op = 0, 0, '+'
            port_val, data_val = None, None

            if "Русский" in mode:
                lines = [line.strip() for line in source_code.split('\n') if line.strip()]
                var_name = "result"

                for line in lines:
                    line_lower = line.lower()
                    if "пусть" in line_lower or "=" in line:
                        parts = line.replace("пусть", "").strip().split("=")
                        if len(parts) == 2:
                            var_name = parts[0].strip()
                            expr = parts[1].strip()

                            for op_symbol, op_words in [('+', ['плюс', '+']), ('-', ['минус', '-']), ('*', ['умножить', '*'])]:
                                for w in op_words:
                                    if w in expr:
                                        nums = expr.split(w)
                                        if len(nums) == 2:
                                            val1 = int(nums[0].strip())
                                            val2 = int(nums[1].strip())
                                            op = op_symbol
                                            break
                    elif "отправить" in line_lower and "порт" in line_lower:
                        words = line_lower.replace("отправить", "").replace("в порт", "").replace("порт", "").split()
                        if len(words) >= 2:
                            data_val = int(words[0])
                            port_val = int(words[1])

                if val1 == 0 and val2 == 0:
                    QMessageBox.warning(self, "Ошибка псевдокода", "Не удалось разобрать выражение.\nПример: `пусть шаг = 10 умножить на 5`")
                    return

                sov_code = f"fn main() {{\n    let {var_name} = {val1} {op} {val2};\n"
                if port_val is not None:
                    sov_code += f"    out {port_val}, {data_val};\n"
                sov_code += f"    return {var_name};\n}}"
            else:
                sov_code = source_code
                match_calc = re.search(r'let\s+(\w+)\s*=\s*(\d+)\s*([\+\-\*])\s*(\d+);', sov_code)
                match_port = re.search(r'out\s+(\d+),\s*(\d+);', sov_code)

                if not match_calc:
                    QMessageBox.warning(self, "Ошибка", "Проверьте синтаксис инструкции let в Sov v0.3")
                    return
                _, val1_str, op, val2_str = match_calc.groups()
                val1, val2 = int(val1_str), int(val2_str)

                if match_port:
                    port_str, data_str = match_port.groups()
                    port_val, data_val = int(port_str), int(data_str)

            if op == '+': calc_result = val1 + val2
            elif op == '-': calc_result = val1 - val2
            else: calc_result = val1 * val2

            machine_code = bytearray()
            machine_code.append(0xB8)
            machine_code.extend(val1.to_bytes(4, 'little', signed=False))

            if op == '+':
                machine_code.append(0x05)
                machine_code.extend(val2.to_bytes(4, 'little', signed=False))
            elif op == '-':
                machine_code.append(0x2D)
                machine_code.extend(val2.to_bytes(4, 'little', signed=False))
            elif op == '*':
                machine_code.extend([0x69, 0xC0])
                machine_code.extend(val2.to_bytes(4, 'little', signed=False))

            if port_val is not None:
                machine_code.extend([0x66, 0xBA])
                machine_code.extend(port_val.to_bytes(2, 'little', signed=False))
                machine_code.append(0xB0)
                machine_code.append(data_val & 0xFF)
                machine_code.append(0xEE)

            machine_code.append(0xC3)

            self.sov_code_view.setPlainText(sov_code)
            self.eax_label.setText(f"Значение в регистре EAX: {calc_result} (0x{calc_result:X})")
            self.hex_view.setPlainText(machine_code.hex())

            asm = f"00000000  B8{val1.to_bytes(4, 'little').hex().upper()}        mov eax, 0x{val1:x}\n"
            offset = 5
            if op == '+':
                asm += f"00000005  05{val2.to_bytes(4, 'little').hex().upper()}        add eax, 0x{val2:x}\n"
                offset += 5
            elif op == '-':
                asm += f"00000005  2D{val2.to_bytes(4, 'little').hex().upper()}        sub eax, 0x{val2:x}\n"
                offset += 5
            elif op == '*':
                asm += f"00000005  69C0{val2.to_bytes(4, 'little').hex().upper()}      imul eax, eax, 0x{val2:x}\n"
                offset += 6

            if port_val is not None:
                asm += f"000000{offset:02X}  66BA{port_val.to_bytes(2, 'little').hex().upper()}    mov dx, 0x{port_val:x}\n"
                asm += f"000000{offset+4:02X}  B0{data_val:02X}              mov al, 0x{data_val:x}\n"
                asm += f"000000{offset+6:02X}  EE                  out dx, al\n"
                offset += 7

            asm += f"000000{offset:02X}  C3                  ret"
            self.asm_view.setPlainText(asm)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка компиляции WRITE", str(e))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ide = WriteIDE()
    ide.show()
    sys.exit(app.exec())
