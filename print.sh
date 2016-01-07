#!/bin/bash

INFILE=$1

if [ ! -f $INFILE ]; then
    echo "File $INFILE does not exist"
    exit 1
fi

FILENAME="$(date +%s)_$INFILE"
mv $INFILE $PRINTBOT_DIR/$FILENAME
cp $PRINTBOT_DIR/$FILENAME $PRINTBOT_DIR/$FILENAME.updated
FILEPATH=$PRINTBOT_DIR/$FILENAME.updated

# Turn fan on 
echo "M106" >> $FILEPATH
# Go to home position
echo "G0 F10740 X200.0 Y200.0 Z120.0" >> $FILEPATH
# Turn fan off
echo "M107" >> $FILEPATH
# Show a message
echo "M117 PrintBot is done!" >> $FILEPATH

printcore /dev/ttyUSB0 $FILEPATH

export DISPLAY=:0.0; zenity --info --text="Printing of $INFILE has finished.\nClick OK once you clean up the 3D printer!"
