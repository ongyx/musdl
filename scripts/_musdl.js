/*
musdl.js: musescore-downloader interface for Python.

remember, i am a Python dev, not a JS dev
pls open a issue on my github if anything goes wrong.
*/

import "core-js/es6/map";
import "core-js/web/timers";

import "regenerator-runtime/runtime";

// assuming that the url is already defined as global '_url'
require("global-jsdom")(
    "",
    {
        url: _url,
        contentType: "text/html",
        runScripts: "dangerously",
        resources: "usable"
    }
);

// at this point, we pretty much have a full DOM
// initiate musescore-downloader

const scoreinfo = require("musescore-downloader/src/scoreinfo.ts").scoreinfo;
const getFileUrl = require("musescore-downloader/src/file.ts").getFileUrl;