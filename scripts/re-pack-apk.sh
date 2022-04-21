#!/bin/bash

if [ -d .git ]
then
    CREDITS_GH=$(git remote -v|head -n1 | cut -d' ' -f1|cut -c8-)
else
    CREDITS_GH="Not a git repo"
fi



WEB=${1:-demo}

CN=$(basename $(pwd))

APK=$CN.apk
echo "
APK=$APK

Web Service Folder : $WEB

assets folder: $(pwd)

CREDITS:
    GH $CREDITS_GH

"

export TEMP=some_name_no_one_would_choose


if [ -d static ]
then
    rm ../../build/$WEB/$APK $APK

    mkdir $TEMP

    mv static ../$APK-static
    mv * ./$TEMP/ 2>/dev/null

    mv ./$TEMP/META-INF ./
    mv ./$TEMP/package.toml ./

    mv $TEMP assets

    zip -r9 ${APK} . --exclude .git/\* -x .gitignore | wc -l
    sync
    if du -hs ${APK}
    then

        mv ../$APK-static static


        mv assets ./$TEMP/
        mv ./$TEMP/* ./
        rmdir ./$TEMP

        cat > static/$CN.html <<END
        <html>
        <pre>
        Github: <a href="$CREDITS_GH">$CREDITS_GH</a>
END


        if [ -d .git ]
        then
            git status 2>&1 |grep -v \(use |grep -v ^$|grep -v :$|\
                grep -v ^Your |grep -v ^On | grep -v apk$ |grep -v static/ >> static/$CN.html
        else
            cat package.toml >> static/$CN.html
        fi

        cat >> static/$CN.html <<END
        </pre>
        </html>
END

        if [ -f inline.html ]
        then
            cat inline.html >> static/$CN.html
        fi


        mv $APK ../../build/$WEB/
        ln static/* ../../build/$WEB/
        sync
    else
        echo "


        *****************************************************************************




                ZIP failure at $(pwd) for ${APK}




        *****************************************************************************
"
    fi
else
    echo "no folder 'static' found, Are you in app folder ?"
fi


