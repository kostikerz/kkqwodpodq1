#!/bin/sh
# Independent reference commands; never used by the analyzer itself.
set -eu
mkdir -p artifacts/reference
for package in apt bash coreutils; do
    apt-cache policy "$package" > "artifacts/reference/$package-policy.txt"
    apt-cache depends "$package" > "artifacts/reference/$package-depends.txt"
    apt-cache dotty "$package" > "artifacts/reference/$package.dot"
    apt-get --simulate --no-install-recommends install "$package" \
        > "artifacts/reference/$package-simulation.txt"
done
printf '%s\n' 'Reference output is in artifacts/reference'
