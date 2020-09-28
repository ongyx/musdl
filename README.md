# musdl

# NOTE:
_**The author of musdl does NOT condone piracy in any way, and is not responsible for anything that happens as a result of piracy arising from the use of mudl.**_

musdl (Musescore Downloader) is a Python script that I wrote to make it easier to download scores from Musescore.

## Why?
See the [original](https://github.com/Xmader/musescore-downloader) Javascript version for more infomation.

## takedown request something something
Take a look at this [issue](https://github.com/Xmader/musescore-downloader/issues/5) in the (same) Javascript downloader repo.

## Requirements
- `requests` - Downloader.
- `beautifulsoup4` - Powerful HTML parser.

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
[MIT](/LICENSE)

## Changelog

### 1.1.2
Version bump, use Flit to build instead of `setup.py`.
Updated README too.

### 1.1.0
Added MusicXML download option, thanks to [JPFrancoia](https://github.com/JPFrancoia) for the update!

### 1.0.0
Initial version.
