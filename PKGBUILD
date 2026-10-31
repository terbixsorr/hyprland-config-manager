# Maintainer: Arch Linux Hyprland Community
pkgname=hyprland-config-manager
pkgver=1.0.0
pkgrel=1
pkgdesc="Modern native GTK4/Libadwaita graphical configuration manager for Hyprland on Arch Linux"
arch=('any')
url="https://github.com/hyprwm/hyprland-config-manager"
license=('GPL-3.0-or-later')
depends=(
    'python>=3.9'
    'python-gobject'
    'gtk4'
    'libadwaita'
    'hyprland'
)
makedepends=(
    'python-build'
    'python-installer'
    'python-wheel'
    'python-setuptools'
)
optdepends=(
    'hyprpaper: Official Hyprland wallpaper daemon'
    'swww: Smooth animated Wayland wallpaper daemon'
    'swaybg: Lightweight Wayland wallpaper tool'
    'wl-clipboard: Wayland clipboard support'
    'xdg-utils: Opening folders and default apps'
)
source=()
sha256sums=()

build() {
    cd "$startdir"
    python -m build --wheel --no-isolation
}

package() {
    cd "$startdir"
    python -m installer --destdir="$pkgdir" dist/*.whl

    # Install XDG desktop entry
    install -Dm644 data/hyprland-config-manager.desktop \
        "$pkgdir/usr/share/applications/hyprland-config-manager.desktop"

    # Install scalable application icon
    install -Dm644 data/icons/hicolor/scalable/apps/hyprland-config-manager.svg \
        "$pkgdir/usr/share/icons/hicolor/scalable/apps/hyprland-config-manager.svg"
}
