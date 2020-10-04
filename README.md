# musdl

![logo](https://raw.githubusercontent.com/ongyx/musdl/master/logo.jpg "musdl")

# NOTE:
_**The author of musdl does NOT condone piracy in any way, and is not responsible for anything that happens as a result of piracy arising from the use of musdl.**_

musdl (Musescore Downloader) is a Python script that I wrote to make it easier to download scores from Musescore.
It is meant to be used as a command-line tool, but can also be imported and used as a module:

```python
from musdl import Score

my_score = Score(...)  # the Musescore url goes here
data = my_score.download("mp3")  # download as mp3, returns as bytes
```

## Why?
See the [original](https://github.com/Xmader/musescore-downloader) Javascript version for more infomation.

## takedown request something something
Take a look at this [issue](https://github.com/Xmader/musescore-downloader/issues/5) in the (same) Javascript downloader repo.

## Requirements
- `requests` - Downloader.
- `beautifulsoup4` - Powerful HTML parser.
- `fpdf` - Create pdfs

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

## License
MIT.

## Changelog

### 2.1.0
Added PDF support. Tested on Linux (but not on Windows yet), requires Inkscape to work.

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
