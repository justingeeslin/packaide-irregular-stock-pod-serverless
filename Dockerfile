FROM python:3.14-slim AS builder

LABEL maintainer="info@blib.la"
LABEL org.opencontainers.image.source="https://github.com/blib-la/runpod-worker-helloworld"
LABEL org.opencontainers.image.description="RunPod worker for Packaide irregular-stock SVG nesting"

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    BOOST_VERSION=1.89.0 \
    BOOST_VERSION_UNDERSCORE=1_89_0 \
    CMAKE_PREFIX_PATH=/usr/local \
    LD_LIBRARY_PATH=/usr/local/lib \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:${PATH}"

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

WORKDIR /

RUN set -eux; \
    echo "=== packaide worker build: builder diagnostics ==="; \
    python --version; \
    uname -a; \
    dpkg --print-architecture

RUN set -eux; \
    echo "=== installing native build dependencies: CGAL, CMake, compiler, git ==="; \
    apt-get update && \
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
    rm -rf /var/lib/apt/lists/*; \
    echo "=== native build dependencies installed ==="; \
    cmake --version; \
    gcc --version | head -n 1; \
    g++ --version | head -n 1; \
    dpkg-query -W libcgal-dev libgmp-dev libmpfr-dev

# Packaide's current develop branch still uses Boost.Python and looks for a
# library matching Python 3.14, e.g. libboost_python314.
RUN set -eux; \
    echo "=== downloading Boost ${BOOST_VERSION} source ==="; \
    curl -fsSL -o /tmp/boost.tar.gz "https://archives.boost.io/release/${BOOST_VERSION}/source/boost_${BOOST_VERSION_UNDERSCORE}.tar.gz"; \
    tar -xzf /tmp/boost.tar.gz -C /tmp; \
    cd "/tmp/boost_${BOOST_VERSION_UNDERSCORE}"; \
    echo "=== bootstrapping Boost.Python for $(python --version) ==="; \
    ./bootstrap.sh --with-python=python3 --with-libraries=python; \
    echo "=== compiling and installing Boost.Python; this can take several minutes ==="; \
    ./b2 -d0 -j"$(nproc)" --with-python link=shared threading=multi runtime-link=shared install; \
    ldconfig; \
    ls -l /usr/local/lib/libboost_python314.so*; \
    rm -rf "/tmp/boost_${BOOST_VERSION_UNDERSCORE}" /tmp/boost.tar.gz; \
    echo "=== Boost.Python install complete ==="

COPY requirements.txt ./
RUN set -eux; \
    echo "=== creating Python virtual environment at ${VIRTUAL_ENV} ==="; \
    python -m venv "${VIRTUAL_ENV}"; \
    echo "=== installing Python dependencies from requirements.txt ==="; \
    pip install --upgrade pip && \
    pip install --progress-bar off -r requirements.txt; \
    echo "=== verifying native Packaide and RunPod imports ==="; \
    python -c "import packaide, packaide_irregular_stock, runpod; print('import smoke ok')"

FROM python:3.14-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:${PATH}" \
    LD_LIBRARY_PATH=/usr/local/lib

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

WORKDIR /

RUN set -eux; \
    echo "=== packaide worker runtime: installing shared runtime libraries ==="; \
    apt-get update && \
    apt-get install -y --no-install-recommends \
      bash \
      ca-certificates \
      libgmp10 \
      libmpfr6 && \
    rm -rf /var/lib/apt/lists/*; \
    python --version; \
    dpkg --print-architecture

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /usr/local/lib/libboost_python314.so* /usr/local/lib/

COPY src/ ./
RUN set -eux; \
    chmod +x /start.sh; \
    echo "=== verifying runtime imports and handler syntax ==="; \
    python -m py_compile /rp_handler.py; \
    python -c "import packaide, packaide_irregular_stock, runpod, rp_handler; print('runtime smoke ok')"

CMD ["/start.sh"]
