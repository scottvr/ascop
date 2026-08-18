import subprocess
import sys

import polascii


class DummyOptions:
    def __init__(self, **kwargs):
        self.replace = kwargs.get('replace')
        self.use_unicode = kwargs.get('use_unicode', False)
        self.typographic = kwargs.get('typographic', False)
        self.strip_stickers = kwargs.get('strip_stickers', False)
        self.encoding = kwargs.get('encoding', 'utf-8')
        self.encode_mode = kwargs.get('encode_mode')
        self.check = kwargs.get('check', False)
        self.policy = kwargs.get('policy')


def _write(tmp_path, text):
    p = tmp_path / "sample.txt"
    p.write_text(text, encoding="utf-8")
    return str(p)


def test_ascii_pass_through(tmp_path):
    text = "Just a regular ASCII sentence."
    out, chars, pos = polascii.analyze_file(_write(tmp_path, text), DummyOptions())
    assert out == text
    assert chars == []
    assert pos == []


def test_typographic_replacement(tmp_path):
    text = '“Smart quotes” and – dashes…'
    expected = '"Smart quotes" and - dashes...'
    out, _, _ = polascii.analyze_file(_write(tmp_path, text), DummyOptions(typographic=True))
    assert expected in out


def test_unicode_normalization(tmp_path):
    text = 'fiancé naïve coöperate'
    expected = 'fiance naive cooperate'
    out, _, _ = polascii.analyze_file(_write(tmp_path, text), DummyOptions(use_unicode=True))
    assert expected in out


def test_replace_mode(tmp_path):
    text = 'bad…stuff™'
    out, _, _ = polascii.analyze_file(_write(tmp_path, text), DummyOptions(replace='?'))
    assert '?' in out
    assert '…' not in out


def test_emoji_stripping(tmp_path):
    text = 'clean 🧼 text 😎'
    out, chars, pos = polascii.analyze_file(_write(tmp_path, text), DummyOptions(strip_stickers=True))
    assert '🧼' not in out
    assert '😎' not in out


# --- reporting path (previously uncovered) ---

def test_positions_reported(tmp_path):
    text = 'a—b…c'  # em dash at index 1, ellipsis at index 3
    out, chars, positions = polascii.analyze_file(_write(tmp_path, text), DummyOptions())
    assert chars == ['—', '…']
    assert positions == [1, 3]
    # No output-producing flag set -> content passes through unchanged.
    assert out == text


# --- encoded output ---

def test_html_entities(tmp_path):
    text = 'a—b·c'  # em dash (named: mdash), middle dot (named: middot)
    out, _, _ = polascii.analyze_file(_write(tmp_path, text), DummyOptions(encode_mode='html'))
    assert out == 'a&mdash;b&middot;c'


def test_html_entities_falls_back_to_numeric(tmp_path):
    text = '⁙'  # dotted cross (no named HTML entity)
    out, _, _ = polascii.analyze_file(_write(tmp_path, text), DummyOptions(encode_mode='html'))
    assert out == '&#x2059;'


def test_numeric_entities(tmp_path):
    text = 'em—dash'
    out, _, _ = polascii.analyze_file(_write(tmp_path, text), DummyOptions(encode_mode='numeric'))
    assert out == 'em&#x2014;dash'


def test_css_escapes_have_terminator_space(tmp_path):
    text = '·'  # middle dot U+00B7
    out, _, _ = polascii.analyze_file(_write(tmp_path, text), DummyOptions(encode_mode='css'))
    assert out == '\\0000B7 '


def test_backslash_u_bmp_and_astral(tmp_path):
    text = 'em—dash 😎'  # BMP em dash + astral emoji U+1F60E
    out, _, _ = polascii.analyze_file(_write(tmp_path, text), DummyOptions(encode_mode='backslash'))
    assert '\\u2014' in out
    assert '\\U0001F60E' in out


def test_encode_char_helper():
    assert polascii._encode_char(0x2014, 'html') == '&mdash;'
    assert polascii._encode_char(0x2014, 'numeric') == '&#x2014;'
    assert polascii._encode_char(0x00B7, 'css') == '\\0000B7 '
    assert polascii._encode_char(0x2014, 'backslash') == '\\u2014'
    assert polascii._encode_char(0x1F60E, 'backslash') == '\\U0001F60E'


# --- --check / CLI exit codes (integration via subprocess) ---

import os

_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'polascii.py')

def _run(args, stdin=None):
    return subprocess.run(
        [sys.executable, _SCRIPT, *args],
        input=stdin, capture_output=True, text=True,
    )

def _run_in(cwd, args, stdin=None):
    return subprocess.run(
        [sys.executable, _SCRIPT, *args],
        input=stdin, capture_output=True, text=True, cwd=str(cwd),
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


# --- classification of dangerous / deceptive Unicode ---

def test_classify_bidi_control():
    cat, _ = polascii._cluster_category('‮')  # RIGHT-TO-LEFT OVERRIDE
    assert cat == 'bidi-control'


def test_classify_invisible():
    cat, _ = polascii._cluster_category('​')  # ZERO WIDTH SPACE
    assert cat == 'invisible'


def test_classify_homoglyph():
    cat, detail = polascii._cluster_category('а')  # Cyrillic 'a'
    assert cat == 'homoglyph'
    assert "'a'" in detail


def test_classify_zwj_emoji_is_emoji_not_invisible():
    # ZWJ family sequence: the internal U+200D must NOT be flagged as invisible.
    family = '\U0001F468‍\U0001F469‍\U0001F467'
    cat, _ = polascii._cluster_category(family)
    assert cat == 'emoji'


def test_classify_benign_accent_is_non_ascii():
    cat, _ = polascii._cluster_category('é')
    assert cat == 'non-ascii'


def test_format_finding_does_not_echo_bidi():
    # A bidi override must never be reproduced raw in report text.
    line = polascii._format_finding('‮', 5)
    assert '‮' not in line
    assert 'U+202E' in line
    assert 'bidi-control' in line


def test_format_finding_shows_safe_glyph():
    # A homoglyph is safe (and useful) to display raw.
    line = polascii._format_finding('а', 3)
    assert 'а' in line
    assert 'homoglyph' in line


# --- --security audit mode (integration via subprocess) ---

def test_security_flags_bidi(tmp_path):
    f = _write(tmp_path, 'ok = "x"  # ‮evil‬\n')  # Trojan Source
    r = _run(['--security', f])
    assert r.returncode == 1
    assert 'bidi-control' in r.stderr
    assert '‮' not in r.stderr  # never echo the raw override


def test_security_flags_invisible(tmp_path):
    f = _write(tmp_path, 'pass​word\n')
    r = _run(['--security', f])
    assert r.returncode == 1
    assert 'invisible' in r.stderr


def test_security_flags_homoglyph(tmp_path):
    f = _write(tmp_path, 'pаypal.com\n')  # Cyrillic 'a'
    r = _run(['--security', f])
    assert r.returncode == 1
    assert 'homoglyph' in r.stderr


def test_security_ignores_benign_accents(tmp_path):
    # The whole point: legitimate UTF-8 must NOT fail a security audit.
    f = _write(tmp_path, 'naïve café fiancé\n')
    r = _run(['--security', f])
    assert r.returncode == 0
    assert r.stdout == ''
    assert r.stderr == ''


def test_security_ignores_zwj_emoji(tmp_path):
    f = _write(tmp_path, 'family \U0001F468‍\U0001F469‍\U0001F467 ok\n')
    r = _run(['--security', f])
    assert r.returncode == 0  # internal ZWJ is legitimate, not smuggling


def test_check_warns_on_dangerous_without_verbose(tmp_path):
    # --check surfaces dangerous classes even without -v.
    f = _write(tmp_path, 'x‮y\n')
    r = _run(['--check', f])
    assert r.returncode == 1
    assert 'WARNING' in r.stderr
    assert 'bidi-control' in r.stderr


# --- allow-list: Policy unit tests ---

GREEK_A = 'α'      # homoglyph for 'a'
CYRILLIC_A = 'а'   # homoglyph for 'a'
NBSP = ' '
EN_DASH = '–'

def test_policy_subgroup_greek_only():
    p = polascii.build_policy(['homoglyph:greek'])
    assert p.allows(GREEK_A) is True
    assert p.allows(CYRILLIC_A) is False


def test_policy_whole_category():
    p = polascii.build_policy(['homoglyph'])
    assert p.allows(GREEK_A) is True
    assert p.allows(CYRILLIC_A) is True


def test_policy_codepoint():
    p = polascii.build_policy(['U+00A0'])
    assert p.allows(NBSP) is True
    assert p.allows(EN_DASH) is False


def test_policy_range():
    p = polascii.build_policy(['U+2010-U+2015'])
    assert p.allows(EN_DASH) is True       # 0x2013 is inside
    assert p.allows(NBSP) is False


def test_policy_bidi_control_token_is_category_not_range():
    # 'bidi-control' contains a hyphen but must parse as a category, not a range.
    p = polascii.build_policy(['bidi-control'])
    assert ('bidi-control' in p.categories) or p.allows('‮')


def test_policy_bad_token_raises():
    import pytest
    with pytest.raises(ValueError):
        polascii.build_policy(['definitely-not-a-token'])


def test_empty_policy_is_falsy():
    assert not polascii.build_policy([])


# --- allow-list: end-to-end behavior ---

def test_allow_greek_passes_but_cyrillic_still_fails(tmp_path):
    greek = _write(tmp_path, f'value {GREEK_A}\n')
    r = _run(['--security', '--allow', 'homoglyph:greek', greek])
    assert r.returncode == 0

    cyr = tmp_path / "cyr.txt"
    cyr.write_text(f'p{CYRILLIC_A}ypal\n', encoding='utf-8')
    r2 = _run(['--security', '--allow', 'homoglyph:greek', str(cyr)])
    assert r2.returncode == 1
    assert 'homoglyph' in r2.stderr


def test_allow_codepoint_makes_check_pass(tmp_path):
    f = _write(tmp_path, 'it’s fine\n')  # curly apostrophe
    clean = _run(['--check', '--allow', 'U+2019', f])
    assert clean.returncode == 0
    # Without the allowance it should fail.
    dirty = _run(['--check', f])
    assert dirty.returncode == 1


def test_allow_reports_count_under_verbose(tmp_path):
    f = _write(tmp_path, 'it’s fine\n')
    r = _run(['--check', '-v', '--allow', 'U+2019', f])
    assert r.returncode == 0
    assert 'allowed by policy' in r.stderr


def test_allow_file_discovered(tmp_path):
    (tmp_path / polascii.ALLOW_FILENAME).write_text(
        "# repo policy\nhomoglyph:greek\n", encoding='utf-8')
    target = tmp_path / "doc.txt"
    target.write_text(f'alpha {GREEK_A}\n', encoding='utf-8')
    # Run with cwd = tmp_path so the .polascii-allow file is discovered.
    r = _run_in(tmp_path, ['--security', str(target)])
    assert r.returncode == 0
    # --no-config ignores the file, so the greek homoglyph fails again.
    r2 = _run_in(tmp_path, ['--security', '--no-config', str(target)])
    assert r2.returncode == 1


def test_allow_passthrough_leaves_char_unfolded(tmp_path):
    # A policy-allowed char must not be transformed by -t either.
    policy = polascii.build_policy(['U+2019'])
    out, _, _ = polascii.analyze_file(
        _write(tmp_path, 'it’s'),
        DummyOptions(typographic=True, policy=policy))
    assert '’' in out          # left alone
    assert out == 'it’s'
