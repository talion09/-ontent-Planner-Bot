FROM python:3.10

RUN apt-get update && apt-get install -y postgresql-client

RUN mkdir /HarvesterBot

WORKDIR /HarvesterBot

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN chmod a+x docker/*.sh