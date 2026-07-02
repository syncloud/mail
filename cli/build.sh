#!/bin/bash -e
DIR=$(cd "$(dirname "$0")" && pwd)
cd "$DIR"

OUT_HOOKS=../build/snap/meta/hooks
OUT_BIN=../build/snap/bin
mkdir -p "$OUT_HOOKS" "$OUT_BIN"

CGO_ENABLED=0 go build -buildvcs=false -o "$OUT_HOOKS/install"      ./cmd/install
CGO_ENABLED=0 go build -buildvcs=false -o "$OUT_HOOKS/configure"    ./cmd/configure
CGO_ENABLED=0 go build -buildvcs=false -o "$OUT_HOOKS/post-refresh" ./cmd/post-refresh
CGO_ENABLED=0 go build -buildvcs=false -o "$OUT_BIN/cli"            ./cmd/cli
