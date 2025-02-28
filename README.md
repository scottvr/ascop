# ascop
*ascii operator, or ascii cop, or "ask op", or... A Case (and Remedy) Against Unsolicited Smart Punctuation*

### The Principle of Least Astonishment (POLA)
When I input text via a keyboard that has printed on it 64 ostensibly 7-bit ASCII characters - or on a software version of one displayed on my iPhone *that even has enhanced long-press optional variants of these characters, should they be what I actually want*, I expect the exact characters I typed to be preserved in the document (or whatever sort of container) to which I enter them. The automatic substitution of a minus (-) with an emdash (—), a single quote (') with a curly apostrophe (’), or a simple double quote (") with a typographically “correct” quotation mark (“ or ”) is a violation of [POLA](https://en.wikipedia.org/wiki/Principle_of_least_astonishment) because I never explicitly asked for those substitutions.

### The Problem With Smart Punctuation
I recognize that smart punctuation is useful for some people, especially in word processors. However, its creeping presence in note-taking apps, text messages, and even plain-text exports means that what I type is often not what I get when I copy-paste or send the text elsewhere. I find I often have to "unsmarten" (or endumben?) when:

- Sending code snippets where an emdash breaks syntax.
- Writing commands where a fancy apostrophe causes errors.
- Composing plaintext files that should be portable across systems.
- Using SMS or simple messaging apps, where unexpected characters may break formatting.
  
### Existing Tools Too Much or Not Enough

I explored:

iconv: Great for encoding conversion but requires pre-processing to strip specific non-ASCII replacements.
tr: Too primitive for handling multi-byte Unicode substitutions (e.g., changing ’ back to ').
recode: Overkill? The fact that its man page told me that there exists a manual I can read with `/usr/bin/info` was already too much.
Rather than contorting these tools into doing exactly what I need, `ascop` solves the problem directly.

### ASCop: A Simple, Purpose-Built Solution
`ascop` does one thing well:
-  Finds non-ASCII characters in a file.
-  Lists their positions and counts.
-  Replaces them with either ASCII equivalents or a placeholder of choice.
-  Preserves encoding while ensuring ASCII integrity.

### That said...

I could totally see eventually scratching an itch to add more codepages, charsets, mapping features, etc. 
In which case, ascop would become overkill too. I should avoid adding features and just learn to use `recode`
if this becomes a thing.

### and THAT said...

I think PR's containing additions to the TYPOGRAPHIC_MAP with fixes for your least favorite, most peeve-y "smart" repalcements are swell. 
Let me know of (or submit a PR fixing) anything I have missed.

### In the meantime... 
**ascop can**
- give you control over your own text.
- provide some options, and not impose defaults that require post-processing.
- respect your intent rather than assuming "I know better than you."

____
**__Ascop exists because plaintext should be just that - plain.__**
