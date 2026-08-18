#!/usr/bin/python3

# ascop - the ascii police.. the ascii operator.. the ask op? ass cop?

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
  ascop.py [options] [FILE...]
  
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
  --html-entities       Encode non-ASCII as HTML entities (em dash -> &mdash;)
  --numeric             Encode non-ASCII as hex numeric refs (em dash -> &#x2014;)
  --css-escapes         Encode non-ASCII as CSS unicode escapes (middot -> \\0000B7 )
  --backslash-u         Encode non-ASCII as source-string escapes (em dash -> \\u2014)

Examples:
  ascop.py file.txt                      # Report non-ASCII characters
  ascop.py -r '?' file.txt               # Replace with question marks
  ascop.py -l -c file.txt                # List and count occurrences
  ascop.py --check src/*.py              # Fail (exit 1) if any file has non-ASCII
  ascop.py --html-entities page.html     # Keep the glyph, encode it for HTML
  cat file.txt | ascop.py -r '_' -o clean.txt  # Read from stdin, write to file
"""

import sys
import argparse
import unicodedata
import html.entities
import regex
import grapheme
from collections import Counter

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

def _remove_unicode_emoji(text):
    return regex.sub(r'\p{Emoji}', '', text)

def _is_emoji_cluster(cluster):
    return all(regex.match(r'\p{Emoji}', c) for c in cluster)

def _codepoints(cluster):
    """Format a grapheme cluster as its U+ code points (handles multi-codepoint
    clusters like ZWJ emoji, which ord() cannot)."""
    return ' '.join(f"U+{ord(c):04X}" for c in cluster)

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

        # A decode error means the file could not be read as clean text; in
        # check mode that is a failure, otherwise we skip it (already warned).
        if processed_content is None:
            if options.check:
                exit_code = 1
            continue

        # Linter/CI mode: report violations to stderr, write nothing, and flag
        # the run for a non-zero exit. Stay silent when the file is clean.
        if options.check:
            if non_ascii_chars:
                exit_code = 1
                print(f"{filename}: {len(non_ascii_chars)} non-ASCII character(s)",
                      file=sys.stderr)
                if options.verbose:
                    for char, pos in zip(non_ascii_chars, positions):
                        print(f"  {_codepoints(char)} '{char}' at position {pos}",
                              file=sys.stderr)
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

