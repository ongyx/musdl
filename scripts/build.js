var fs = require("fs");
var path = require("path");

var browserify = require("browserify")

const msPath = path.dirname(require.resolve("musescore-downloader/package.json"));

const PATCHES = {
    "src/scoreinfo.ts": function (data) {
        return data.replaceAll("this: typeof scoreinfo", "")
    }
};


function applyPatches() {
    Object.keys(PATCHES).forEach(function (relpath) {
        callback = PATCHES[relpath];
        fullPath = path.join(msPath, relpath);
        fs.readFile(
            fullPath,
            "utf8",
            function (err, data) {
                if (err) { return console.log(err); }
                patched = callback(data);
                fs.writeFile(fullPath, patched, "utf8", function() {})
            }
        );
    });
}


function build() {
    applyPatches();
    browserify(path.join(__dirname, "_musdl.js"), {standalone: "musdl", debug: true})
        .plugin("tsify", {global: true})
        .transform("babelify", {
            presets: ["@babel/env"],
            //plugins: [
            //    "@babel/plugin-transform-runtime",
            //    "@babel/plugin-transform-async-to-generator",
            //    "@babel/plugin-transform-regenerator"
            //],
            global: true,
            extensions: [".js", ".ts"],
        })
        .bundle()
        .pipe(fs.createWriteStream(path.join(__dirname, "../musdl/musdl.js")));
}


if (typeof require !== 'undefined' && require.main === module) {
    build()
}