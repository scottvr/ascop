# ascop -- project guide for Claude Code

`ascop` (ascii cop / ascii operator) is a small, single-file CLI that restores
plain ASCII by undoing "smart" punctuation and other unsolicited Unicode. It is
a POLA-restorer, not a transliterator: it folds the *specific* smart
substitutions back to the ASCII the user actually typed (em dash -> `--`, curly
quotes -> `"`/`'`, ellipsis -> `...`), and it treats reporting (list / count /
positions) as a first-class mode. Keep it 7-bit in spirit and plain ASCII in its
own source/docs.

## Layout
- `ascop.py`   -- the whole tool (argparse CLI + `analyze_file`).
- `test_ascop.py` -- pytest suite (currently 5 tests).
- `requirements.txt` -- `regex`, `grapheme` (third-party).
- `README.md`  -- the philosophy (POLA/DWIM/WYSIWYG) and usage; worth a read.

## Dev workflow
Use the venv at `~/.venv` (has regex, grapheme, pytest):

    source ~/.venv/bin/activate
    python -m pytest -q test_ascop.py        # run tests
    python ascop.py -t somefile.txt          # typographic fold to stdout
    echo 'smart "text"...' | python ascop.py -t   # stdin

Options today: `-r/--replace CHAR`, `-l/--list`, `-c/--count`, `-o/--output`,
`-e/--encoding`, `-u/--use-unicode` (NFKD), `-t/--typographic`,
`-s/--strip-stickers` (emoji removal), `-v/--verbose`.

## Architecture notes
- `TYPOGRAPHIC_MAP` (top of `ascop.py`) -- the curated codepoint -> ASCII table.
  The README explicitly invites additions here; keep it the extension point.
- `analyze_file()` -- single O(n) pass over `grapheme.graphemes(content)`.
  Grapheme clusters (not bare codepoints) are the unit so multi-codepoint
  graphemes like ZWJ emoji stay intact for stripping. Returns
  `(processed_text, non_ascii_clusters, positions)`; positions are code-point
  offsets.
- `main()` -- argparse; writes processed output only when `-r` or `-t` is set;
  reporting (`-l`/`-c`) goes to stderr via `_codepoints()` (handles
  multi-codepoint clusters).

## Recent state (2026-08-17)
Two confirmed bugs were fixed:
1. `analyze_file` had an O(n^2) nested grapheme loop (30 KB took ~50 s); it is
   now a single O(n) pass (~0.2 s).
2. `-l`/`-c` called `ord()` on grapheme clusters and crashed on multi-codepoint
   graphemes (ZWJ emoji); now formatted via `_codepoints()`.
Tests still pass 5/5.

## Roadmap (highest-value first)
These two would turn ascop from a personal script into something worth adopting,
and would let it replace the hand-rolled `ascii_harden` in the sibling
`GUM_of_Devops` repo and serve as that repo's pre-commit gate:

1. `--check` (linter/CI mode): exit non-zero if any non-ASCII is found, quiet on
   success. Makes ascop a pre-commit / CI gate.
2. Encoded output (not just folding). Every competitor (unidecode, recode,
   iconv //TRANSLIT) transliterates and destroys the glyph; none offer "keep the
   glyph, encode it 7-bit for the target format." Add:
   - `--html-entities`  em dash -> `&mdash;`, middle dot -> `&middot;`, etc.
   - `--css-escapes`    -> `\0000B7` **with a trailing terminator space** (a CSS
     unicode escape consumes one following whitespace, so emit two to render one
     visible space -- learned the hard way in GUM_of_Devops).
   - `--numeric`        -> `&#x2014;`
   - `--backslash-u`    -> `—` (for source strings)

Supporting ideas (lower priority): in-place `-i` with `.bak`; directory
recursion honoring `.gitignore`; `--diff` dry-run; config-file custom maps
(TOML/JSON) so users extend without forking; `line:col` positions; `--json`
output; per-category toggles (quotes/dashes/spaces/accents/currency/emoji);
format profiles (`--profile html|source|markdown`; markdown code-fence-aware is
the hard, valuable one).

## Known limitations / cleanups
- `_is_emoji_cluster` uses `\p{Emoji}` per code point, but ZWJ (U+200D),
  variation selectors, and skin-tone modifiers are NOT `\p{Emoji}` -- so a
  multi-part ZWJ emoji cluster is not recognized and `-s` won't strip it. Fix:
  treat joiners/modifiers/VS as emoji-cluster members (cluster is emoji if it
  contains any `\p{Emoji}` and the rest are joiners/modifiers).
- `\p{Emoji}` also matches ASCII digits, `#`, and `*`; today that's masked
  because the check only runs inside the non-ASCII branch -- watch this if
  refactoring.
- `_remove_unicode_emoji()` is defined but unused (wire into `-s` or delete).
- Tests write `test.txt` into the cwd (should use `tmp_path`) and cover neither
  the reporting path (`-l`/`-c`) nor performance -- add cases for both.

## Style
Plain ASCII in source and docs (this tool is about 7-bit hygiene -- dogfood it).
Keep it a focused single-file tool; the README deliberately resists feature
creep toward being `recode`. New folds belong in `TYPOGRAPHIC_MAP`.
