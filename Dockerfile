FROM python:3.6-slim-stretch as builder

RUN mkdir /src
COPY . /src
WORKDIR /src

RUN python setup.py bdist_wheel
RUN pip install dist/*


FROM python:3.6-slim-stretch

COPY --from=builder /usr/local/lib/python3.6/site-packages /usr/local/lib/python3.6/site-packages
COPY --from=builder /usr/local/bin/tensorcraft /usr/local/bin/tensorcraft
EXPOSE 5678/tcp

CMD ["tensorcraft", "server", "--host", "0.0.0.0"]
