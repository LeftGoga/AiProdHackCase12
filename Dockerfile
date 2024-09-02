FROM python:3.12

WORKDIR /ai-api

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

RUN apt install make

ENTRYPOINT ["make", "run"]
