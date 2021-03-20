FROM python:3.9

ENV PORT 5001

COPY ./requirements.txt /app/requirements.txt

COPY ./ads.py /app/ads.py

WORKDIR /app

RUN pip install -r requirements.txt

ENTRYPOINT [ "python" ]
CMD [ "ads.py" ]