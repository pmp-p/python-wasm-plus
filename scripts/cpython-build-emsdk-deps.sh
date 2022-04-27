#!/bin/bash

. ${CONFIG:-config}

. ./scripts/emsdk-fetch.sh

# ../../devices/x86_64/usr/bin/python3-wasm -mpip install .
# not working because python startup is skipped

export PYSETUP="$HOST_PREFIX/bin/python3-wasm setup.py install --single-version-externally-managed --root=/"


# https://download.osgeo.org/libtiff/tiff-4.3.0.tar.gz
# http://code.google.com/intl/en-US/speed/webp/index.html
#

ALL="-fPIC -s USE_SDL=2 -sUSE_LIBPNG -sUSE_LIBJPEG $CPPFLAGS"
CNF="emconfigure ./configure --prefix=$PREFIX --with-pic --disable-shared"


# ncurses ncursesw


# SDL_image

cd $ROOT/src

TIFF_VER="4.3.0"
WEBP_VER="1.2.2"

# ================== tiff ===================

if false
then
    if [ -f ../devices/emsdk/usr/lib/libtiff.a ]
    then
        echo "
        * tiff $TIFF_VER already built
    "
    else
        wget -c https://download.osgeo.org/libtiff/tiff-$TIFF_VER.tar.gz && tar xfz tiff-$TIFF_VER.tar.gz
        pushd tiff-$TIFF_VER
        EMCC_CFLAGS="$ALL" $CNF
        EMCC_CFLAGS="$ALL" emmake make 2>&1>/dev/null
        emmake make install 2>&1>/dev/null
        popd
    fi
fi

# ============ webp =========================

if [ -f ../devices/emsdk/usr/lib/libwebp.a ]
then
    echo "
    * libwep $WEBP_VER already built
"
else
    wget -c https://storage.googleapis.com/downloads.webmproject.org/releases/webp/libwebp-$WEBP_VER.tar.gz \
        && tar xfz libwebp-$WEBP_VER.tar.gz
    pushd libwebp-$WEBP_VER
    EMCC_CFLAGS="$ALL" $CNF \
     --disable-threading --disable-neon --disable-sse2 --enable-libwebpdecoder 2>&1>/dev/null
    EMCC_CFLAGS="$ALL" emmake make 2>&1>/dev/null
    emmake make install 2>&1>/dev/null
    popd
fi

# ================== SDL2_image ====================

if [ -f ../devices/emsdk/usr/lib/libSDL2_image.a ]
then
    echo "
    * SDL2_image already built
"
else
    [ -d SDL_image ] || git clone https://github.com/libsdl-org/SDL_image
    pushd SDL_image
    CFLAGS=$CPOPTS EMCC_CFLAGS="$ALL" $CNF \
     --disable-sdltest --disable-jpg-shared --disable-png-shared
    #--disable-tif-shared
    EMCC_CFLAGS="$ALL" emmake make
    emmake make install
    popd
fi


# =============== ncurses ===========================

NCOPTS="--enable-ext-colors --enable-ext-mouse --prefix=$PREFIX --disable-echo --without-pthread \
 --disable-database --without-tests --without-tack --without-progs --without-manpages \
 --disable-db-install --enable-termcap --without-cxx --without-cxx-binding --enable-pc-files \
 --with-pkg-config-libdir=$PREFIX/lib/pkgconfig \
 --without-termlib"

if [ -f ../devices/emsdk/usr/lib/libncurses.a ]
then
    echo "
    * ncurses already built
"
else
    wget -c https://ftp.gnu.org/pub/gnu/ncurses/ncurses-6.1.tar.gz && tar xfz ncurses-6.1.tar.gz
    pushd ncurses-6.1
    [ -f patch.done ] || patch -p1 < $ROOT/support/__EMSCRIPTEN__.deps/ncurses-6.1_emscripten.patch
    touch patch.done
    popd

    mkdir ../build/ncurses
    pushd ../build/ncurses
    make clean
    CC=clang CFLAGS="-fpic -Wno-unused-command-line-argument" $ROOT/src/ncurses-6.1/configure \
     $NCOPTS && make && make install

    CFLAGS="-fpic -Wno-unused-command-line-argument" emconfigure \
     $ROOT/src/ncurses-6.1/configure \
     $NCOPTS

    if patch -p1 < $ROOT/support/__EMSCRIPTEN__.deps/ncurses-6.1_emscripten_make.patch
    then
        emmake make clean
        if emmake make
        then
            emmake make install
        fi
    fi
fi

if [ -f ../devices/emsdk/usr/lib/libncursesw.a ]
then
    echo "
    * ncursesw already built
"
else
    # build wide char
    pushd ../build/ncurses
    make clean
    CC=clang CFLAGS="-fpic -Wno-unused-command-line-argument" $ROOT/src/ncurses-6.1/configure \
     $NCOPTS --enable-widec && make && make install

    CFLAGS="-fpic -Wno-unused-command-line-argument" emconfigure \
     $ROOT/src/ncurses-6.1/configure \
     $NCOPTS --enable-widec

    if patch -p1 < $ROOT/support/__EMSCRIPTEN__.deps/ncurses-6.1_emscripten_makew.patch
    then
        emmake make clean
        if emmake make
        then
            emmake make install
        fi
    fi
    popd
fi


# TODO https://github.com/onelivesleft/PrettyErrors







