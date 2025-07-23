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

Examples:
  ascop.py file.txt                      # Report non-ASCII characters
  ascop.py -r '?' file.txt               # Replace with question marks
  ascop.py -l -c file.txt                # List and count occurrences
  cat file.txt | ascop.py -r '_' -o clean.txt  # Read from stdin, write to file
"""

import sys
import argparse
import unicodedata
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
    '\ufb01': 'fi',   # Latin small ligature fi
    '\ufb02': 'fl',   # Latin small ligature fl
    
    # Common accented characters
    '\u00e0': 'a',    # à
    '\u00e1': 'a',    # á
    '\u00e2': 'a',    # â
    '\u00e3': 'a',    # ã
    '\u00e4': 'a',    # ä
    '\u00e5': 'a',    # å
    '\u00e8': 'e',    # è
    '\u00e9': 'e',    # é
    '\u00ea': 'e',    # ê
    '\u00eb': 'e',    # ë
    '\u00ec': 'i',    # ì
    '\u00ed': 'i',    # í
    '\u00ee': 'i',    # î
    '\u00ef': 'i',    # ï
    '\u00f2': 'o',    # ò
    '\u00f3': 'o',    # ó
    '\u00f4': 'o',    # ô
    '\u00f5': 'o',    # õ
    '\u00f6': 'o',    # ö
    '\u00f9': 'u',    # ù
    '\u00fa': 'u',    # ú
    '\u00fb': 'u',    # û
    '\u00fc': 'u',    # ü
    '\u00f1': 'n',    # ñ
    '\u00ff': 'y',    # ÿ
    '\u00fd': 'y',    # ý
    '\u00e7': 'c',    # ç
    
    # Currency
    '\u20ac': 'EUR',  # Euro sign
    '\u00a3': 'GBP',  # Pound sign
    '\u00a5': 'JPY',  # Yen sign
}

def _remove_unicode_emoji(text):
    return regex.sub(r'\p{Emoji}', '', text)

def _is_emoji_cluster(cluster):
    return all(regex.match(r'\p{Emoji}', c) for c in cluster)

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
    emoji_chars = []
    processed_content = []

    grapheme_boundaries = []
    index = 0
    for g in grapheme.graphemes(content):
        grapheme_boundaries.append((index, index + len(g)))
        index += len(g)


        for start, end in grapheme_boundaries:
            cluster = content[start:end]

        if all(ord(c) < 128 for c in cluster):
            processed_content.append(cluster)
            continue

        # This cluster contains non-ASCII
        non_ascii_chars.append(cluster)
        positions.append(start)

        # Normalize if requested
        if options.use_unicode:
            normalized = unicodedata.normalize('NFKD', cluster)
            ascii_normalized = ''.join([c for c in normalized if ord(c) < 128])
            if ascii_normalized:
                processed_content.append(ascii_normalized)
                continue
            if normalized != cluster:
                cluster = normalized

        # Strip stickers if requested
        if options.strip_stickers and _is_emoji_cluster(cluster):
            non_ascii_chars.append(cluster)
            positions.append(start)
            continue

        # Typographic mapping
        if options.typographic:
            replaced = False
            for c in cluster:
                if c in TYPOGRAPHIC_MAP:
                    processed_content.append(TYPOGRAPHIC_MAP[c])
                    replaced = True
                    break
            if replaced:
                continue

        # Fallback replacement
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
                        help="Remove emoji, pictographs, and other Unicode sticker-type glyphs that don't belong in a terminal, text file, or serious conversation. No ÎõÎõ")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Mention every file processed, whether it contains offensive characters or not.')

    options = parser.parse_args()
    
    output_file = sys.stdout
    if options.output:
        try:
            output_file = open(options.output, 'w', encoding='utf-8')
        except IOError as e:
            print(f"Error opening output file: {e}", file=sys.stderr)
            return 1
    
    for file in options.files:
        processed_content, non_ascii_chars, positions = analyze_file(file, options)
        
        if processed_content is None:
            continue
            
        # Write the processed content if we're replacing or using typographic mapping
        if options.replace is not None or options.typographic:
            print(processed_content, file=output_file, end='')
        
        # Reporting
        if file == '-':
            filename = 'stdin'
        else:
            filename = file
            
        if non_ascii_chars:
            if not options.replace and not options.typographic:
                print(f"\nFound {len(non_ascii_chars)} non-ASCII characters in {filename}", file=sys.stderr)
            
            if options.list:
                print("\nNon-ASCII characters with positions:", file=sys.stderr)
                for char, pos in zip(non_ascii_chars, positions):
                    print(f"U+{ord(char):04X} '{char}' at position {pos}", file=sys.stderr)
            
            if options.count:
                counter = Counter(non_ascii_chars)
                print("\nCharacter count:", file=sys.stderr)
                for char, count in counter.most_common():
                    print(f"U+{ord(char):04X} '{char}': {count} occurrences", file=sys.stderr)

        else:
            if options.verbose:
                print(f"\nNo non-ASCII characters found in {filename}", file=sys.stderr)
    
    if options.output:
        output_file.close()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

