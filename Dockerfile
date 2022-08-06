FROM python:3.9-alpine3.13
LABEL maintainer="github.com/Ridiealist"

ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /tmp/requirements.txt
COPY ./app /app
WORKDIR /app
EXPOSE 8000

    # 가상환경 생성
ARG DEV=true
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apk add --update --no-cache postgresql-client jpeg-dev && \
    apk add --update --no-cache --virtual .tmp-build-deps \
        build-base postgresql-dev musl-dev zlib zlib-dev linux-headers && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    # actual image에서 사용하지 않을 파일은 build process에서 삭제하는 습관!(임시파일 등)
    # TO make Docker image as lightweight as possible
    rm -rf /tmp && \
    apk del .tmp-build-deps && \
    # Image 안에 new user 생성 -> root user로 설정되는것 방지 위함
    # Don't run your app using ROOT USER! 
    ## (해킹시 공격자가 DOCKER container에 대한 full access를 갖는 것의 위험성)
    adduser \
        --disabled-password \
        --no-create-home \
        django-user && \
    mkdir -p /vol/web/media && \
    mkdir -p /vol/web/static && \
    chown -R django-user:django-user /vol && \
    chmod -R 755 /vol

ENV PATH="/py/bin:$PATH"

USER django-user