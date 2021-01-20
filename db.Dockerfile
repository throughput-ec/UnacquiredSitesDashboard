# Docker file for Unaquired Sites ML Predictions
# Socorro Dominguez, August, 2020
# Last updated: January, 2021

# use python:3 as the base image
FROM python:3

# install dependencies
RUN pip3 install pandas
RUN apt-get update && \
    pip3 install matplotlib && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install argparse

RUN pip3 install plotly
RUN pip3 install dash


RUN pip3 install dash_html_components
RUN pip3 install dash_core_components
RUN pip3 install dash_table
RUN pip3 install dash
RUN pip3 install dash_extensions

WORKDIR /app
COPY src/ /app/src/
COPY input/ /app/input/
COPY output/ /app/output/

RUN ls -alp /app

CMD ["python3", "/app/src/record_mining_dashboard.py", "--input_file=/app/input/sentences", "--output_file=/app/output"]

# how to build the docker image
# docker build . -f db.Dockerfile -t sedv8808/unacquired_sites_db_app

# how to run image locally
# docker run -v <User's Path>/sentences.tsv:/app/input/ -v <User's Path>/output/:/app/output -p 8050:8050 sedv8808/unacquired_sites_db_app

# Example
# docker run -v /Users/seiryu8808/Desktop/UWinsc/UnacquiredSitesDashboard/input/predictions_train_dummy.tsv:/app/input/sentences -v /Users/seiryu8808/Desktop/UWinsc/UnacquiredSitesDashboard/output/:/app/output -p 8050:8050 sedv8808/unacquired_sites_db_app:latest

# troubleshooting useful command
# docker run -it sedv8808/unacquired_sites_db_app:latest bash
