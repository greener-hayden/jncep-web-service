FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
ENV JNCEP_OUTPUT_DIR /app/downloads
RUN mkdir -p ${JNCEP_OUTPUT_DIR}
EXPOSE 5000
CMD ["gunicorn", "--workers=3", "--bind=0.0.0.0:5000", "app:app"]
