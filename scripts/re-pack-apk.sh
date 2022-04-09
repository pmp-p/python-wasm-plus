#!/bin/bash

export CREDITS_GH=$(git remote -v|head -n1 | cut -d' ' -f1|cut -c8-)

WEB=${1:-demo}

APK=$(basename $(pwd)).apk
echo "
APK=$APK

Web Service Folder : $WEB


CREDITS:
    GH $CREDITS_GH

"

rm ../../build/$WEB/$APK $APK
mkdir assets
mv static ../$APK-static
mv * assets/ 2>/dev/null

mv assets/META-INF ./
mv assets/package.toml ./

zip -r9 ${APK} . --exclude .git/\* -x .gitignore | wc -l
mv ../$APK-static static

cat > static/$APK.html <<END
<html>
<pre>
Github: <a href="$CREDITS_GH">$CREDITS_GH</a>
END

git status 2>&1 |grep -v \(use |grep -v ^$|grep -v :$|grep -v ^Your |grep -v ^On >> static/$APK.html
cat >> static/$APK.html <<END
</pre>
</html>
END


mv assets/* ./
rmdir assets
ln $APK ../../build/$WEB/
ln static/* ../../build/$WEB/


