
. ${CONFIG:-config}

if [[ ! -z ${EMSDK+z} ]]
then
    echo -n
else
    . scripts/emsdk-fetch.sh
fi

pushd src

if [ -d cython ]
then
    pushd cython

    if git pull|grep -q 'Already up to date'
    then
        export REBUILD=${REBUILD:-false}
    else
        export REBUILD=true
    fi
    popd

else
    git clone https://github.com/cython/cython
fi


if $REBUILD
then
    pushd cython
    $HOST/bin/python3 setup.py install
    popd
fi


popd
