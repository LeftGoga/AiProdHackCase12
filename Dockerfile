FROM python:3.12

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

RUN export FLASH_ATTENTION_SKIP_CUDA_BUILD=TRUE
RUN pip install flash-attn --no-build-isolation

COPY . .

RUN apt install make

ENTRYPOINT ["make", "run"]
