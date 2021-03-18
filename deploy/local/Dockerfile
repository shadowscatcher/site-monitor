FROM python:3.8-slim

WORKDIR /usr/src/app

COPY Pipfile Pipfile.lock ./
RUN pip install pipenv
RUN pipenv install --system

COPY src/ .
COPY wait-for-it.sh deploy/local/docker-entrypoint.sh ./

RUN chmod +x docker-entrypoint.sh wait-for-it.sh main.py

CMD [ "./docker-entrypoint.sh" ]
