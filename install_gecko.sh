#!/usr/bin/env bash

for i in "$@"
    do
        case ${i} in
            -a=*|--arch=*)
            ARCH="${i#*=}"
                shift;;
                -p=*|--pass=*)
                SUDO_PASSWORD="${i#*=}"
                shift;;
                -v=*|--version=*)
                VERSION="${i#*=}"
                shift;;
                -d=*|--dir=*)
                DIR="${i#*=}"
                shift;;
            esac
    done

if [[ "${ARCH}" == "" ]]
    then
    echo 'Please specify your architecture'
    exit 1
fi
if [[ "${VERSION}" == "" ]]
    then
    VERSION='0.27.0'
fi
if [[ "${DIR}" == "" ]]
    then
    DIR='/usr/bin'
fi
wget https://github.com/mozilla/geckodriver/releases/download/v${VERSION}/geckodriver-v${VERSION}-linux${ARCH}.tar.gz
tar -xvzf *linux${ARCH}.tar.gz
chmod +x ./geckodriver
if [[ "${SUDO_PASSWORD}" == "" ]]
    then
    sudo cp geckodriver ${DIR}
else
    sudo -S <<< ${SUDO_PASSWORD} cp geckodriver ${DIR}
fi
rm -f ./gecko*
