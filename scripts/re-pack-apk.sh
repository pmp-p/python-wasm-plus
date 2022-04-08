#!/bin/bash

WEB=${1:-demo}

APK=$(basename $(pwd)).apk
echo "
APK=$APK

Web Service Folder : $WEB

"

rm ../../build/$WEB/$APK $APK
mkdir assets
mv static ../$APK-static
mv * assets/ 2>/dev/null

mv assets/META-INF ./
mv assets/package.toml ./

zip -r9 ${APK} . --exclude .git/\* -x .gitignore | wc -l
mv ../$APK-static static

mv assets/* ./
rmdir assets
ln $APK ../../build/$WEB/
ln static/* ../../build/$WEB/

