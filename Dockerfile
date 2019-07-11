FROM python:3.6-stretch

RUN pip install tensorcraft==0.0.1b1
EXPOSE 5678/tcp

CMD ["tensorcraft", "server", "--host", "0.0.0.0"]
