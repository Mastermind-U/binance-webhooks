FROM duffn/python-poetry:3.10-buster

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi
RUN apt-get update -y; apt-get install curl nano -y
COPY app /app
