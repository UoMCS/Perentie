#!/bin/bash

# Generates a download.zip which doesn't include this www directory.

cd ..
git ls-files . | grep -vxRE "www/.*" | zip perentie -@
mv perentie.zip www/
