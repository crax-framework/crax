#!/usr/bin/env bash

cd tests
cp -r ../venv .
PYTHON_PATH='venv/bin/python3'
LOG_FILE=$(echo $(pwd)'/docker/test.log')

echo -e '\e[32mTESTS STARTED. OPEN YOUR BROWSER AT 127.0.0.1:5000 TO SEE DETAILS\032'

function pyTestCrax() {
    export CRAX_TEST_MODE='mysql'
    export DOCKER_DATABASE_HOST='mysql-container'
    ${PYTHON_PATH} -m pytest --cov=../crax --cov-config=.coveragerc test_files/auth_tests.py test_files/command_one.py
    ${PYTHON_PATH} -m pytest --cov=../crax --cov-append --cov-config=.coveragerc test_files/command_two.py
    ${PYTHON_PATH} -m pytest --cov=../crax --cov-append --cov-config=.coveragerc test_files/command_three.py
    ${PYTHON_PATH} -m pytest --cov=../crax --cov-append --cov-config=.coveragerc test_files/command_four.py

    export CRAX_TEST_MODE='postgresql'
    export DOCKER_DATABASE_HOST='postgres-container'
    ${PYTHON_PATH} -m pytest --cov=../crax --cov-config=.coveragerc test_files/auth_tests.py test_files/command_one.py
    ${PYTHON_PATH} -m pytest --cov=../crax --cov-append --cov-config=.coveragerc test_files/command_two.py
    ${PYTHON_PATH} -m pytest --cov=../crax --cov-append --cov-config=.coveragerc test_files/command_three.py
    ${PYTHON_PATH} -m pytest --cov=../crax --cov-append --cov-config=.coveragerc test_files/command_four.py

    export CRAX_TEST_MODE='sqlite'
    ${PYTHON_PATH} -m pytest --cov=../crax --cov-config=.coveragerc test_files/auth_tests.py test_files/command_one.py
    ${PYTHON_PATH} -m pytest --cov=../crax --cov-append --cov-config=.coveragerc test_files/command_two.py
    ${PYTHON_PATH} -m pytest --cov=../crax --cov-append --cov-config=.coveragerc test_files/command_three.py
    ${PYTHON_PATH} -m pytest --cov=../crax --cov-append --cov-config=.coveragerc test_files/command_four.py

    ${PYTHON_PATH} -m pip uninstall --yes sqlalchemy databases alembic
    ${PYTHON_PATH} -m pytest --cov=../crax --cov-append --cov-config=.coveragerc test_files/common_tests.py
}

function runTests() {
    rm -f ${LOG_FILE}
    touch ${LOG_FILE}
    pyTestCrax | tee ${LOG_FILE}
}

runTests
echo 'ALL TESTS DONE' >> ${LOG_FILE}
echo -e '\e[32mTESTS FINISHED.\032'
