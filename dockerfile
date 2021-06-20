FROM python:3

WORKDIR usr/src/crumlbyredditor
COPY . .

RUN pip install -r requirements.txt

CMD ["python", "./CrumblyRedditor/bot.py"]