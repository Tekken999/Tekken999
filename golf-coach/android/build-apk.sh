#!/usr/bin/env bash
# Builds RangeCoach.apk without Gradle: the web app + bundled MediaPipe files are
# packed as assets, served by a tiny WebView activity (src/.../MainActivity.java).
#
# Needs: aapt2, zipalign, apksigner, javac/keytool (JDK 11+), a dexer (d8 or
# dalvik-exchange), zip, curl, npm, and an android.jar (API 23+).
# On Ubuntu:  apt-get install android-sdk-build-tools android-sdk-platform-23 \
#               apksigner zipalign dalvik-exchange zip default-jdk-headless
# Usage:      golf-coach/android/build-apk.sh   ->  golf-coach/android/build/RangeCoach.apk
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
APP="$(dirname "$HERE")"
OUT="$HERE/build"
CACHE="$HERE/.cache"
MP_VERSION=0.10.14
MIN_SDK=24
TARGET_SDK=34

ANDROID_JAR="${ANDROID_JAR:-$(ls -d "${ANDROID_HOME:-/nonexistent}"/platforms/android-*/android.jar /usr/lib/android-sdk/platforms/*/android.jar 2>/dev/null | sort -V | tail -1 || true)}"
[ -f "$ANDROID_JAR" ] || { echo "android.jar not found. Set ANDROID_JAR or ANDROID_HOME." >&2; exit 1; }

VERSION_CODE="${VERSION_CODE:-$(git -C "$APP" rev-list --count HEAD 2>/dev/null || echo 1)}"
VERSION_NAME="${VERSION_NAME:-1.0.$VERSION_CODE}"

echo "==> Fetching MediaPipe $MP_VERSION and pose models (cached)"
mkdir -p "$CACHE"
if [ ! -f "$CACHE/mediapipe/vision_bundle.mjs" ]; then
  (cd "$CACHE" && npm pack "@mediapipe/tasks-vision@$MP_VERSION" --silent >/dev/null \
    && tar xzf "mediapipe-tasks-vision-$MP_VERSION.tgz" && rm -rf mediapipe && mv package mediapipe \
    && rm -f "mediapipe-tasks-vision-$MP_VERSION.tgz")
fi
for m in lite full; do
  f="$CACHE/pose_landmarker_$m.task"
  [ -s "$f" ] || curl -fsSL -o "$f" \
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_$m/float16/1/pose_landmarker_$m.task"
done

echo "==> Staging web assets"
rm -rf "$OUT"
WWW="$OUT/assets/www"
mkdir -p "$WWW/vendor/mediapipe/wasm" "$WWW/models" "$OUT/classes"
cp -r "$APP/index.html" "$APP/css" "$APP/js" "$WWW/"
cp "$CACHE/mediapipe/vision_bundle.mjs" "$WWW/vendor/mediapipe/"
cp "$CACHE"/mediapipe/wasm/*.js "$CACHE"/mediapipe/wasm/*.wasm "$WWW/vendor/mediapipe/wasm/"
cp "$CACHE"/pose_landmarker_*.task "$WWW/models/"
# Point pose.js at the bundled files instead of the CDN.
CONFIG="<script>window.RC_ASSETS={bundle:'/vendor/mediapipe/vision_bundle.mjs',wasm:'/vendor/mediapipe/wasm',models:{lite:'/models/pose_landmarker_lite.task',full:'/models/pose_landmarker_full.task'}};</script>"
sed -i "s#  <script type=\"module\" src=\"js/app.js\"></script>#  $CONFIG\n&#" "$WWW/index.html"
grep -q RC_ASSETS "$WWW/index.html" || { echo "Failed to inject asset config" >&2; exit 1; }

echo "==> Compiling resources"
aapt2 compile --dir "$HERE/res" -o "$OUT/res.zip"
aapt2 link -o "$OUT/unsigned.apk" -I "$ANDROID_JAR" \
  --manifest "$HERE/AndroidManifest.xml" \
  --min-sdk-version "$MIN_SDK" --target-sdk-version "$TARGET_SDK" \
  --version-code "$VERSION_CODE" --version-name "$VERSION_NAME" --replace-version \
  -A "$OUT/assets" "$OUT/res.zip"

echo "==> Compiling Java"
javac -nowarn -Xlint:-options -source 8 -target 8 -bootclasspath "$ANDROID_JAR" \
  -d "$OUT/classes" $(find "$HERE/src" -name '*.java')
if command -v d8 >/dev/null; then
  d8 --min-api "$MIN_SDK" --lib "$ANDROID_JAR" --output "$OUT" $(find "$OUT/classes" -name '*.class')
else
  dalvik-exchange --dex --min-sdk-version=$MIN_SDK --output="$OUT/classes.dex" "$OUT/classes"
fi
(cd "$OUT" && zip -q unsigned.apk classes.dex)

echo "==> Aligning and signing"
KEYSTORE="${KEYSTORE:-$HERE/rangecoach.keystore}"
if [ ! -f "$KEYSTORE" ]; then
  keytool -genkeypair -keystore "$KEYSTORE" -storepass android -keypass android -alias rangecoach \
    -keyalg RSA -keysize 2048 -validity 10000 -dname "CN=Range Coach" >/dev/null 2>&1
fi
zipalign -f -p 4 "$OUT/unsigned.apk" "$OUT/aligned.apk"
apksigner sign --ks "$KEYSTORE" --ks-pass pass:android --key-pass pass:android \
  --out "$OUT/RangeCoach.apk" "$OUT/aligned.apk"
apksigner verify "$OUT/RangeCoach.apk"
rm -f "$OUT/unsigned.apk" "$OUT/aligned.apk" "$OUT/RangeCoach.apk.idsig"

echo "==> Built $OUT/RangeCoach.apk ($(du -h "$OUT/RangeCoach.apk" | cut -f1), version $VERSION_NAME)"
