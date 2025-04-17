import io
import types
import ascop

class DummyOptions:
    def __init__(self, **kwargs):
        self.replace = kwargs.get('replace')
        self.use_unicode = kwargs.get('use_unicode', False)
        self.typographic = kwargs.get('typographic', False)
        self.strip_stickers = kwargs.get('strip_stickers', False)
        self.encoding = kwargs.get('encoding', 'utf-8')

def test_ascii_pass_through():
    text = "Just a regular ASCII sentence."
    with open("test.txt", "w", encoding="utf-8") as f:
        f.write(text)
    out, chars, pos = ascop.analyze_file("test.txt", DummyOptions())
    assert out == text
    assert chars == []
    assert pos == []

def test_typographic_replacement():
    text = '“Smart quotes” and – dashes…'
    expected = '"Smart quotes" and - dashes...'
    with open("test.txt", "w", encoding="utf-8") as f:
        f.write(text)
    out, _, _ = ascop.analyze_file("test.txt", DummyOptions(typographic=True))
    assert expected in out

def test_unicode_normalization():
    text = 'fiancé naïve coöperate'
    expected = 'fiance naive cooperate'
    with open("test.txt", "w", encoding="utf-8") as f:
        f.write(text)
    out, _, _ = ascop.analyze_file("test.txt", DummyOptions(use_unicode=True))
    assert expected in out

def test_replace_mode():
    text = 'bad…stuff™'
    with open("test.txt", "w", encoding="utf-8") as f:
        f.write(text)
    out, _, _ = ascop.analyze_file("test.txt", DummyOptions(replace='?'))
    assert '?' in out
    assert '…' not in out

def test_emoji_stripping():
    text = 'clean 🧼 text 😎'
    with open("test.txt", "w", encoding="utf-8") as f:
        f.write(text)
    out, chars, pos = ascop.analyze_file("test.txt", DummyOptions(strip_stickers=True))
    assert '🧼' not in out
    assert '😎' not in out
