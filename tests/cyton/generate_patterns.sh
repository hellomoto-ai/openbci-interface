#!/usr/bin/env bash

set -euo pipefail

cd "$( dirname "${BASH_SOURCE[0]}" )"
javac Gen16bitPatterns.java
java Gen16bitPatterns > 16bit_patterns.txt
javac Gen24bitPatterns.java
java Gen24bitPatterns > 24bit_patterns.txt
