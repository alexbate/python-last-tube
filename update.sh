#!/bin/bash
mkdir ./data
mkdir ./data1
wget "http://data.tfl.gov.uk/tfl/syndication/feeds/journey-planner-timetables.zip?<API-KEY>" -O ./data.zip
unzip -o data.zip
unzip -o LULDLRTramRiverCable.zip -d ./data1
for file in ./data1/*
  do
    if [[ $file != *tfl_1-* ]]
      then
        rm $file
    fi
  done
unzip -o LULDLRTramRiverCable.zip "tfl_25-DLR_-77-y05.xml" -d ./data1
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
