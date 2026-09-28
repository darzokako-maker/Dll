#!/usr/bin/env sh
# Lightweight Gradle launcher for CI and local APK builds.
set -eu
GRADLE_VERSION=8.14.4
BASE_DIR="${GRADLE_USER_HOME:-$HOME/.gradle}/wrapper/dists/gradle-${GRADLE_VERSION}-bin"
GRADLE_HOME="$BASE_DIR/gradle-${GRADLE_VERSION}"
if [ ! -x "$GRADLE_HOME/bin/gradle" ]; then
  mkdir -p "$BASE_DIR"
  ARCHIVE="$BASE_DIR/gradle-${GRADLE_VERSION}-bin.zip"
  if [ ! -f "$ARCHIVE" ]; then
    curl -fsSL "https://services.gradle.org/distributions/gradle-${GRADLE_VERSION}-bin.zip" -o "$ARCHIVE"
  fi
  unzip -q -o "$ARCHIVE" -d "$BASE_DIR"
fi
exec "$GRADLE_HOME/bin/gradle" "$@"
