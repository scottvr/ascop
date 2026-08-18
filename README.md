# ~~ascop~~  polascii
### POLA+ASCII

*f/k/a ascii operator, or ascii cop, or "ask op", or maybe astonishment police ... 


## Why not just use iconv / unidecode / a sed one-liner?

 Because those either destroy the character or make you maintain the fragile part yourself. iconv -t ASCII//TRANSLIT and unidecode *transliterate*: that is, they "produce some ASCII from this glyph," which is lossy, locale- and implementation-dependent (glibc, BSD, and macOS iconv don't agreee), and  perhaps the biggest difference is the cconceptual one - those established applications are not trying to restore what you originally typed.
 
 Hand-rolled sed/perl one-liners with substitutions like `s/\xe2\x80\x94/--/g` are fragile and a bit of a PITA. If the input encoding iis different from that last machine you rolled the one-linger on,  or a variant glyph slips through (with eight different "space" characters and many "dash"-type-things, it's not hard.) And since these one-liners are simple and single-purpose, they won't always DWYM.

Plus, **none of the other tools function as a linter** (silent, return code value logic) nor can they be run with the intent of looking for **security-exposure via glyphs** (such as [CVE-2021-42574](https://nvd.nist.gov/vuln/detail/cve-2021-42574) and eliminating them from your codebase.

~~~~`polascii` fills the gap those tools leave; it does three intent-preserving things, according to your intent.

- Fold the specific smart substitution back to the keystroke you actually made — —→--, "/"→", …→... — reversing the autocorrect instead of romanizing the text.
- Encode, don't destroy. Keep the glyph's identity but render it 7-bit for a specific target: --html-entities (&mdash;), --css-escapes (\0000B7 ), --numeric (&#x2014;), --backslash-u (\u2014). No other common tool offers "keep the character, express it safely for HTML/CSS/source."
- Gate it. `--check` exits non-zero the moment unwanted Unicode (smart punctuation, zero-width characters, an emoji smuggled in from a copy-paste) shows up in a file. Drop  in a pre-commit hook or CI and stop shipping stuff you never typed.
- Catch the *dangerous* stuff. `--security` is the linter that stays out of your way on legitimate UTF-8 (accented names, quoted foreign text) but fails the build on the Unicode that can actually bite you: bidirectional control characters (the "Trojan Source" attack, CVE-2021-42574), bare zero-width/invisible characters, and homoglyphs (the Cyrillic `а`-for-`a` trick). `iconv` will never be a security linter; this is the gap  actually fills.

`` is a Principle-of-Least-Astonishment Enforcer/Restorer and a lint gate, not a transliterator. If you want CJK romanization or full charset conversion, you want recode or unidecode — and that's fine.



### The Principle of Least Astonishment (POLA)
When I input text via a keyboard that has printed on it 32-64 ostensibly 7-bit ASCII characters (or twice that if the shifted variant is also displayed, or more of course but we're pushing up against our bitness limit now aren't we?) - or on a software version of one displayed on my iPhone *that even has enhanced long-press optional variants of these characters, should they be what I actually want* and expectr; I expect the exact characters I typed to be preserved in the document (or whatever sort of container) to which I enter them. 

The automatic substitution of a minus with an emdash, a single quotei with a curly apostrophe (’), or a simple double quote (") with a typographically "correct" quotation mark (“ or ”) is a violation of [POLA](https://en.wikipedia.org/wiki/Principle_of_least_astonishment) because I never explicitly asked for those substitutions. Of course what proves to be astonishing to different types of users can be as different as the users and use cases themselves, and a company creating software for profit will aim to serve whichever class of users is the majority. 

The same nuance can be found when discussing [DWIM](https://en.m.wikipedia.org/wiki/DWIM) and more subtle and potentially more dangerous, [WYSIWYG](https://en.m.wikipedia.org/wiki/WYSIWYG) which, tangentially is also addressed in `` from another angle with its `-u` option. `ascop` is for the minority then, I guess; for those for whom majority software does not Do What they Mean. For those of you who are frustrated by not Getting What You think You See, and who are Astonished (though decreasingly so with time and proliferation of smarts) at Least.

### The Problem With Smart Punctuation
Certainly for some people, having their software (such as a word processor) act as an editor and typesetter is seen as a beneficial feature, as it saves them time they would otherwise have to spend on re-formatting after initially typing something. However, this insidious creeping presence in note-taking apps, text messages, and what would sensibly be assumed to be an actual  *plain-text* export means that what I type is often not what I get when I copy-paste or send the text elsewhere. I am often having to spend time editing text to "unsmarten" (or endumben?) it, usually only after some other process chokes on the text. Some examples:

- Sending code snippets where an emdash breaks syntax. 
- similarky, your programming language probably expects single and double ticks, not &ldquo; (`&ldquo;`) and &rdquo; (`&rdquo;`) surrounding strings.
- Writing a list of commands, intending to paste them into a terminal to be parsed by a shell, where ticks and backticks have special meanings, and a fancy apostrophe causes errors.
- Writing a plaintext file that expect to be portable across systems.
- Using SMS or simple messaging apps, or even HTML form fields where unexpected characters may break formatting.
   - (and if you're like me and often need to compose your long body of text outside of an app prone to crashing, refreshing, or otherwise finding ways to lose a whole bunch of typing you've done with no way to recover it, finding that when you paste the long-form text into the shaky input area, you break it anyway with some uninvited text your editor has "helpfully" swapped in for you.)
- Oh, how could I have forgotten to mention in the preface perhaps my favorite of them all. If I type three dots, full stops, periods, or decimal points - ASCII 0x2E - I want `...`, not &mldr; (`&mldr;`)

### Existing Tools Too Much or Not Enough
I looked at:

- **iconv:** Great for converting between encodings but would require pre-processing to strip specific non-ASCII replacements. Also, seems lots of variance among implementations.
- **tr:** Too primitive for handling multi-byte Unicode substitutions (e.g., changing ’ back to '). And let's face it, if we were going to use tr for the job, we'd place all the tr commands in a reusable shell script anyway, so we're already heading toward tool-forging territory.
- **recode:** Overkill? The fact that its man page told me that there exists a manual I can read with `/usr/bin/info` was already too much.
  
Rather than contorting these tools into doing exactly what I need, `` solves the problem directly.

### : A Simple, Purpose-Built Solution
`` does _one thing_* well:
-  Finds non-ASCII characters in a file.
-  Lists their positions and counts.
-  Replaces them with either ASCII equivalents or a placeholder of choice.
-  Preserves encoding while ensuring ASCII integrity.
  
\*_one thing_ that splits naturally into four bullets of course

### Having said that...

Maybe you're like the smart reddit user who informed me that Smart Punctuation can be disabled on the iPhone in keyboard settings and you don't have this problem. Heck, I won't have this problem in the future from my iPhone now (I hope) but that doesn't fix all the files I have that started out on my phone that have these little annoyances lurking in them. So `` is still useful to repair existing files, or files you may not have created, as demonstrated in the example usage below,.

### and that said...

I could totally see eventually scratching an itch to add more codepages, charsets, mapping features, etc.  In which case,  would become overkill too. I should avoid adding features and just learn to use `recode` if this becomes a thing.


### and THAT said...

I think PR's containing additions to the TYPOGRAPHIC_MAP with fixes for your least favorite, most peeve-y "smart" replacements are swell. 
Let me know of (or submit a PR fixing) anything I have missed.

### In the meantime... 
** will**
- give you control over your own text.
- provide some options, and not impose defaults that require post-processing.
- respect your intent rather than assuming "I know better than you."

____
**__ exists because plaintext should be just that - plain.__**

# Oh yeah! Usage:

```bash
usage: .py [-h] [-r CHAR] [-l] [-c] [-o FILE] [-e ENCODING] [-u] [-t]
                [-s] [-v] [--check] [--security] [--html-entities |
                --numeric | --css-escapes | --backslash-u]
                [FILE ...]

Detect and handle non-ASCII characters

positional arguments:
  FILE                  Files to process (default: stdin)

options:
  -h, --help            show this help message and exit
  -r, --replace CHAR    Replace non-ASCII chars with CHAR
  -l, --list            List all non-ASCII characters found with positions
  -c, --count           Count occurrences of each non-ASCII character
  -o, --output FILE     Write output to FILE instead of stdout
  -e, --encoding ENCODING
                        Specify input encoding (default: utf-8)
  -u, --use-unicode     Normalize Unicode characters to ASCII equivalents when
                        possible
  -t, --typographic     Replace typographic chars with ASCII equivalents
                        (smart quotes, em-dashes, etc)
  -s, --strip-stickers  Remove emoji, pictographs, and other Unicode sticker-
                        type glyphs that don't belong in a terminal, text
                        file, or serious conversation.
  -v, --verbose         Mention every file processed, whether it contains
                        offensive characters or not.
  --check               Linter/CI mode: exit non-zero if any non-ASCII is
                        found, quiet on success. Writes no output.
  --security            Security audit: exit non-zero only on DANGEROUS
                        Unicode -- bidi controls (Trojan Source), bare zero-
                        width/invisible characters, and homoglyphs -- ignoring
                        benign UTF-8 like accents. Quiet on success.
  --allow SPEC          Carve exceptions out of detection/handling. Comma-list of a category (bidi, invisible,
                        homoglyph, emoji), a script subgroup (homoglyph:greek), a code point (U+00A0), or a range
                        (U+2010-U+2015). Repeatable. Also read from a .polascii-allow file unless --no-config.
  --no-config           Ignore any .polascii-allow file; use only --allow.
  --html-entities       Encode non-ASCII as HTML entities (em dash -> &mdash;)
  --numeric             Encode non-ASCII as hex numeric refs (em dash ->
                        &#x2014;)
  --css-escapes         Encode non-ASCII as CSS unicode escapes (middot ->
                        \0000B7 )
  --backslash-u         Encode non-ASCII as source-string escapes (em dash ->
                        \u2014)
```

### Linting / CI gate

`--check` turns  into a pre-commit or CI gate: it exits non-zero the moment
any non-ASCII slips into a tracked file, and stays silent when everything is
clean. Add `-v` to see exactly which code points offend and where.

```bash
.py --check src/*.py            # exit 1 if any file has non-ASCII, else 0
.py --check -v README.md        # ... and list the offenders on failure
```

`--check` also *names* what it finds and flags the dangerous classes even
without `-v`, so a smuggled bidi override does not hide in a pile of curly
quotes:

```
$ .py --check payload.py
payload.py: 3 non-ASCII character(s)  [WARNING: 1 bidi-control, 1 invisible]
  U+202E [bidi-control] RIGHT-TO-LEFT OVERRIDE at position 41
  U+200B [invisible] ZERO WIDTH SPACE at position 58
```

### Security audit: bidi / invisible / homoglyph

`--check` fails on *any* non-ASCII, which is too blunt for a repo that
legitimately contains UTF-8 (accented author names, quoted foreign text). That
is what `--security` is for: it ignores benign Unicode and fails only on the
characters that can actually deceive a human or a parser:

- **Bidirectional controls** -- the "Trojan Source" attack ([CVE-2021-42574](https://nvd.nist.gov/vuln/detail/CVE-2021-42574)),
  where source *displays* differently from how it *compiles*.
- **Bare zero-width / invisible characters** -- a common vector for hiding text,
  watermarking, or smuggling data. (A ZWJ inside a legitimate emoji sequence is
  recognized as part of the emoji and left alone -- no false alarm.)
- **Homoglyphs** -- non-ASCII letters that impersonate ASCII ones, e.g. a
  Cyrillic `а` (U+0430) standing in for a Latin `a`.

```bash
.py --security src/**/*.py      # exit 1 only on the dangerous classes
```

For safety,  never echoes a raw bidi override or invisible character back
into your terminal in its report -- it prints the code point and Unicode name
instead. The `BIDI_CONTROLS`, `INVISIBLE_CHARS`, and `CONFUSABLES` tables at the
top of `.py` are the extension point, just like `TYPOGRAPHIC_MAP`.

### Encoded output (keep the glyph, encode it 7-bit)

Unlike `iconv //TRANSLIT`, `unidecode`, or `recode` -- which transliterate and
*destroy* the glyph -- these modes preserve the character's identity while
rendering it as 7-bit text for a specific target format. Pick one:

```bash
.py --html-entities page.html   # em dash -> &mdash;   (named, else numeric)
.py --numeric      page.html    # em dash -> &#x2014;  (hex numeric ref)
.py --css-escapes  styles.css   # middle dot -> \0000B7  (trailing space terminates)
.py --backslash-u  strings.py   # em dash -> \u2014   (source-string escape)
```

### Examples:

Find the files with unwanted characters
```bash
.py -c w*.html

Found 6 non-ASCII characters in wrongslash-ooo-generated.html

Character count:
U+2013 '–': 2 occurrences
U+00A0 ' ': 2 occurrences
U+2019 '’': 2 occurrences

No non-ASCII characters found in wrongslash.html
```

Tell me exactly where they are in a file with unwanted characters
```bash
.py -l wrongslash-ooo-generated.html

Found 6 non-ASCII characters in wrongslash-ooo-generated.html

Non-ASCII characters with positions:
U+2013 '–' at position 6572
U+2013 '–' at position 8589
U+00A0 ' ' at position 8789
U+2019 '’' at position 8821
U+00A0 ' ' at position 8884
U+2019 '’' at position 8939
```

Write out a new file, with the unwanted characters replaced with the ASCII I intended
```bash
[scottvr@grid html]$ ~/source//ascop.py -t -o wrongslash-cleaned.html  wrongslash-ooo-generated.html
[scottvr@grid html]$ ~/source//ascop.py -l wrongslash-cleaned.html

No non-ASCII characters found in wrongslash-cleaned.html
[scottvr@grid html]$ wc -l wrongslash-cleaned.html wrongslash-ooo-generated.html
   40 wrongslash-cleaned.html
   40 wrongslash-ooo-generated.html
   80 total
```

and in the spirit of you knowing more about what you want your text to be than some software, you can supply your own replacements with 
`-r`, and as a result of creeping featurism, you can [normalize possibly edge case code points to Unicode equivalents](https://en.wikipedia.org/wiki/Unicode_equivalence) which can, optionally then be processed by specifying `-r` or `-t` replacement mapping.
