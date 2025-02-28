# ascop
*ascii operator, or ascii cop, or "ask op", or... A Case (and Remedy) Against Unsolicited Smart Punctuation*

### The Principle of Least Astonishment (POLA)
When I input text via a keyboard that has printed on it 32-64 ostensibly 7-bit ASCII characters (or twice that if the shifted variant is also displayed, or more of course but we're pushing up against our bitness limit now aren't we?) - or on a software version of one displayed on my iPhone *that even has enhanced long-press optional variants of these characters, should they be what I actually want*, I expect the exact characters I typed to be preserved in the document (or whatever sort of container) to which I enter them. 

The automatic substitution of a minus (-) with an emdash (—), a single quote (') with a curly apostrophe (’), or a simple double quote (") with a typographically "correct" quotation mark (“ or ”) is a violation of [POLA](https://en.wikipedia.org/wiki/Principle_of_least_astonishment) because I never explicitly asked for those substitutions. Of course what proves to be astonishing to different types of users can be as different as the users and use cases themselves, and a company creating software for profit will aim to serve whichever class of users is the majority. The same nuance can be found when discussing [DWIM](https://en.m.wikipedia.org/wiki/DWIM) and more subtle and potentially more dangerous, [WYSIWYG](https://en.m.wikipedia.org/wiki/WYSIWYG) which, tangentially is also addressed in ascop from another angle with its `-u` option.

### The Problem With Smart Punctuation
Certainly for some people, having their software (such as a word processor) act as an editor and typesetter is seen as a beneficial feature, as it saves them time they would otherwise have to spend after initially writing on re-formatting. However, this insidious creeping presence in note-taking apps, text messages, and what would sensibly be assumed to be an actual  *plain-text* export means that what I type is often not what I get when I copy-paste or send the text elsewhere. I am often having to spend time editing text to "unsmarten" (or endumben?) it, usually only after  some other process chokes on the text. Some examples:

- Sending code snippets where an emdash breaks syntax. (your programming language probably expects single and double ticks, not &ldquo; (`&ldquo;`) and &rdquo; (`&rdquo;`) surrounding strings.)
- Writing a list of commands, intending to paste them into a terminal to be parsed by a shell, where ticks and backticks have special meanings, and a fancy apostrophe causes errors.
- Writing a plaintext file that you should be able to expect to be portable across systems.
- Using SMS or simple messaging apps, or even HTML form fields where unexpected characters may break formatting.
   - (and if you're like me and often need to compose your long body of text outside of an app prone to crashing, refreshing, or otherwise finding ways to lose a whole bunch of typing you've done with no way to recover it, finding that when you paste the long-form text into the shaky input are, you break it anyway with some uninvited text your editor has "helpfully" swapped in for you.)
- Oh, how could I have forgotten to mention in the preface perhaps my favorite of them all. If I type three dots, full stops, periods, or decimal points - ASCII 0x2E - I want `...`, not &mldr; (`&mldr;`)
### Existing Tools Too Much or Not Enough

I looked at:

- **iconv:** Great for converting between encodings but would require pre-processing to strip specific non-ASCII replacements. Also, seems lots of variance among implementations.
- **tr:** Too primitive for handling multi-byte Unicode substitutions (e.g., changing ’ back to '). And let's face it, if we were going to use tr for the job, we'd place all the tr commands in a reusable shell script anyway, so we're already heading toward tool-forging territory.
- **recode:** Overkill? The fact that its man page told me that there exists a manual I can read with `/usr/bin/info` was already too much.
  
Rather than contorting these tools into doing exactly what I need, `ascop` solves the problem directly.

### ASCop: A Simple, Purpose-Built Solution
`ascop` does _one thing_* well:
-  Finds non-ASCII characters in a file.
-  Lists their positions and counts.
-  Replaces them with either ASCII equivalents or a placeholder of choice.
-  Preserves encoding while ensuring ASCII integrity.
  
\*_one thing_ that splits naturally into four bullets of course
### That said...

I could totally see eventually scratching an itch to add more codepages, charsets, mapping features, etc. 
In which case, ascop would become overkill too. I should avoid adding features and just learn to use `recode`
if this becomes a thing.

### and THAT said...

I think PR's containing additions to the TYPOGRAPHIC_MAP with fixes for your least favorite, most peeve-y "smart" replacements are swell. 
Let me know of (or submit a PR fixing) anything I have missed.

### In the meantime... 
**ascop will**
- give you control over your own text.
- provide some options, and not impose defaults that require post-processing.
- respect your intent rather than assuming "I know better than you."

____
**__Ascop exists because plaintext should be just that - plain.__**

# Oh yeah! Usage:

```bash
usage: ascop.py [-h] [-r CHAR] [-l] [-c] [-o FILE] [-e ENCODING] [-u] [-t]
                [FILE ...]

Detect and handle non-ASCII characters

positional arguments:
  FILE                  Files to process (default: stdin)

optional arguments:
  -h, --help            show this help message and exit
  -r CHAR, --replace CHAR
                        Replace non-ASCII chars with CHAR
  -l, --list            List all non-ASCII characters found with positions
  -c, --count           Count occurrences of each non-ASCII character
  -o FILE, --output FILE
                        Write output to FILE instead of stdout
  -e ENCODING, --encoding ENCODING
                        Specify input encoding (default: utf-8)
  -u, --use-unicode     Replace with similar-looking Unicode characters when
                        possible (NFKD), to either convert to ASCI directly,
                        or to a unicode char more likely to be in our typographic map.
  -t, --typographic     Replace typographic chars with ASCII equivalents
                        (smart quotes, em-dashes, etc)
```

### Examples:

Find the files with unwanted characters
```bash
ascop.py -c w*.html

Found 6 non-ASCII characters in wrongslash-ooo-generated.html

Character count:
U+2013 '–': 2 occurrences
U+00A0 ' ': 2 occurrences
U+2019 '’': 2 occurrences

No non-ASCII characters found in wrongslash.html
```

Tell me exactly where they are in a file with unwanted characters
```bash
ascop.py -l wrongslash-ooo-generated.html

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
[scottvr@grid html]$ ~/source/ascop/ascop.py -t -o wrongslash-cleaned.html  wrongslash-ooo-generated.html
[scottvr@grid html]$ ~/source/ascop/ascop.py -l wrongslash-cleaned.html

No non-ASCII characters found in wrongslash-cleaned.html
[scottvr@grid html]$ wc -l wrongslash-cleaned.html wrongslash-ooo-generated.html
   40 wrongslash-cleaned.html
   40 wrongslash-ooo-generated.html
   80 total
```

and in the spirit of you knowing more about what you want your text to be than some software, you can supply your own replacements with 
`-r`, and as a result of creeping featurism, you can [normalize possibly edge case code points to Unicode equivalents](https://en.wikipedia.org/wiki/Unicode_equivalence) which can, optionally then be processed by speciying `-r` or `-t` replacement mapping.
