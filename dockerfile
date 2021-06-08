FROM python:3

WORKDIR usr/src/redditor
COPY . .

RUN pip install -r requirements.txt

CMD ["python", "./Redditor/redditor.py"]