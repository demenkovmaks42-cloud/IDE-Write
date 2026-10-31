import pytest
from parser import parse, ParseError, Assign, Out
from codegen import generate


def test_russian_multiply_na():
    instrs = parse("пусть x = 10 умножить на 5", "russian")
    assert isinstance(instrs[0], Assign)
    assert instrs[0].result() == 50


def test_russian_multiply_no_na():
    instrs = parse("пусть x = 10 умножить 5", "russian")
    assert instrs[0].result() == 50


def test_russian_star():
    instrs = parse("пусть x = 10 * 5", "russian")
    assert instrs[0].result() == 50


def test_russian_simple_assign():
    instrs = parse("пусть x = 42", "russian")
    assert instrs[0].op == '='
    assert instrs[0].result() == 42


def test_russian_negative():
    instrs = parse("пусть x = -5", "russian")
    assert instrs[0].result() == -5


def test_russian_out():
    instrs = parse("пусть x = 1\nотправить 42 в порт 80", "russian")
    out = [i for i in instrs if isinstance(i, Out)][0]
    assert out.port == 80 and out.data == 42


def test_python_mode():
    instrs = parse("x = 10 * 5\nout(80, 42)", "python")
    assert instrs[0].result() == 50
    assert isinstance(instrs[1], Out)


def test_cpp_mode():
    instrs = parse("int x = 10 * 5;\nout(80, 42);", "cpp")
    assert instrs[0].result() == 50


def test_html_mode():
    instrs = parse('<let name="x" expr="10 * 5"/><out port="80" data="42"/>', "html")
    assert instrs[0].result() == 50
    assert instrs[1].port == 80


def test_sov_mode():
    src = "fn main() {\n let x = 10 * 5;\n out 80, 42;\n return x;\n}"
    instrs = parse(src, "sov")
    assert instrs[0].result() == 50


def test_bad_ident():
    with pytest.raises(ParseError):
        parse("пусть 1x = 5", "russian")


def test_data_out_of_range():
    instrs = parse("пусть x = 1\nотправить 300 в порт 80", "russian")
    with pytest.raises(ParseError):
        generate(instrs)


def test_port_out_of_range():
    instrs = parse('<let name="x" expr="1"/><out port="70000" data="1"/>', "html")
    with pytest.raises(ParseError):
        generate(instrs)
