#!/usr/bin/env bash
set -e

cd crax_tests && python3 -m venv venv
PYTHON_PATH=$(echo $(pwd)'/venv/bin/python3')
echo -e '\e[32mCRAX VIRTUAL ENVIRONMENT CREATED\032'
${PYTHON_PATH} -m pip install -r requirements.txt
echo -e '\e[32mREQUIREMENTS INSTALLED\032'
${PYTHON_PATH} -m pip install uvicorn
echo -e '\e[32mINSTALLED UVICORN\032'
${PYTHON_PATH} -m pip install .
echo -e '\e[32mINSTALLED CRAX\032'
/etc/init.d/nginx start
bash launch_tests.sh &
cd tests/docker && ${PYTHON_PATH} -m uvicorn streams.app:app --port 5000
