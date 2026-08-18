#!/usr/bin/python3

# polascii - POLA + ASCII (say it like a Polish surname; "pola" for short).
# Formerly "ascop" (the ascii cop / ascii operator) -- see ascop.py for the
# backward-compatible alias.

# a simple tool to un-smarten (endumben?) the damage "Smart" punctuation
# does do to plain text.
#
# When I input via a qwerty keyboard labeled with 7-bit ascii characters
# that's what I expect to have typed. I might have grown to excuse
# a Word processor because I'm sure for many people that is saving them effort
# but for me, if I type in a simple note-taking app and copy-paste or send-to
# something like SMS, I just want the text I intended to write.

"""
Usage:
  polascii.py [options] [FILE...]

Options:
  -h, --help            Show this help message and exit
  -r, --replace CHAR    Replace non-ASCII chars with CHAR (defaults to reporting only)
  -l, --list            List all non-ASCII characters found with their positions
  -c, --count           Count occurrences of each non-ASCII character
  -o, --output FILE     Write output to FILE instead of stdout
  -e, --encoding ENC    Specify input encoding (default: utf-8)
  -u, --use-unicode     Replace with similar-looking Unicode characters when possible,
  -s, --strip-stickers  remove emoji, pictographs, and other Unicode sticker-type glyphs
                        that don't belong in a terminal, text file, or serious conversation.
  --check               Linter/CI mode: exit non-zero if any non-ASCII is found,
                        quiet on success. Writes no output.
  --security            Security audit: exit non-zero only on DANGEROUS Unicode
                        (bidi controls / Trojan Source, bare zero-width and
                        invisible characters, homoglyphs), ignoring benign UTF-8.
  --allow SPEC          Carve exceptions out of detection/handling. SPEC is a
                        comma-list of: a category (bidi, invisible, homoglyph,
                        emoji), a script subgroup (homoglyph:greek), a code
                        point (U+00A0), or a range (U+2010-U+2015). Repeatable.
                        Also read from a .polascii-allow file (see --no-config).
  --no-config           Ignore any .polascii-allow file; use only --allow.
  --html-entities       Encode non-ASCII as HTML entities (em dash -> &mdash;)
  --numeric             Encode non-ASCII as hex numeric refs (em dash -> &#x2014;)
  --css-escapes         Encode non-ASCII as CSS unicode escapes (middot -> \\0000B7 )
  --backslash-u         Encode non-ASCII as source-string escapes (em dash -> \\u2014)

Examples:
  polascii.py file.txt                      # Report non-ASCII characters
  polascii.py -r '?' file.txt               # Replace with question marks
  polascii.py -l -c file.txt                # List and count occurrences
  polascii.py --check src/*.py              # Fail (exit 1) if any file has non-ASCII
  polascii.py --security src/*.py           # Fail only on bidi/invisible/homoglyph
  polascii.py --security --allow homoglyph:greek src/*.py   # ... but allow Greek
  polascii.py --html-entities page.html     # Keep the glyph, encode it for HTML
  cat file.txt | polascii.py -r '_' -o clean.txt  # Read from stdin, write to file
"""

import os
import sys
import argparse
import unicodedata
import html.entities
import regex
import grapheme
from collections import Counter

ALLOW_FILENAME = '.polascii-allow'

# Typographic replacement map for smart quotes and other fancy characters
TYPOGRAPHIC_MAP = {
    # Smart quotes
    '\u201c': '"',    # Left double quotation mark
    '\u201d': '"',    # Right double quotation mark
    '\u2018': "'",    # Left single quotation mark
    '\u2019': "'",    # Right single quotation mark
    '\u201a': "'",    # Single low-9 quotation mark
    '\u201b': "'",    # Single high-reversed-9 quotation mark
    '\u201e': '"',    # Double low-9 quotation mark
    '\u201f': '"',    # Double high-reversed-9 quotation mark
    
    # Dashes
    '\u2013': '-',    # En dash
    '\u2014': '--',   # Em dash
    '\u2015': '--',   # Horizontal bar
    '\u2212': '-',    # Minus sign
    
    # Other typographic characters
    '\u2026': '...',  # Ellipsis
    '\u2022': '*',    # Bullet
    '\u2023': '>',    # Triangular bullet
    '\u00a0': ' ',    # Non-breaking space
    '\u00ad': '-',    # Soft hyphen
    
    # Spaces
    '\u2000': ' ',    # En quad
    '\u2001': ' ',    # Em quad
    '\u2002': ' ',    # En space
    '\u2003': ' ',    # Em space
    '\u2004': ' ',    # Three-per-em space
    '\u2005': ' ',    # Four-per-em space
    '\u2006': ' ',    # Six-per-em space
    '\u2007': ' ',    # Figure space
    '\u2008': ' ',    # Punctuation space
    '\u2009': ' ',    # Thin space
    '\u200a': ' ',    # Hair space
    '\u200b': '',     # Zero width space
    '\u200c': '',     # Zero width non-joiner
    '\u200d': '',     # Zero width joiner
    
    # Ligatures
    '\ufb01': 'fi',   # latin small ligature fi
    '\ufb02': 'fl',   # latin small ligature fl
    
    # Common accented characters
    '\u00e0': 'a',    # latin small letter a with grave
    '\u00e1': 'a',    # latin small letter a with acute
    '\u00e2': 'a',    # latin small letter a with circumflex
    '\u00e3': 'a',    # latin small letter a with tilde
    '\u00e4': 'a',    # latin small letter a with diaeresis
    '\u00e5': 'a',    # latin small letter a with ring above
    '\u00e8': 'e',    # latin small letter e with grave
    '\u00e9': 'e',    # latin small letter e with acute
    '\u00ea': 'e',    # latin small letter e with circumflex
    '\u00eb': 'e',    # latin small letter e with diaeresis
    '\u00ec': 'i',    # latin small letter i with grave
    '\u00ed': 'i',    # latin small letter i with acute
    '\u00ee': 'i',    # latin small letter i with circumflex
    '\u00ef': 'i',    # latin small letter i with diaeresis
    '\u00f2': 'o',    # latin small letter o with grave
    '\u00f3': 'o',    # latin small letter o with acute
    '\u00f4': 'o',    # latin small letter o with circumflex
    '\u00f5': 'o',    # latin small letter o with tilde
    '\u00f6': 'o',    # latin small letter o with diaeresis
    '\u00f9': 'u',    # latin small letter u with grave
    '\u00fa': 'u',    # latin small letter u with acute
    '\u00fb': 'u',    # latin small letter u with circumflex
    '\u00fc': 'u',    # latin small letter u with diaeresis
    '\u00f1': 'n',    # latin small letter n with tilde
    '\u00ff': 'y',    # latin small letter y with diaeresis
    '\u00fd': 'y',    # latin small letter y with acute
    '\u00e7': 'c',    # latin small letter c with cedilla
    
    # Currency
    '\u20ac': 'EUR',  # Euro sign
    '\u00a3': 'GBP',  # Pound sign
    '\u00a5': 'JPY',  # Yen sign
}

# --- Dangerous / deceptive Unicode ------------------------------------------
# These are the security-relevant classes: characters that do not just look
# wrong, but can actively mislead a human or a parser. `--check` names them and
# `--security` fails a build on them while leaving benign UTF-8 (accents, etc.)
# alone. Like TYPOGRAPHIC_MAP, these tables are the intended extension point.

# Bidirectional control characters. They can make source or text *display*
# differently from how it *parses* -- the "Trojan Source" attack
# (CVE-2021-42574). Almost never legitimate in code or plain text.
# (Kept as \u escapes so this source stays 7-bit and passes its own --check.)
BIDI_CONTROLS = {
    '\u202a': 'LEFT-TO-RIGHT EMBEDDING',
    '\u202b': 'RIGHT-TO-LEFT EMBEDDING',
    '\u202c': 'POP DIRECTIONAL FORMATTING',
    '\u202d': 'LEFT-TO-RIGHT OVERRIDE',
    '\u202e': 'RIGHT-TO-LEFT OVERRIDE',
    '\u2066': 'LEFT-TO-RIGHT ISOLATE',
    '\u2067': 'RIGHT-TO-LEFT ISOLATE',
    '\u2068': 'FIRST STRONG ISOLATE',
    '\u2069': 'POP DIRECTIONAL ISOLATE',
    '\u200e': 'LEFT-TO-RIGHT MARK',
    '\u200f': 'RIGHT-TO-LEFT MARK',
    '\u061c': 'ARABIC LETTER MARK',
}

# Zero-width and otherwise invisible characters. Some have legitimate uses (ZWJ
# inside an emoji sequence, a BOM at the very start of a file) -- those are
# handled at the cluster level so we do not cry wolf -- but a bare one in prose
# or source is a classic vector for hiding text, watermarking, or smuggling.
INVISIBLE_CHARS = {
    '\u200b': 'ZERO WIDTH SPACE',
    '\u200c': 'ZERO WIDTH NON-JOINER',
    '\u200d': 'ZERO WIDTH JOINER',
    '\u2060': 'WORD JOINER',
    '\ufeff': 'ZERO WIDTH NO-BREAK SPACE (BOM)',
    '\u180e': 'MONGOLIAN VOWEL SEPARATOR',
    '\u00ad': 'SOFT HYPHEN',
}

# Homoglyphs: non-ASCII letters that look like ASCII ones -- the IDN / "paypaI"
# homograph trick. A curated set of the common Latin lookalikes mapped to the
# ASCII they mimic. This is deliberately small and additive, like TYPOGRAPHIC_MAP.
CONFUSABLES = {
    # Cyrillic lowercase
    '\u0430': 'a', '\u0435': 'e', '\u043e': 'o', '\u0440': 'p',
    '\u0441': 'c', '\u0443': 'y', '\u0445': 'x', '\u0455': 's',
    '\u0456': 'i', '\u0458': 'j',
    # Cyrillic uppercase
    '\u0410': 'A', '\u0412': 'B', '\u0415': 'E', '\u041a': 'K',
    '\u041c': 'M', '\u041d': 'H', '\u041e': 'O', '\u0420': 'P',
    '\u0421': 'C', '\u0422': 'T', '\u0425': 'X',
    # Greek
    '\u03b1': 'a', '\u03bf': 'o', '\u03c1': 'p', '\u03bd': 'v',
    '\u0391': 'A', '\u0392': 'B', '\u0395': 'E', '\u0396': 'Z',
    '\u0397': 'H', '\u0399': 'I', '\u039a': 'K', '\u039c': 'M',
    '\u039d': 'N', '\u039f': 'O', '\u03a1': 'P', '\u03a4': 'T',
    '\u03a5': 'Y', '\u03a7': 'X',
}

# Categories that `--security` treats as a failure.
DANGEROUS_CATEGORIES = frozenset({'bidi-control', 'invisible', 'homoglyph'})

# --allow accepts short category names; map them to the classification labels.
_CATEGORY_ALIASES = {
    'bidi': 'bidi-control',
    'bidi-control': 'bidi-control',
    'invisible': 'invisible',
    'homoglyph': 'homoglyph',
    'emoji': 'emoji',
}


def _script(cp):
    """Coarse script of a code point, enough for homoglyph subgroups. (Python's
    stdlib has no script property, so we use block ranges.)"""
    if 0x0370 <= cp <= 0x03ff or 0x1f00 <= cp <= 0x1fff:
        return 'greek'
    if 0x0400 <= cp <= 0x052f:
        return 'cyrillic'
    if cp < 0x0250:
        return 'latin'
    return 'other'


class Policy:
    """An allow-list of exceptions carved out of the safe default. A code point
    (and the cluster carrying it) is allowed if it matches an allowed category,
    a script subgroup (e.g. homoglyph:greek), an explicit code point, or a
    range. Allowed clusters are passed through untouched and never counted as a
    violation -- 'this is acceptable; hands off.'"""

    def __init__(self, categories=None, subgroups=None, codepoints=None, ranges=None):
        self.categories = set(categories or ())
        self.subgroups = set(subgroups or ())      # set of (category, script)
        self.codepoints = set(codepoints or ())    # set of int
        self.ranges = list(ranges or ())           # list of (lo, hi)

    def __bool__(self):
        return bool(self.categories or self.subgroups
                    or self.codepoints or self.ranges)

    def _cp_allowed(self, cp, category):
        if cp in self.codepoints:
            return True
        if any(lo <= cp <= hi for lo, hi in self.ranges):
            return True
        if (category, _script(cp)) in self.subgroups:
            return True
        return False

    def allows(self, cluster):
        """True if the whole cluster is acceptable under this policy."""
        category = _cluster_category(cluster)[0]
        if category in self.categories:
            return True
        non_ascii = [ord(c) for c in cluster if ord(c) >= 128]
        if not non_ascii:
            return False
        return all(self._cp_allowed(cp, category) for cp in non_ascii)


def _parse_allow_token(token):
    """Parse one --allow / .polascii-allow token into a partial Policy spec.
    Returns (categories, subgroups, codepoints, ranges). Unknown tokens raise
    ValueError so typos are caught rather than silently ignored."""
    token = token.strip()
    if not token:
        return set(), set(), set(), []

    def _hex(s):
        s = s.strip()
        if s.upper().startswith('U+'):
            s = s[2:]
        return int(s, 16)

    if ':' in token:
        cat, _, sub = token.partition(':')
        cat = _CATEGORY_ALIASES.get(cat.strip().lower())
        if cat is None:
            raise ValueError(f"unknown category in '{token}'")
        return set(), {(cat, sub.strip().lower())}, set(), []

    # A bare category name (check before ranges so 'bidi-control' is not
    # mistaken for a hex range).
    low = token.lower()
    if low in _CATEGORY_ALIASES:
        return {_CATEGORY_ALIASES[low]}, set(), set(), []

    if '-' in token:
        # Range: U+2010-U+2015 (both sides must parse as hex).
        lo_s, _, hi_s = token.partition('-')
        try:
            lo, hi = _hex(lo_s), _hex(hi_s)
        except ValueError:
            raise ValueError(f"bad range '{token}'")
        if lo > hi:
            lo, hi = hi, lo
        return set(), set(), set(), [(lo, hi)]

    # Otherwise a single code point (U+XXXX or bare hex).
    try:
        return set(), set(), {_hex(token)}, []
    except ValueError:
        raise ValueError(f"unrecognized --allow token '{token}'")


def build_policy(allow_tokens):
    """Build a Policy from an iterable of raw tokens (from --allow and/or a
    .polascii-allow file)."""
    cats, subs, cps, ranges = set(), set(), set(), []
    for tok in allow_tokens:
        c, s, p, r = _parse_allow_token(tok)
        cats |= c
        subs |= s
        cps |= p
        ranges += r
    return Policy(cats, subs, cps, ranges)


def _iter_allow_file_tokens(path):
    """Yield tokens from a .polascii-allow file: one or more per line, split on
    whitespace/commas, with '#' comments and blank lines ignored."""
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.split('#', 1)[0]
            for tok in line.replace(',', ' ').split():
                yield tok


def find_allow_file(start_dir):
    """Search start_dir and its ancestors for a .polascii-allow file; return the
    path of the nearest one, or None."""
    d = os.path.abspath(start_dir)
    while True:
        candidate = os.path.join(d, ALLOW_FILENAME)
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def _remove_unicode_emoji(text):
    return regex.sub(r'\p{Emoji}', '', text)

def _is_emoji_cluster(cluster):
    return all(regex.match(r'\p{Emoji}', c) for c in cluster)

def _codepoints(cluster):
    """Format a grapheme cluster as its U+ code points (handles multi-codepoint
    clusters like ZWJ emoji, which ord() cannot)."""
    return ' '.join(f"U+{ord(c):04X}" for c in cluster)

def _cluster_category(cluster):
    """Classify a non-ASCII grapheme cluster for reporting. Returns
    (category, detail).

    Emoji clusters are recognized as a whole so their internal joiners (ZWJ)
    and variation selectors are not mis-flagged as smuggled invisibles. The
    dangerous classes -- bidi controls, bare zero-width/invisible characters,
    and homoglyphs -- are named explicitly; everything else falls back to the
    Unicode name of its first non-ASCII code point.

    Categories: 'emoji', 'bidi-control', 'invisible', 'homoglyph', 'non-ascii'.
    """
    # A cluster carrying any Emoji code point is an emoji grapheme; its joiners
    # are legitimate, so do not treat them as invisible-character smuggling.
    if any(regex.match(r'\p{Emoji}', c) for c in cluster):
        return ('emoji', 'emoji / pictograph')

    for c in cluster:
        if c in BIDI_CONTROLS:
            return ('bidi-control', BIDI_CONTROLS[c])
        if c in INVISIBLE_CHARS:
            return ('invisible', INVISIBLE_CHARS[c])
        if c in CONFUSABLES:
            return ('homoglyph', f"looks like ASCII '{CONFUSABLES[c]}'")

    for c in cluster:
        if ord(c) >= 128:
            try:
                return ('non-ascii', unicodedata.name(c))
            except ValueError:
                return ('non-ascii', 'unnamed code point')
    return ('non-ascii', 'non-ASCII')

def _format_finding(cluster, pos):
    """Render one flagged cluster for a lint report: code points, category, and
    a human name. Bidi controls and invisible characters are NOT echoed raw --
    printing an override or a zero-width into a terminal is itself a hazard --
    so only their code points and names are shown."""
    category, detail = _cluster_category(cluster)
    cps = _codepoints(cluster)
    if category in ('bidi-control', 'invisible'):
        return f"{cps} [{category}] {detail} at position {pos}"
    return f"{cps} '{cluster}' [{category}] {detail} at position {pos}"

def _encode_char(cp, mode):
    """Encode a single non-ASCII code point 7-bit for the target format.
    Keeps the glyph's identity (unlike a fold) so it round-trips."""
    if mode == 'html':
        # Named entity when one exists (em dash -> &mdash;), else hex numeric.
        name = html.entities.codepoint2name.get(cp)
        if name is not None:
            return f'&{name};'
        return f'&#x{cp:X};'
    if mode == 'numeric':
        # Hex numeric character reference (em dash -> &#x2014;).
        return f'&#x{cp:X};'
    if mode == 'css':
        # CSS unicode escape. A CSS escape consumes exactly one trailing
        # whitespace as its terminator, so we always emit one space to close it
        # (middle dot -> "\0000B7 "). Note: to render a literal space that
        # follows, the caller needs a second space -- the escape eats the first.
        return f'\\{cp:06X} '
    if mode == 'backslash':
        # Source-string escape (Python/JS): \uXXXX for the BMP, \UXXXXXXXX above.
        if cp <= 0xFFFF:
            return f'\\u{cp:04X}'
        return f'\\U{cp:08X}'
    raise ValueError(f"unknown encode mode: {mode!r}")

def _encode_cluster(cluster, mode):
    """Encode the non-ASCII code points of a cluster, passing ASCII through."""
    return ''.join(
        c if ord(c) < 128 else _encode_char(ord(c), mode) for c in cluster
    )

def analyze_file(file, options):
    try:
        if file == '-':
            content = sys.stdin.read()
        else:
            with open(file, 'r', encoding=options.encoding) as f:
                content = f.read()
    except UnicodeDecodeError as e:
        print(f"Error decoding {file} using {options.encoding}: {e}", file=sys.stderr)
        return None, None, None
    
    non_ascii_chars = []
    positions = []
    processed_content = []

    # One pass over grapheme clusters, O(n). Clusters keep multi-codepoint
    # graphemes (e.g. ZWJ emoji sequences) intact so stripping removes them
    # whole. `index` tracks the code-point offset for position reporting.
    index = 0
    for cluster in grapheme.graphemes(content):
        start = index
        index += len(cluster)

        if all(ord(c) < 128 for c in cluster):
            processed_content.append(cluster)
            continue

        # This cluster contains non-ASCII: record it for reporting.
        non_ascii_chars.append(cluster)
        positions.append(start)

        # Allow-list: this cluster is acceptable under policy -- pass it through
        # untouched (no fold, strip, encode, or replace) and do not act on it.
        # It stays in non_ascii_chars so reporting can account for it; main()
        # re-checks the policy to exclude allowed clusters from pass/fail.
        policy = getattr(options, 'policy', None)
        if policy and policy.allows(cluster):
            processed_content.append(cluster)
            continue

        # Strip stickers (whole emoji grapheme) if requested.
        if options.strip_stickers and _is_emoji_cluster(cluster):
            continue  # omit from output entirely

        # Normalize to ASCII via NFKD if requested.
        if options.use_unicode:
            normalized = unicodedata.normalize('NFKD', cluster)
            ascii_normalized = ''.join(c for c in normalized if ord(c) < 128)
            if ascii_normalized:
                processed_content.append(ascii_normalized)
                continue
            cluster = normalized  # no ASCII form; fall through normalized

        # Encoded output: keep the glyph's identity but render it 7-bit for the
        # target format (HTML entities, CSS escapes, source-string escapes).
        # Takes precedence over the typographic fold and -r.
        if getattr(options, 'encode_mode', None):
            processed_content.append(_encode_cluster(cluster, options.encode_mode))
            continue

        # Typographic mapping, applied per code point within the cluster.
        if options.typographic and any(c in TYPOGRAPHIC_MAP for c in cluster):
            processed_content.append(''.join(TYPOGRAPHIC_MAP.get(c, c) for c in cluster))
            continue

        # Fallback replacement.
        if options.replace is not None:
            processed_content.append(options.replace)
        else:
            processed_content.append(cluster)

    return ''.join(processed_content), non_ascii_chars, positions

def main():
    parser = argparse.ArgumentParser(description="Detect and handle non-ASCII characters")
    parser.add_argument('files', metavar='FILE', nargs='*', default=['-'],
                        help='Files to process (default: stdin)')
    parser.add_argument('-r', '--replace', metavar='CHAR', 
                        help='Replace non-ASCII chars with CHAR')
    parser.add_argument('-l', '--list', action='store_true',
                        help='List all non-ASCII characters found with positions')
    parser.add_argument('-c', '--count', action='store_true',
                        help='Count occurrences of each non-ASCII character')
    parser.add_argument('-o', '--output', metavar='FILE',
                        help='Write output to FILE instead of stdout')
    parser.add_argument('-e', '--encoding', default='utf-8',
                        help='Specify input encoding (default: utf-8)')
    parser.add_argument('-u', '--use-unicode', action='store_true',
                        help='Normalize Unicode characters to ASCII equivalents when possible')
    parser.add_argument('-t', '--typographic', action='store_true',
                        help='Replace typographic chars with ASCII equivalents (smart quotes, em-dashes, etc)')
    parser.add_argument('-s', '--strip-stickers', action='store_true',
                        help="Remove emoji, pictographs, and other Unicode sticker-type glyphs that don't belong in a terminal, text file, or serious conversation.")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Mention every file processed, whether it contains offensive characters or not.')
    parser.add_argument('--check', action='store_true',
                        help='Linter/CI mode: exit non-zero if any non-ASCII is '
                             'found, quiet on success. Writes no output.')
    parser.add_argument('--security', action='store_true',
                        help='Security audit: exit non-zero only on DANGEROUS '
                             'Unicode -- bidi controls (Trojan Source), bare '
                             'zero-width/invisible characters, and homoglyphs -- '
                             'ignoring benign UTF-8 like accents. Quiet on success.')
    parser.add_argument('--allow', metavar='SPEC', action='append', default=[],
                        help='Carve exceptions out of detection/handling. '
                             'Comma-list of a category (bidi, invisible, '
                             'homoglyph, emoji), a script subgroup '
                             '(homoglyph:greek), a code point (U+00A0), or a '
                             'range (U+2010-U+2015). Repeatable. Also read from '
                             f'a {ALLOW_FILENAME} file unless --no-config.')
    parser.add_argument('--no-config', action='store_true',
                        help=f'Ignore any {ALLOW_FILENAME} file; use only --allow.')

    # Encoded output: keep the glyph, render it 7-bit for a target format.
    # Mutually exclusive -- pick one target. All map to options.encode_mode.
    encode = parser.add_mutually_exclusive_group()
    encode.add_argument('--html-entities', dest='encode_mode',
                        action='store_const', const='html',
                        help='Encode non-ASCII as HTML entities (em dash -> &mdash;)')
    encode.add_argument('--numeric', dest='encode_mode',
                        action='store_const', const='numeric',
                        help='Encode non-ASCII as hex numeric refs (em dash -> &#x2014;)')
    encode.add_argument('--css-escapes', dest='encode_mode',
                        action='store_const', const='css',
                        help='Encode non-ASCII as CSS unicode escapes (middot -> \\0000B7 )')
    encode.add_argument('--backslash-u', dest='encode_mode',
                        action='store_const', const='backslash',
                        help='Encode non-ASCII as source-string escapes (em dash -> \\u2014)')
    parser.set_defaults(encode_mode=None)

    options = parser.parse_args()

    # Build the allow-list policy from a .polascii-allow file (nearest ancestor
    # of the cwd, unless --no-config) plus any --allow tokens on the command
    # line. CLI and file are unioned.
    allow_tokens = []
    allow_source = None
    if not options.no_config:
        allow_source = find_allow_file(os.getcwd())
        if allow_source:
            allow_tokens.extend(_iter_allow_file_tokens(allow_source))
    for spec in options.allow:
        allow_tokens.extend(t for t in spec.replace(',', ' ').split())
    try:
        options.policy = build_policy(allow_tokens)
    except ValueError as e:
        print(f"Error in allow-list: {e}", file=sys.stderr)
        return 2
    if options.policy and options.verbose and allow_source:
        print(f"Using allow-list from {allow_source}", file=sys.stderr)

    output_file = sys.stdout
    if options.output:
        try:
            output_file = open(options.output, 'w', encoding='utf-8')
        except IOError as e:
            print(f"Error opening output file: {e}", file=sys.stderr)
            return 1
    
    exit_code = 0

    for file in options.files:
        processed_content, non_ascii_chars, positions = analyze_file(file, options)

        # Reporting name.
        filename = 'stdin' if file == '-' else file

        # A decode error means the file could not be read as clean text; in a
        # lint mode that is a failure, otherwise we skip it (already warned).
        if processed_content is None:
            if options.check or options.security:
                exit_code = 1
            continue

        # Lint modes write no output, stay quiet on clean files, and set a
        # non-zero exit on violations. --check flags ANY non-ASCII; --security
        # flags only the dangerous classes (bidi controls, bare invisibles,
        # homoglyphs) and ignores benign UTF-8 like accents. If both are given,
        # --check wins (it is the superset).
        if options.check or options.security:
            all_findings = list(zip(non_ascii_chars, positions))
            # Policy-allowed clusters are not violations; count them so a quiet
            # exit is never mistaken for "there was nothing here."
            allowed_n = 0
            if options.policy:
                kept = []
                for c, p in all_findings:
                    if options.policy.allows(c):
                        allowed_n += 1
                    else:
                        kept.append((c, p))
                all_findings = kept

            findings = all_findings
            security_only = options.security and not options.check
            if security_only:
                findings = [(c, p) for c, p in findings
                            if _cluster_category(c)[0] in DANGEROUS_CATEGORIES]

            allowed_note = f" ({allowed_n} allowed by policy)" if allowed_n else ""

            if findings:
                exit_code = 1
                dangerous = [(c, p) for c, p in findings
                             if _cluster_category(c)[0] in DANGEROUS_CATEGORIES]

                if security_only:
                    print(f"{filename}: {len(findings)} dangerous "
                          f"character(s){allowed_note}", file=sys.stderr)
                    to_show = findings
                else:
                    summary = (f"{filename}: {len(findings)} non-ASCII "
                               f"character(s){allowed_note}")
                    if dangerous:
                        cats = Counter(_cluster_category(c)[0] for c, _ in dangerous)
                        breakdown = ', '.join(f"{n} {cat}"
                                              for cat, n in cats.most_common())
                        summary += f"  [WARNING: {breakdown}]"
                    print(summary, file=sys.stderr)
                    # Always surface the dangerous findings; show everything
                    # only under -v.
                    to_show = findings if options.verbose else dangerous

                for char, pos in to_show:
                    print(f"  {_format_finding(char, pos)}", file=sys.stderr)
            elif allowed_n and options.verbose:
                # Clean apart from policy-allowed characters -- say so under -v.
                print(f"{filename}: clean{allowed_note}", file=sys.stderr)
            continue

        # Write the processed content if we're replacing, folding, or encoding.
        if options.replace is not None or options.typographic or options.encode_mode:
            print(processed_content, file=output_file, end='')

        if non_ascii_chars:
            if not options.replace and not options.typographic and not options.encode_mode:
                print(f"\nFound {len(non_ascii_chars)} non-ASCII characters in {filename}", file=sys.stderr)
            
            if options.list:
                print("\nNon-ASCII characters with positions:", file=sys.stderr)
                for char, pos in zip(non_ascii_chars, positions):
                    print(f"{_codepoints(char)} '{char}' at position {pos}", file=sys.stderr)
            
            if options.count:
                counter = Counter(non_ascii_chars)
                print("\nCharacter count:", file=sys.stderr)
                for char, count in counter.most_common():
                    print(f"{_codepoints(char)} '{char}': {count} occurrences", file=sys.stderr)

        else:
            if options.verbose:
                print(f"\nNo non-ASCII characters found in {filename}", file=sys.stderr)
    
    if options.output:
        output_file.close()

    return exit_code

if __name__ == "__main__":
    sys.exit(main())

