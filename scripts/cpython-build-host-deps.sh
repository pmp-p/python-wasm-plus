. ${CONFIG:-config}

echo "
    *   cpython-build-host-deps pip==$PIP   *
" 1>&2


# https://stackoverflow.com/questions/6301003/stopping-setup-py-from-installing-as-egg
# python3 setup.py install --single-version-externally-managed --root=/
SPY="$HPY setup.py install --single-version-externally-managed --root=/"


# just in case
$PIP install pip --upgrade


# to remove ctypes deps
$PIP install setuptools --upgrade


HPFX=./devices/x86_64/usr/lib/python${PYBUILD}
rm -rf $HPFX/ensurepip/_bundled/*-py3-none-any.whl


for moveit in setuptools _distutils _distutils_hack pkg_resources
do
    if [ -d $HPFX/site-packages/${moveit} ]
    then
        echo "
        * migrating ${moveit}
"
        rm -rf $HPFX/${moveit} rm -rf $HPFX/${moveit}-*
        mv $HPFX/site-packages/${moveit}  $HPFX/
        mv $HPFX/site-packages/${moveit}-* $HPFX/
    fi
done


# https://github.com/aroberge/ideas, for code transformation
$PIP install token-utils

export CC=clang

rm -fr $ROOT/build/pycache/*


git_update () {
    SRC=$(basename $1)
    echo "
    * updating $SRC
"
    if [ -d $SRC ]
    then
        pushd $SRC
        if git pull||grep -q 'Already up to date'
        then
            export REBUILD=${REBUILD:-false}
        else
            export REBUILD=true
        fi
        popd
    else
        git clone $1
    fi
}

#===================================================================

mkdir -p src
pushd src

if false
then
    # pcpp   https://pypi.org/project/pcpp/
    # A C99 preprocessor written in pure Python
    $PIP install pcpp --user
fi


for req in pycparser
do
    pip3 download --dest $(pwd) --no-binary :all: $req
    archive=$(echo -n $req-*z)
    echo $archive
    tar xfz $archive && rm $archive
    pushd $req-*
    $PIP install .
    popd
done


rm cffi-branch-default.zip
wget -q https://foss.heptapod.net/pypy/cffi/-/archive/branch/default/cffi-branch-default.zip
unzip -o -q cffi-branch-default.zip

pushd cffi-branch-default
    $PIP install .
popd


## cython 3 ( not out yet )
#if $HPY -m cython -V 2>&1|grep -q 'version 3.0.'
#then
#    echo  found cython 3+
#else
#    git_update https://github.com/cython/cython
#    pushd cython
#    $PIP install .
#    popd
#fi


if [ -d pymunk-4.0.0 ]
then
    pushd pymunk-4.0.0

    [ -d $HOST_PREFIX/lib/python3.${PYMINOR}/site-packages/pymunk4 ] && rm -rf $HOST_PREFIX/lib/python3.${PYMINOR}/site-packages/pymunk4
    rm -f  build/lib/pymunk/* chipmunk_src/*.so chipmunk_src/*/*.o
    $HPY setup.py build_chipmunk
    $SPY
    mv $HOST_PREFIX/lib/python3.${PYMINOR}/site-packages/pymunk/libchipmunk.so $HOST_PREFIX/lib/python3.${PYMINOR}/site-packages/pymunk/libchipmunk64.so
    mv $HOST_PREFIX/lib/python3.${PYMINOR}/site-packages/pymunk $HOST_PREFIX/lib/python3.${PYMINOR}/site-packages/pymunk4
    popd
fi




# ${ROOT}/bin/python3-${ABI_NAME} -m pip $MODE --use-feature=2020-resolver --no-use-pep517 --no-binary :all: $@
#for req in $(find "${ORIGIN}/projects" -maxdepth 2 -type f |grep /requirements.txt$)



# TODO: build/patch from sources pip packages here.
# ${ROOT}/bin/pip3 download --dest ${CROSSDIR} --no-binary :all: setuptools pip

popd










unset CC

























#
