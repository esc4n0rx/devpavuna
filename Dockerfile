
FROM python:3.8-slim


WORKDIR /


COPY . .


RUN pip install Flask flask_socketio reportlab chardet email-validator


EXPOSE 80


CMD ["python", "app.py"]  
