#!/bin/bash
APK=$(basename $(pwd)).apk
echo "
APK=$APK
"
rm ../../build/service/$APK $APK
mkdir assets
mv static ../$APK-static
mv * assets/
mv assets/META-INF ./
mv assets/package.toml ./

zip -r9 ${APK} . --exclude .git/\* -x .gitignore
mv ../$APK-static static

mv assets/* ./
rmdir assets
ln $APK ../../build/service/
ln static/* ../../build/service/

