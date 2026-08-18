import subprocess
import sys

import ascop


class DummyOptions:
    def __init__(self, **kwargs):
        self.replace = kwargs.get('replace')
        self.use_unicode = kwargs.get('use_unicode', False)
        self.typographic = kwargs.get('typographic', False)
        self.strip_stickers = kwargs.get('strip_stickers', False)
        self.encoding = kwargs.get('encoding', 'utf-8')
        self.encode_mode = kwargs.get('encode_mode')
        self.check = kwargs.get('check', False)


def _write(tmp_path, text):
    p = tmp_path / "sample.txt"
    p.write_text(text, encoding="utf-8")
    return str(p)


def test_ascii_pass_through(tmp_path):
    text = "Just a regular ASCII sentence."
    out, chars, pos = ascop.analyze_file(_write(tmp_path, text), DummyOptions())
    assert out == text
    assert chars == []
    assert pos == []


def test_typographic_replacement(tmp_path):
    text = '“Smart quotes” and – dashes…'
    expected = '"Smart quotes" and - dashes...'
    out, _, _ = ascop.analyze_file(_write(tmp_path, text), DummyOptions(typographic=True))
    assert expected in out


def test_unicode_normalization(tmp_path):
    text = 'fiancé naïve coöperate'
    expected = 'fiance naive cooperate'
    out, _, _ = ascop.analyze_file(_write(tmp_path, text), DummyOptions(use_unicode=True))
    assert expected in out


def test_replace_mode(tmp_path):
    text = 'bad…stuff™'
    out, _, _ = ascop.analyze_file(_write(tmp_path, text), DummyOptions(replace='?'))
    assert '?' in out
    assert '…' not in out


def test_emoji_stripping(tmp_path):
    text = 'clean 🧼 text 😎'
    out, chars, pos = ascop.analyze_file(_write(tmp_path, text), DummyOptions(strip_stickers=True))
    assert '🧼' not in out
    assert '😎' not in out


# --- reporting path (previously uncovered) ---

def test_positions_reported(tmp_path):
    text = 'a—b…c'  # em dash at index 1, ellipsis at index 3
    out, chars, positions = ascop.analyze_file(_write(tmp_path, text), DummyOptions())
    assert chars == ['—', '…']
    assert positions == [1, 3]
    # No output-producing flag set -> content passes through unchanged.
    assert out == text


# --- encoded output ---

def test_html_entities(tmp_path):
    text = 'a—b·c'  # em dash (named: mdash), middle dot (named: middot)
    out, _, _ = ascop.analyze_file(_write(tmp_path, text), DummyOptions(encode_mode='html'))
    assert out == 'a&mdash;b&middot;c'


def test_html_entities_falls_back_to_numeric(tmp_path):
    text = '⁙'  # dotted cross (no named HTML entity)
    out, _, _ = ascop.analyze_file(_write(tmp_path, text), DummyOptions(encode_mode='html'))
    assert out == '&#x2059;'


def test_numeric_entities(tmp_path):
    text = 'em—dash'
    out, _, _ = ascop.analyze_file(_write(tmp_path, text), DummyOptions(encode_mode='numeric'))
    assert out == 'em&#x2014;dash'


def test_css_escapes_have_terminator_space(tmp_path):
    text = '·'  # middle dot U+00B7
    out, _, _ = ascop.analyze_file(_write(tmp_path, text), DummyOptions(encode_mode='css'))
    assert out == '\\0000B7 '


def test_backslash_u_bmp_and_astral(tmp_path):
    text = 'em—dash 😎'  # BMP em dash + astral emoji U+1F60E
    out, _, _ = ascop.analyze_file(_write(tmp_path, text), DummyOptions(encode_mode='backslash'))
    assert '\\u2014' in out
    assert '\\U0001F60E' in out


def test_encode_char_helper():
    assert ascop._encode_char(0x2014, 'html') == '&mdash;'
    assert ascop._encode_char(0x2014, 'numeric') == '&#x2014;'
    assert ascop._encode_char(0x00B7, 'css') == '\\0000B7 '
    assert ascop._encode_char(0x2014, 'backslash') == '\\u2014'
    assert ascop._encode_char(0x1F60E, 'backslash') == '\\U0001F60E'


# --- --check / CLI exit codes (integration via subprocess) ---

def _run(args, stdin=None):
    return subprocess.run(
        [sys.executable, 'ascop.py', *args],
        input=stdin, capture_output=True, text=True,
    )


def test_check_clean_exits_zero(tmp_path):
    clean = _write(tmp_path, 'plain ascii only\n')
    r = _run(['--check', clean])
    assert r.returncode == 0
    assert r.stdout == ''  # quiet on success


def test_check_dirty_exits_nonzero(tmp_path):
    dirty = _write(tmp_path, 'smart “quotes”\n')
    r = _run(['--check', dirty])
    assert r.returncode == 1
    assert 'non-ASCII' in r.stderr


def test_check_writes_no_output(tmp_path):
    dirty = _write(tmp_path, 'smart “quotes”\n')
    r = _run(['--check', dirty])
    assert r.stdout == ''  # linter mode never emits processed content
