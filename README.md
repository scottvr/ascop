# ascop
*ascii operator, or ascii cop, or "ask op", or... A Case (and Remedy) Against Unsolicited Smart Punctuation*

### The Principle of Least Astonishment (POLA)
When I input text via a keyboard that has printed on it 64 ostensibly 7-bit ASCII characters - or on a software version of one displayed on my iPhone *that even has enhanced long-press optional variants of these characters, should they be what I actually want*, I expect the exact characters I typed to be preserved in the document (or whatever sort of container) to which I enter them. The automatic substitution of a minus (-) with an emdash (—), a single quote (') with a curly apostrophe (’), or a simple double quote (") with a typographically “correct” quotation mark (“ or ”) is a violation of [POLA](https://en.wikipedia.org/wiki/Principle_of_least_astonishment) because I never explicitly asked for those substitutions.

### The Problem With Smart Punctuation
Certainly for some people, having their software (such as a word processor) act as an editor and typesetter is seen as a beneficial feature, as it saves them time they would otherwise have to spend after initially writing or re-formatting. However, this insidious creeping presence in note-taking apps, text messages, and what would sensibly be assumed to be an actual  *plain-text* export means that what I type is often not what I get when I copy-paste or send the text elsewhere. I am often having to spend time editing text to "unsmarten" (or endumben?) it, usually only when some other process chokes on the text. Some examples:

- Sending code snippets where an emdash breaks syntax. (your programming language probably expects single and double ticks, not &ldquo; (`&ldquo;`) and &rdquo; (`&rdquo;`) surrounding strings.)
- Writing a list of command, intending to paste them into a terminal to be parsed by a shell, where ticks and backticks have special meanings, and a fancy apostrophe causes errors.
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
