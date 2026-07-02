#!/bin/bash -xe

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

${DIR}/../integration/openssl/bin/openssl version -a
