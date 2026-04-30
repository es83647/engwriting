# myBoard/Dockerfile

FROM python:3.11.6

WORKDIR /usr/src/app

COPY requirements.txt .
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

WORKDIR /usr/src/app/board_project

EXPOSE 8000

CMD ["/usr/src/app/entrypoint.sh"]
