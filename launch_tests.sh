#!/usr/bin/env bash
pip install .
cd tests
LOG_FILE='test.log'

function pyTestCrax() {
    pytest --cov=../crax --cov-config=.coveragerc test_files/command_one.py
    pytest --cov=../crax --cov-config=.coveragerc test_files/command_two.py
    python -m pytest --cov=../crax --cov-append --cov-config=.coveragerc test_files/command_three.py
    python -m pytest --cov=../crax --cov-append --cov-config=.coveragerc test_files/command_four.py
    python -m pytest --cov=../crax --cov-append --cov-config=.coveragerc test_files/auth_tests.py
}

function runTests() {
    rm -f ${LOG_FILE}
    touch ${LOG_FILE}
    pyTestCrax | tee ${LOG_FILE}
    ret=$(cat ${LOG_FILE} | grep 'FAILED')
    if [ "$ret" = "" ];
        then
            rm -f ${LOG_FILE}
            echo 'OK'
        else echo ${ret} && exit 1;
    fi
}
pip install sqlalchemy databases alembic asyncpg psycopg2-binary aiomysql pymysql==0.9.2
echo 'SQLite tests started'
export CRAX_TEST_MODE='sqlite'
runTests

export CRAX_TEST_MODE='mysql'
echo 'MySQL tests started'
runTests

export CRAX_TEST_MODE='postgresql'
echo 'PostgreSQL tests started'
runTests

pip uninstall --yes sqlalchemy databases alembic
python -m pytest --cov=../crax --cov-append --cov-config=.coveragerc test_files/common_tests.py
