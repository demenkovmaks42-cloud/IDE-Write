#!/bin/bash
export LD_LIBRARY_PATH="$(python -c "import PyQt6, os; print(os.path.join(os.path.dirname(PyQt6.__file__), 'Qt6', 'lib'))"):$LD_LIBRARY_PATH"
python main.py
