%global debug_package %{nil}

Name:           ascii-saver
Version:        0.111.0
Release:        1%{?dist}
Summary:        Animated terminal effect screensaver for GNOME and KDE

License:        MIT
URL:            https://github.com/JustAdreamerFL/ascii-saver
Source0:        %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildRequires:  cmake
BuildRequires:  gcc-c++
BuildRequires:  glib2-devel
BuildRequires:  json-glib-devel
BuildRequires:  kf6-kidletime-devel
BuildRequires:  pkgconf-pkg-config
BuildRequires:  qt6-qtbase-devel
BuildRequires:  cargo
BuildRequires:  rust

Requires:       desktop-file-utils
Requires:       gtk4
Requires:       libadwaita
Requires:       python3
Requires:       python3-gobject
Requires:       vte291-gtk4
Requires:       xdg-utils

Recommends:     gtk4-layer-shell

%description
ASCII Saver renders custom artwork with randomized terminal text effects when
the desktop session becomes idle. It supports multiple monitors, GNOME/Mutter
and KDE Plasma, dismisses the overlay on lock, and includes a libadwaita
control panel for artwork, playlists, palettes, previews and diagnostics.

The package ships prebuilt native idle watchers and the instrumented ttfx
renderer, so no Python virtual environment or Rust toolchain is needed on the
installed system.

%prep
%autosetup -n %{name}-%{version}

%build

%install
LIBDIR=%{_libdir} bash packaging/linux/build-payload.sh %{buildroot}

%files
%{_bindir}/ascii-saver
%{_bindir}/ascii-saverctl
%{_bindir}/ascii-saver-settings
%{_bindir}/ascii-saver-watcher
%{_libdir}/ascii-saver
%{_datadir}/applications/com.github.justadreamerfl.asciisaver.desktop
%{_datadir}/metainfo/com.github.justadreamerfl.asciisaver.metainfo.xml
%{_datadir}/icons/hicolor/scalable/apps/com.github.justadreamerfl.asciisaver.svg
%{_datadir}/kwin/scripts/ascii-saver-fullscreen
%{_datadir}/gnome-shell/extensions/ascii-saver-cursor@ascii-saver.local
%config(noreplace) /etc/xdg/autostart/com.github.justadreamerfl.asciisaver.Watcher.desktop
%license LICENSE
%doc ttfx-rust/NOTICE ttfx-rust/LICENSE

%changelog
* Mon Nov 23 2026 JustAdreamerFL <Slavouli@gmail.com> - 0.111.0-1
- Native RPM package with prebuilt ttfx and GNOME/KDE watchers.
- Consolidated source and package publishing in the Release workflow.
