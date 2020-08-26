#!/usr/bin/env bash
pip install .[sqlite]
pip install uvicorn selenium
cd tests
rm -f python_logo.png
cp test_crax.sqlite test_selenium/test.sqlite

for i in "$@"
    do
        case ${i} in
            -e=*|--executable=*)
            EXECUTABLE="${i#*=}"
                shift;;
                -t=*|--threads=*)
                THREADS="${i#*=}"
                shift;;
                -d=*|--delay=*)
                DELAY="${i#*=}"
                shift;;
            esac
    done

if [[ "${EXECUTABLE}" != "" ]]
    then
    export CRAX_GECKO_EXECUTABLE=${EXECUTABLE}
fi
if [[ "${THREADS}" != "" ]]
    then
    export CRAX_TEST_THREADS=${THREADS}
fi
if [[ "${DELAY}" != "" ]]
    then
    export CRAX_TEST_DELAY=${DELAY}
fi
python -m uvicorn run:app &
cd test_selenium && python thread_tests.py
pip uninstall --yes sqlalchemy databases alembic crax selenium
rm -f test.sqlite
rm -f geckodriver.log
rm -f ../python_logo.png
rm -f ../crax.log
ps aux | grep -v grep | grep uvicorn | awk '{print $2}' | xargs kill -9
