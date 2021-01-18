// 'Glue' code between musdl (py) and musescore-downloader (js).

import {ScoreInfoInPage} from "../musescore-downloader/src/scoreinfo.ts"

var musdl = {};

var scoreinfo = new ScoreInfoInPage();

musdl["id"] = scoreinfo.id

window._musdl = musdl;
