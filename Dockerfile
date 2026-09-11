FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"] 
# cmd is what is executed when the container starts. In this case, it runs the main.py script using Python. starts the whole thing