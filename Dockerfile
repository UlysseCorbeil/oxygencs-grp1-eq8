FROM python:3.8-alpine

ENV PYTHONUNBUFFERED=1

ENV WORK_DIR /usr/bin/src/webapp

WORKDIR ${WORK_DIR}

COPY . ${WORK_DIR}/

RUN pip install pipenv

RUN pipenv install --system --deploy

CMD ["python", "src/main.py"]
