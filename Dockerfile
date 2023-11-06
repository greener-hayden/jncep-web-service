FROM python:slim
WORKDIR /app
RUN pip install Flask gunicorn jncep requests
COPY . /app
ENV JNCEP_OUTPUT_DIR /app/downloads
RUN mkdir -p ${JNCEP_OUTPUT_DIR}
EXPOSE 5000
CMD ["gunicorn", "--workers=3", "--bind=0.0.0.0:5000", "app:app"]