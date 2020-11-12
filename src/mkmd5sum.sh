#!/bin/sh

md5sum addons.xml | awk '{printf("%s", $1)}' > addons.xml.md5
