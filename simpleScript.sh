#!/bin/bash

arrFiles=$(echo $1 | tr ",")
echo $arrFiles
for f in $arrFiles; do
    echo $f
done