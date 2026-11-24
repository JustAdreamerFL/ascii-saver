FROM debian:latest
RUN rm -f /etc/apt/apt.conf.d/docker-clean \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential ca-certificates cmake debhelper devscripts fakeroot git \
       libglib2.0-dev libjson-glib-dev libkf6idletime-dev pkg-config qt6-base-dev \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*.deb
