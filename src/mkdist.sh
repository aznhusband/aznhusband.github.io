#!/bin/sh

eval `grep "plugin.video.icdrama" plugin.video.icdrama/addon.xml | awk '{print $3}'`
echo $version

find plugin.video.icdrama -type f -print | grep -v ".git" | zip -@ plugin.video.icdrama-$version.zip
