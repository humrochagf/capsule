FROM python:3.12-alpine

ENV PIP_ROOT_USER_ACTION=ignore
ENV LOG_CONFIG=logger_example.yml

COPY . /capsule

WORKDIR /capsule

RUN pip install --upgrade pip
RUN pip install .

EXPOSE 8000

ENTRYPOINT uvicorn capsule:app --host 0.0.0.0 --workers 3 --proxy-headers --forwarded-allow-ips=* --log-config=$LOG_CONFIG
