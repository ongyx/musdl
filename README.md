# musdl

![logo](https://raw.githubusercontent.com/ongyx/musdl/master/logo.jpg "musdl")

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/musdl)](https://pypi.org/project/musdl)
![PyPI - License](https://img.shields.io/pypi/l/musdl)
![PyPI](https://img.shields.io/pypi/v/musdl)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/musdl)
![Lines of code](https://img.shields.io/tokei/lines/github/ongyx/musdl)

## ;-;
This repo is no longer in development because musescore-downloader now has a CLI. See [here](https://github.com/ongyx/musdl/issues/4) for more info. 

## NOTE

**The author of musdl does NOT condone piracy in any way, and is not responsible for anything that happens as a result of piracy arising from the use of musdl.**

musdl (**mus**score **d**own**l**oader) is a downloader for Musescore, written in Python (with a little help from [js2py](https://pypi.org/project/Js2Py/)).
musdl can download scores as MP3, MIDI, MXL and PDF.
PDFs are rendered from individual SVGs to A4 size using [svglib](https://pypi,org/project/svglib), guaranteeing the highest resolution available.

For [example](https://github.com/ongyx/musdl/blob/master/Gymnop%C3%A9die_No_1.pdf), Gymnopédie No. 1.

It is meant to be used as a command-line tool, but can also be imported and used as a module:

```python
from musdl import Score

my_score = Score(...)  # the Musescore url goes here
data = my_score.download("mp3")  # download as mp3, returns as bytes
```

## How it works

I browserified [musescore-downloader](https://github.com/Xmader/musescore-downloader), which is written in TypeScript. This bundles the relavent parts into a single file that can be run by js2py.

Other approaches were considered:

- Create a native Python interpreter just to decode the musescore js. (Will problably break with every API change.)
- Use a headless browser with requests-html or Selenium. (Resource-heavy, not really cross-platform.)

So I decided to roll with js2py because its pure-Python.
The pipeline for creating the JS file looks like this:

```text
_musdl.js
    -> tsify (TS to JS)
    -> babelify (ES6 to ES5, beacause js2py translates ES6 to ES5 anyway)
    -> browserify (bundle the whole thing)
    -> musdl.js
```

## takedown request, et tu

Take a look at this [issue](https://github.com/Xmader/musescore-downloader/issues/5) in the same repo.

## Requirements

- `requests` - Downloader.
- `beautifulsoup4` - Powerful HTML parser.

For downloading PDFs:

- `reportlab` - Make PDFs.
- `svglib` - Convert SVGs into Reportlab drawings.

## Hacking

NOTE: Because you need to compile the JS file first, run `node scripts/build.js` to do so.
Obviously, you need npm and nodejs.

All my python projects now use [flit](https://pypi.org/project/flit) to build and publish.
So you need to `python3 -m pip install flit` first.

```text
npm install
node scripts/build.js
flit build
```

## Install

`(python3 -m) pip install musdl`

If you want to download PDFs, you need to install the `pdf` extra:

`(python3 -m) pip install musdl[pdf]`

## License

MIT.

## Changelog

### 2.3.0

Better PDF page detection (now the exact number of pages are known at runtime).
The attributes `.user`, `.id`, and `.pages` have been added to the `Score` class. (user and pages are self-explanatory, id is the score id.)
Added support for multi-threaded downloading of PDF pages (specify with `-t`). Downloading (may) be faster.

### 2.2.2

Fixed PDF scaling issue on Windows.

### 2.2.1

Made PDF downloading a extra feature (because `svglib` and `reportlab` dependencies are not pure-Python).

### 2.2.0

Fixed PDF support for Windows. Now musdl uses `svglib` as the backend for adding SVGs to PDFs.

### 2.1.1-2.1.2

Added PDF support.

### 2.0.0

Added `-O` option to use the score's title as the output filename (y'know, like `curl -O`).
Refactored code to be object-oriented, in the form of the `Score` class. This should make adding new features easier.
(Plus, you can use `musdl` more programmatically!)

### 1.1.2

Version bump, use Flit to build instead of `setup.py`.
Updated README too.

### 1.1.0

Added MusicXML download option, thanks to [JPFrancoia](https://github.com/JPFrancoia) for the update!

### 1.0.0

Initial version.
