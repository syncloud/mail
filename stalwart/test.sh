#!/bin/bash -ex

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

${DIR}/../build/snap/stalwart/stalwart --version
