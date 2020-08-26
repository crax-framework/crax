FROM debian:buster

RUN apt update
COPY app/crax_tests /crax_tests
COPY app/launch_crax.sh /crax_tests/launch_crax.sh
COPY app/launch_tests.sh /crax_tests/launch_tests.sh
RUN apt install -y --no-install-recommends apt-utils nginx make gcc python3-dev python3-venv

ENV nginx_vhost /etc/nginx/sites-available/default
ENV nginx_conf /etc/nginx/nginx.conf
COPY app/default ${nginx_vhost}


VOLUME ["/etc/nginx/sites-enabled", "/etc/nginx/certs", "/etc/nginx/conf.d", "/var/log/nginx"]

CMD ["./crax_tests/launch_crax.sh"]
EXPOSE 80 443
