#!/bin/bash -xe
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd "$DIR"

npm install
npm run build

OUT=../build/snap/www
mkdir -p "$OUT"
cp -r dist/* "$OUT"
