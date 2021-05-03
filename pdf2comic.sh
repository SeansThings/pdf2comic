#!/bin/bash

# pdf2cbz.sh 'PDF Directory (optional)' 'Output File Format (optional)'

## Requirements
#  poppler-utils - sudo apt-get install poppler-utils
#  ImageMagick   - sudo apt-get install imagemagick
## Optional
#  Rar & Unrar   - sudo apt-get install rar unrar
#  p7zip         - sudo apt-get install p7zip-full

arcFmt="cbz"
pwd=`pwd`
workingDir="/home/jarvis/.pdf2cbz"
pdfDir="$workingDir/pdf"
pngDir="$workingDir/png"
trimDir="$workingDir/trim"
webpDir="$workingDir/webp"
archDir="$workingDir/comics"
cleanOnExit=true

##### Add option to delete last image somehow

# Check for optional arguments
if [[ $# -gt 0 ]]
then
    # If the custom pdf directory exists, set the pdfDir variable
    if [[ ! -z "$1" ]]
    then
        if [[ -d "$1" ]]
        then
            pdfDir="$1"
        else
            echo "Invalid PDF directory entered. Exiting..."
            exit
        fi
    fi
    # Check for preferred archive format
    if [[ ! -z "$2" ]]
    then
        usrArcFmt=`echo $2 | tr '[:upper:]' '[:lower:]'`
        case "$usrArcFmt" in
            cb7 | 7)
                arcFmt="cb7"
                echo "CB7 format selected."
            ;;
            cbr | r)
                arcFmt="cbr"
                echo "CBR format selected."
            ;;
            cbt | t)
                arcFmt="cbt"
                echo "CBT format selected."
            ;;
            cbz | z)
                arcFmt="cbz"
                echo "CBZ format selected."
            ;;
            *)
                echo "Invalid archive format entered. Defaulting to CBZ."
            ;;
        esac
    fi
fi

# Check for working directory. If not found prompt for location.
if [[ ! -d "$workingDir" ]]
then
    tempVar="$workingDir"
    echo "Working directory not found. Please enter location of working directory:"
    read -p "(e.g. /home/user/.pdf2cbz): " workingDir
    if [[ $workingDir == "" ]]
    then
        workingDir="$tempVar"
    fi
    mkdir -p "$workingDir"
fi

if [[ ! -d "$pdfDir" ]]
then
    mkdir -p "$pdfDir"
fi

# Split PDF into separate PNG's.
if [[ -z $(ls -A "$pdfDir") ]]
then
    echo "No PDF's found. Exiting..."
    exit
else
    for file in "$pdfDir"/*
    do
        pngFN=`echo $(basename "$file" ".pdf")`
        issueName="$pngDir/$pngFN"
        if [[ -z $(ls -A "$issueName" 2> /dev/null) ]]
        then
            echo "Splitting $(basename "$file" .pdf)..."
            mkdir -p "$issueName"
            pdftoppm -png "$file" "$issueName/$pngFN"
            wait $!
        else
            echo "Existing split PNG files for $(basename "$file" .pdf) will be used"
        fi
    done
fi

# Trim PNG files
for dir in "$pngDir"/*
do
    issueSrc="$pngDir/$(basename "$dir")"
    issueDst="$trimDir/$(basename "$dir")"
    if [[ -z $(ls -A "$issueDst" 2> /dev/null) ]]
    then
        mkdir -p "$issueDst"
        for file in "$issueSrc"/*
        do
            # echo $issueDst
            echo "Trimming $(basename "$file" .png)..."
            cp "$issueSrc/$(basename "$file")" "$issueDst/$(basename "$file")"
            mogrify -trim -fuzz 10% "$issueDst/$(basename "$file")"
            wait $!
        done
    else
        echo "Existing trimmed PNG files for $(basename "$dir") will be used"
    fi
done

# Convert trimmed PNG to WEBP
for dir in "$trimDir"/*
do
    issueSrc="$trimDir/$(basename "$dir")"
    issueDst="$webpDir/$(basename "$dir")"
    if [[ -z $(ls -A "$issueDst" 2> /dev/null) ]]
    then
        mkdir -p "$issueDst"
        for file in "$issueSrc"/*
        do
            dirName=$(basename "$file")
            filename=$(basename "$file" .png)
            filenameNS="${filename// /_}"
            echo "Converting $(basename "$file") to WEBP..."
            convert "$file" "$issueDst/$filenameNS.webp"
            wait $!
        done
    else
        echo "Existing WEBP files for $(basename "$dir") will be used"
    fi
done

# Convert WEBP files to chosen archive
for dir in "$trimDir"/*
do
    issueSrc="$webpDir/$(basename "$dir")"
    issueDst="$archDir/$(basename "$dir")"
    filename="$(basename "$dir").$arcFmt"
    # if [[ -z $(ls -A "$issueDst" 2> /dev/null) ]]
    if [[ ! -f "$issueDst/$filename" ]]
    then
        mkdir -p "$issueDst"
        cd "$issueSrc"
        echo "Creating $(basename "$dir").$arcFmt..."        
        case "$arcFmt" in
            cb7)
                7z a -bsp0 -bso0 -t7z "$issueDst/$filename" .
                wait $!
            ;;
            cbr)
                rar a -inul "$issueDst/$filename" .
                wait $!
            ;;
            cbt)
                tar -cf "$issueDst/$filename" .
                wait $!
            ;;
            cbz)
                zip -q -r "$issueDst/$filename" .
                wait $!
            ;;
            *)
                echo "Error. Invalid archive format."
            ;;
        esac
        cd "$pwd"
    else
        upArcFmt=`echo $arcFmt | tr '[:lower:]' '[:upper:]'`
        echo "Existing $upArcFmt file for $(basename "$dir") found"
        echo "Nothing will be done"
    fi
done

# Clean up
if [[ $cleanOnExit == true ]]
then
    echo "Cleaning up..."
    rm -r "$pngDir"
    rm -r "$trimDir"
    rm -r "$webpDir"
fi

echo "All done!"

exit