#!/bin/bash

NEW_VERSION=$1

if [ -z "${NEW_VERSION}" ]; then
  read -p "Enter a new release version: "  NEW_VERSION
fi

echo "New Release Version ${NEW_VERSION}"

# Grab current version from index.html
CURRENT_VERSION=$(cat ../index.html | grep 'Current Version' | sed "s/.*<h1>.*: //" | sed "s/<\/h1>//")
echo "Current Release: ${CURRENT_VERSION}"


# Replease current release with new release
git grep -l "${CURRENT_VERSION}" ../ | grep -v ../plugin.video.icdrama/index.html | xargs sed -i "s/${CURRENT_VERSION}/${NEW_VERSION}/g"

# Create a new release zip
find plugin.video.icdrama -type f -print | grep -v ".git" | zip -@ ../plugin.video.icdrama/plugin.video.icdrama-${NEW_VERSION}.zip

# Update Release index.html and MD5 hash
pushd ../plugin.video.icdrama/
  ../src/kodidirlist.py > index.html
popd

md5 -q ../addons.xml > ../addons.xml.md5


