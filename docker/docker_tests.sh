#!/usr/bin/env bash
DIRS=$(ls ..)

find .. -name '__pycache__' | xargs rm -rf
mkdir -p app/crax_tests/

for d in ${DIRS}
    do
        if [[ $d == *"docker"* ]] || [[ $d == *"venv"* ]]
            then
                echo "Skipping $d"
            else
                echo "Collecting $d"
                cp -r ../"$d" app/crax_tests/
        fi
    done

cp ../requirements.txt app/crax_tests/requirements.txt
cp ../requirements.txt app/crax_tests/tests/requirements.txt
cp ../tests/test_files/test_postgresql.sql app/pg_init.sql
perl -pi -e 's/OWNER TO postgres/OWNER TO crax/;' app/pg_init.sql
cp ../tests/test_files/test_mysql.sql app/test_mysql.sql

docker-compose down --remove-orphans
docker network create crax_net
docker-compose up --build -d
docker-compose logs -f