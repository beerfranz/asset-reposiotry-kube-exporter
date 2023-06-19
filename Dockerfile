FROM python:3.7.17-alpine3.17

WORKDIR /app

RUN pip install kubernetes

COPY ./src/script.py .

ENV ASSET_REPOSITORY_URL=http://asset-repository-caddy
ENV SOURCE_IDENTIFIER=kube-exporter
ENV LABEL_SELECTOR="asset-repository/export=${SOURCE_IDENTIFIER}"

ENTRYPOINT [ "python", "script.py"  ]
