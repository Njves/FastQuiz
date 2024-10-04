FROM python:3.9-slim

WORKDIR /fastquiz

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN chmod +x boot.sh

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]

RUN chmod +x boot.sh