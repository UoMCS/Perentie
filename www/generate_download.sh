#!/bin/bash

# Generates a download.zip which doesn't include this www directory.

# XXX Fix directory in ZIP
[ -f "download.zip" ] && rm "download.zip"
git ls-files ../ | grep -xRE "^[.][.]/.*" | zip download -@
