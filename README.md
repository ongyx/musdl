# musdl

![logo](https://raw.githubusercontent.com/ongyx/musdl/master/logo.jpg "musdl")

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/musdl)](https://pypi.org/project/musdl)
![PyPI - License](https://img.shields.io/pypi/l/musdl)
![PyPI](https://img.shields.io/pypi/v/musdl)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/musdl)
![Lines of code](https://img.shields.io/tokei/lines/github/ongyx/musdl)

## NOTE

**The author of musdl does NOT condone piracy in any way, and is not responsible for anything that happens as a result of piracy arising from the use of musdl.**

musdl (**mus**score **d**own**l**oader) is a downloader for Musescore, written in Python.
musdl can now only download scores as `.mscz` (use the [Musescore](https://musescore.org/) software to export to other formats).

The easiest way to download the score is through the CLI:

```text
musdl (musescore url)
```

To convert to another format, use `-f/--format`:

```text
# export as midi
musdl -f mid (musescore url)
```

For a complete list of formats, run `musdl --help`.
If you want to export in any format besides `mscz`, you need to [install](#install) musescore first.

It can also be imported and used as a module:

```python
from musdl import Score, OnlineScore

my_score = OnlineScore("musescore_url")

# Read the score's metadata,
name = my_score["workTitle"]
# or save the whole score...
my_score.export("mscz", "my_score.mscz")

# ...and then load it again.
my_score = Score.from_file("my_score.mscz")
```

## How it works

I just copied over the IPNS-specific constants and used them to download the score file from [Xmader](https://github.com/Xmader)'s [dataset](https://github.com/Xmader/musescore-dataset).

Other approaches were considered:

- Create a native Python interpreter just to decode the musescore js (like Js2py). (Will problably break with every API change.)
- Use a headless JS browser with Selenium. (Resource-heavy, not really cross-platform.)
- Run a JS engine like PyMiniRacer/PyQt5. (Better speed, but needs C extensions.)

So I decided to roll with the IPNS dataset.

## takedown request, et tu

Take a look at this [issue](https://github.com/Xmader/musescore-downloader/issues/5) in the same repo.

## Requirements

- `requests` - Downloader.
- `beautifulsoup4` - Powerful HTML parser.

## Hacking

All my python projects now use [flit](https://pypi.org/project/flit) to build and publish.
So you need to `python3 -m pip install flit` first.

```text
flit build
```

## Install

`(python3 -m) pip install musdl`

Optionally, to export the score in other formats (midi, mp3, etc.) install musescore.
musdl relies on its command-line tool `mscore` to export scores:

```text
# Linux
sudo (package manager/snap) install musescore
# Windows
scoop bucket add extras  # add the extras bucket if you haven't
scoop install musescore
```

## License

MIT.

## Changelog

### 3.1.0

Add export to other formats.

### 3.0.0

Complete re-write of musdl to use IPNS instead of relying on MuseScore's API, which can break anytime.

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
