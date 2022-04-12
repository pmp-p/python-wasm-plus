. ${CONFIG:-config}

rm -fr $ROOT/./build/pycache/*


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
wget https://foss.heptapod.net/pypy/cffi/-/archive/branch/default/cffi-branch-default.zip
unzip -o -q cffi-branch-default.zip

pushd cffi-branch-default
    $PIP install .
popd


# cython 3 ( not out yet )
if python3 -m cython -V 2>&1|grep -q 'version 3.0.'
then
    echo  found cython 3+
else
    git_update https://github.com/cython/cython
    pushd cython
    $PIP install .
    popd
fi


# ${ROOT}/bin/python3-${ABI_NAME} -m pip $MODE --use-feature=2020-resolver --no-use-pep517 --no-binary :all: $@
#for req in $(find "${ORIGIN}/projects" -maxdepth 2 -type f |grep /requirements.txt$)



# TODO: build/patch from sources pip packages here.
# ${ROOT}/bin/pip3 download --dest ${CROSSDIR} --no-binary :all: setuptools pip

popd

























































#
