ARG FEDORA_VERSION=45
FROM fedora:${FEDORA_VERSION}
RUN dnf install -y --setopt=install_weak_deps=False --setopt=tsflags=nodocs \
       cmake gcc-c++ git glib2-devel json-glib-devel kf6-kidletime-devel \
       pkgconf-pkg-config qt6-qtbase-devel rpm-build tar gzip \
    && dnf clean all
