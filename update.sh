#!/bin/bash
cd /home/matt/tube
mkdir ./data
mkdir ./data1
wget "http://www.tfl.gov.uk/tfl/businessandpartners/syndication/feed.aspx?email=<YOUREMAIL>&feedId=15" -O ./data.zip
unzip -o data.zip
unzip -o LULDLRRiverTramCable.zip -d ./data1
for file in ./data1/*
  do
    if [[ $file != *tfl_1-* ]]
      then
        rm $file
    fi
  done
unzip -o LULDLRRiverTramCable.zip "tfl_25-DLR_-6-y05.xml" -d ./data1
#the schema info makes life hard
#so dump it
for f in ./data1/*.xml
  do
    sed '2 c\
    <TransXChange>\' $f > $f.1
    rm -rf $f
    mv $f.1 $f
  done
rm -rf ./data
mv ./data1 ./data
python reload.py
