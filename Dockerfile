FROM python:3.6-stretch

RUN pip install polynome==0.0.1b0
EXPOSE 5678/tcp

CMD ["polynome", "server", "--host", "::"]
