#!/bin/sh

eval `grep "plugin.video.icdrama" plugin.video.icdrama/addon.xml | awk '{print $3}'`
echo $version

find plugin.video.icdrama -type f -print | grep -v ".git" | zip -@ plugin.video.icdrama-$version.zip

eval `grep "repository.aznhusband-kodi-repo" repository.aznhusband-kodi-repo/addon.xml | awk '{print $3}'`
find repository.aznhusband-kodi-repo -type f -print | grep -v ".git" | zip -@ repository.aznhusband-kodi-repo-$version.zip
