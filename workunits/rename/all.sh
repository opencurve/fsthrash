#!/usr/bin/env bash
set -ex

mkdir -p ./a/a
mkdir -p ./b/b
mkdir -p ./c/c
mkdir -p ./d/d

bash pri_nul.sh


bash rem_nul.sh
rm -r ./?/* || true

bash pri_pri.sh
rm -r ./?/* || true

bash rem_pri.sh
rm -r ./?/* || true

bash rem_rem.sh
rm -r ./?/* || true

bash pri_nul.sh
rm -r ./?/* || true

bash pri_pri.sh
rm -r ./?/* || true

bash dir_pri_pri.sh
rm -r ./?/* || true
