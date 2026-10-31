# WRITE IDE

**WRITE** — нативная среда разработки (IDE) под Linux Mint и другие дистрибутивы Linux,
созданная для работы с низкоуровневым языком **Sov**.

Поддерживает ввод псевдокода на **русском**, **Python**, **C++** и **HTML**, автоматическую
трансляцию в синтаксис `Sov` и компиляцию в машинный код x86 (32-bit) с выводом
ассемблерного листинга.

## Системные требования

- ОС: Linux Mint / Ubuntu / Debian
- Python 3.10+ (рекомендуется 3.13)
- PyQt6

## Установка и запуск

```bash
git clone https://github.com/demenkovmaks42-cloud/IDE-Write.git
cd WRITE
cd IDE-Write
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
