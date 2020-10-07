# musdl

![logo](https://raw.githubusercontent.com/ongyx/musdl/master/logo.jpg "musdl")

# NOTE:
_**The author of musdl does NOT condone piracy in any way, and is not responsible for anything that happens as a result of piracy arising from the use of musdl.**_

musdl ([mus]score [d]own[l]oader) is a Python script that I wrote to make downloading scores from Musescore easy.

It is meant to be used as a command-line tool, but can also be imported and used as a module:

```python
from musdl import Score

my_score = Score(...)  # the Musescore url goes here
data = my_score.download("mp3")  # download as mp3, returns as bytes
```

## Why?
musdl was inspired by [musescore-downloader](https://github.com/Xmader/musescore-downloader), which is written in TypeScript. But, what if you wanted to run it without a web browser? That's why I made a Python equivalent.

## **cough cough** takedown request something something **cough cough**
Take a look at this [issue](https://github.com/Xmader/musescore-downloader/issues/5) in the same repo.

## Requirements
- `requests` - Downloader.
- `beautifulsoup4` - Powerful HTML parser.

For downloading PDFs:
- `reportlab` - Make PDFs.
- `svglib` - Convert SVGs into Reportlab drawings.

## Hacking

All my python projects now use [flit](https://pypi.org/project/flit) to build and publish.
So you need to `python3 -m pip install flit` first.

```
git clone https://github.com/onyxware/musdl
cd musdl
flit build
```

## Install
`(python3 -m) pip install musdl`

If you want to download PDFs, you need to install the `pdf` extra:

`(python3 -m) pip install musdl[pdf]`

## License
MIT.

## Changelog

### 2020.10.7
Fixed PDF scaling issue on Windows.
Move to date-based versioning.

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
