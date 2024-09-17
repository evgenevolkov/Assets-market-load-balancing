FROM python:3.10-slim

WORKDIR /code

COPY ../requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY prices_analyzer/app /code/app

EXPOSE 8000

CMD ["python", "-m", "app.app"]