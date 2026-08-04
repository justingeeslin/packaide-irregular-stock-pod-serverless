FROM python:3.14-slim

LABEL maintainer="info@blib.la"
LABEL org.opencontainers.image.source="https://github.com/blib-la/runpod-worker-helloworld"
LABEL org.opencontainers.image.description="RunPod worker for Packaide irregular-stock SVG nesting"

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    BOOST_VERSION=1.89.0 \
    BOOST_VERSION_UNDERSCORE=1_89_0 \
    CMAKE_PREFIX_PATH=/usr/local \
    LD_LIBRARY_PATH=/usr/local/lib

WORKDIR /

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      bash \
      build-essential \
      ca-certificates \
      cmake \
      curl \
      git \
      libcgal-dev \
      libgmp-dev \
      libmpfr-dev \
      ninja-build \
      pkg-config && \
    rm -rf /var/lib/apt/lists/*

# Packaide's current develop branch still uses Boost.Python and looks for a
# library matching Python 3.14, e.g. libboost_python314.
RUN curl -fsSL "https://archives.boost.io/release/${BOOST_VERSION}/source/boost_${BOOST_VERSION_UNDERSCORE}.tar.gz" \
      | tar -xz -C /tmp && \
    cd "/tmp/boost_${BOOST_VERSION_UNDERSCORE}" && \
    ./bootstrap.sh --with-python=python3 --with-libraries=python && \
    ./b2 -j"$(nproc)" --with-python link=shared threading=multi runtime-link=shared install && \
    ldconfig && \
    rm -rf "/tmp/boost_${BOOST_VERSION_UNDERSCORE}"

COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY src/ ./
RUN chmod +x /start.sh

CMD ["/start.sh"]
