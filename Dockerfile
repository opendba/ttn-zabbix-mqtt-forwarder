FROM python:3.9

# Setup env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1

RUN pip install pipenv

WORKDIR /usr/src/app

COPY Pipfile .
COPY Pipfile.lock .
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy

RUN useradd -u 20000 -m python
USER python

COPY --chown=python . .

ENV PYTHONPATH=/usr/src/app:/usr/src/app/src

CMD [ "/usr/local/bin/pipenv", "run", "python", "src/ttn-zabbix-mqtt-forwarder.py" ]
