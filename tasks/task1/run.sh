#!/usr/bin/env bash
set -e

python main.py | grep -Fx "Hello, world!"