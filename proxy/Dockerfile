FROM nginxinc/nginx-unprivileged:1-alpine
LABEL maintainer="github.com/Ridiealist"

COPY ./default.conf.tpl /etc/nginx/default.conf.tpl
COPY ./uwsgi_params /etc/nginx/uwsgi_params
COPY ./run.sh /run.sh

ENV LISTEN_PORT=8000
ENV APP_HOST=app
ENV APP_PORT=9000

USER root

RUN mkdir -p /vol/static && \
    # setting the permissions on 755 so can read
    chmod 755 /vol/static && \
    # 아래행 permission을 주기 위함. touch create empty file in given location
    touch /etc/nginx/conf.d/default.conf && \
    # nginx user에게 새로 만들어지는 파일 ownership 주기
    chown nginx:nginx /etc/nginx/conf.d/default.conf && \
    chmod +x /run.sh

VOLUME /vol/static

# Docker Image 최종 유저로 설정됨. nginx가 해당 Image user. at least power given.
USER nginx

CMD [ "/run.sh" ]

