FROM python:2.7.13
COPY requirements.txt /
RUN pip install -r requirements.txt
ADD . /app
WORKDIR /app
ENTRYPOINT ["python", "start.py"]
