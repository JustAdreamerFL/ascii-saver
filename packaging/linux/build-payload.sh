#!/usr/bin/env bash
# Build a system-wide ASCII Saver payload for Debian, Fedora and Arch packages.
set -euo pipefail

destdir=${1:?usage: build-payload.sh DESTDIR}
root=$(cd -- "$(dirname -- "$0")/../.." && pwd)
version=$(head -n 1 "$root/VERSION")
prefix=${PREFIX:-/usr}
libdir=${LIBDIR:-$prefix/lib}
bindir="$prefix/bin"
appdir="$libdir/ascii-saver"
datadir="$prefix/share"
autostart_file="/etc/xdg/autostart/com.github.justadreamerfl.asciisaver.Watcher.desktop"
python=${PYTHON:-/usr/bin/python3}
builddir=${BUILD_DIR:-"$root/build/package"}

install -d \
    "$destdir$appdir" \
    "$destdir$appdir/effects" \
    "$destdir$bindir" \
    "$destdir$datadir/applications" \
    "$destdir$datadir/metainfo" \
    "$destdir$datadir/icons/hicolor/scalable/apps" \
    "$destdir/etc/xdg/autostart" \
    "$destdir$datadir/kwin/scripts/ascii-saver-fullscreen" \
    "$destdir$datadir/gnome-shell/extensions/ascii-saver-cursor@ascii-saver.local"

rm -rf -- "$builddir"
mkdir -p "$builddir"

if [[ -z "${TTFX_BINARY:-}" && -x "$root/.package-ttfx" ]]; then
    TTFX_BINARY="$root/.package-ttfx"
fi
if [[ -n "${TTFX_BINARY:-}" ]]; then
    install -m 0755 "$TTFX_BINARY" "$destdir$appdir/ttfx"
else
    export CARGO_TARGET_DIR="$builddir/cargo"
    cargo build --manifest-path "$root/ttfx-rust/Cargo.toml" --release --locked
    install -m 0755 "$CARGO_TARGET_DIR/release/ttfx" "$destdir$appdir/ttfx"
fi

cmake -S "$root/native/kde" -B "$builddir/kde" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="$prefix"
cmake --build "$builddir/kde" --parallel
install -m 0755 "$builddir/kde/ascii-saver-watcher" \
    "$destdir$appdir/ascii-saver-watcher-kde"

"${CC:-cc}" -O2 -g -Wall -Wextra \
    -DASCII_SAVER_VERSION="\"$version\"" \
    -I"$root/native/kde" \
    $(pkg-config --cflags gio-2.0 glib-2.0 gio-unix-2.0 json-glib-1.0) \
    "$root/native/gnome/gnome_idle_watcher.c" \
    -o "$destdir$appdir/ascii-saver-watcher-gnome" \
    $(pkg-config --libs gio-2.0 glib-2.0 gio-unix-2.0 json-glib-1.0)
chmod 0755 "$destdir$appdir/ascii-saver-watcher-gnome"

install -m 0644 "$root"/src/*.py "$destdir$appdir/"
install -m 0644 "$root/VERSION" "$destdir$appdir/VERSION"
install -m 0644 "$root/config/logo.txt" "$destdir$appdir/logo.txt"
install -m 0644 "$root"/preview-packs/*.aspr "$destdir$appdir/effects/"

for name in ascii-saver ascii-saverctl ascii-saver-settings ascii-saver-watcher; do
    sed \
        -e "s|@APP_DIR@|$appdir|g" \
        -e "s|@PYTHON@|$python|g" \
        -e "s|@BINDIR@|$bindir|g" \
        -e "s|@AUTOSTART_FILE@|$autostart_file|g" \
        "$root/packaging/linux/launchers/$name.in" \
        >"$destdir$bindir/$name"
    chmod 0755 "$destdir$bindir/$name"
done

sed "s|@APP@|$bindir/ascii-saver|g" \
    "$root/data/com.github.justadreamerfl.asciisaver.desktop.in" \
    >"$destdir$datadir/applications/com.github.justadreamerfl.asciisaver.desktop"
chmod 0644 "$destdir$datadir/applications/com.github.justadreamerfl.asciisaver.desktop"

install -m 0644 "$root/data/com.github.justadreamerfl.asciisaver.metainfo.xml" \
    "$destdir$datadir/metainfo/"
install -m 0644 "$root/data/icons/com.github.justadreamerfl.asciisaver.svg" \
    "$destdir$datadir/icons/hicolor/scalable/apps/"

sed "s|@WATCHER@|$bindir/ascii-saver-watcher|g" \
    "$root/packaging/linux/common/ascii-saver-watcher.desktop.in" \
    >"$destdir$autostart_file"
chmod 0644 "$destdir$autostart_file"

cp -a "$root/integrations/kwin-fullscreen/." \
    "$destdir$datadir/kwin/scripts/ascii-saver-fullscreen/"
cp -a "$root/integrations/gnome-shell-extension/ascii-saver-cursor@ascii-saver.local/." \
    "$destdir$datadir/gnome-shell/extensions/ascii-saver-cursor@ascii-saver.local/"
find "$destdir$datadir/kwin/scripts/ascii-saver-fullscreen" \
     "$destdir$datadir/gnome-shell/extensions/ascii-saver-cursor@ascii-saver.local" \
    -type f -exec chmod 0644 {} +

printf 'ASCII Saver %s payload installed under %s\n' "$version" "$destdir"
