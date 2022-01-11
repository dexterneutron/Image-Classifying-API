FROM python:3.9
WORKDIR /usr/src/app
COPY . .
RUN pip install pipenv
RUN pipenv install --system --deploy --ignore-pipfile
CMD ["python", "app.py"]