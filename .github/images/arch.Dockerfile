FROM archlinux:base-devel
RUN pacman -Syu --needed --noconfirm \
       cmake git glib2 json-glib kidletime pkgconf qt6-base \
    && pacman -Scc --noconfirm
