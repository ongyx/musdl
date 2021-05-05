# Table of Contents

* [musdl](#musdl)
  * [Metadata](#musdl.Metadata)
  * [Score](#musdl.Score)
    * [as\_mscz](#musdl.Score.as_mscz)
    * [export](#musdl.Score.export)
    * [from\_file](#musdl.Score.from_file)
  * [OnlineScore](#musdl.OnlineScore)
    * [update\_meta](#musdl.OnlineScore.update_meta)

<a name="musdl"></a>
# musdl

[mus]escore [d]own[l]oader, ported from TypeScript

<a name="musdl.Metadata"></a>
## Metadata Objects

```python
@dataclass
class Metadata(Mapping)
```

A score's metadata.

**Attributes**:

  
- `arranger` - Who arranged the score.
  
- `composer` - Who composed the score.
  
- `copyright` - The copyright statement.
  
- `creation_date` - When the score was created.
  
- `lyricist` - Who created the lyrics for the score.
  
- `movement_number` - Self-explainatory.
  
- `movement_title` - Self-explainatory.
  
- `platform` - Which OS the score was created on (i.e Microsoft Windows).
  
- `poet` - Who created the poem the score's lyrics is based on, if any.
  
- `source` - The URL of the score (if it was hosted online).
  
- `translator` - Who translated the lyrics of the score, if any.
  
- `work_number` - Self-explainatory.
  
- `work_title` - Self-explainatory.

<a name="musdl.Score"></a>
## Score Objects

```python
class Score()
```

A score stored on disk (as a .mscz file).

**Arguments**:

- `score_data` - The score data as bytes.
  It must be in the mscz format.
  

**Attributes**:

- `meta` _Metadata_ - A map of metadata tags to their values.
  Attribute-like access is also supported.
  
- `scorexml` _bs4.BeautifulSoup_ - The parsed score (from XML).

<a name="musdl.Score.as_mscz"></a>
#### as\_mscz

```python
 | as_mscz() -> bytes
```

Get the raw mscz file.

**Returns**:

  The .mscz file, as raw bytes.

<a name="musdl.Score.export"></a>
#### export

```python
 | export(fmt: str, path: Union[str, pathlib.Path]) -> pathlib.Path
```

Export this score to another format and save it.
The format must be one of ['pdf', 'mscz', 'mxl', 'mid', 'mp3', 'flac', 'ogg'].

**Arguments**:

- `fmt` - The export format.
- `path` - Where to save the export file to.
  The path should not have an extension, because it will be replaced
  by the correct extension for the export format.
  

**Returns**:

  The path to the exported file (with correct extension).
  

**Raises**:

  ValueError, if the format is invalid.

<a name="musdl.Score.from_file"></a>
#### from\_file

```python
 | @staticmethod
 | from_file(path: Union[str, pathlib.Path])
```

Open a score from an existing .mscz file.

**Arguments**:

- `path` - The path to the file.
  

**Returns**:

  The score object.

<a name="musdl.OnlineScore"></a>
## OnlineScore Objects

```python
class OnlineScore(Score)
```

A score hosted on musescore.

**Arguments**:

- `url` - The url to the score.
  

**Attributes**:

- `url` - See args.
- `global_cid` _str_ - The 'global key' used to access the mscz cid.
- `mscz_cid` _str_ - The 'mscz key' (specific to each score) used to access the mscz url.
- `mscz_url` _str_ - The url to the .mscz file.
- `session` _requests.Session_ - The session used to get the CID, as well as the .mscz file.

<a name="musdl.OnlineScore.update_meta"></a>
#### update\_meta

```python
 | update_meta()
```

Update the metadata in this score using the musescore webpage.
Note that this does not modify the dataset score itself: only the .meta attribute is updated.

