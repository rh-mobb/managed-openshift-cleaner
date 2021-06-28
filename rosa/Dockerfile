FROM registry.access.redhat.com/ubi8/python-38
COPY --chown=1001:0 ./rosa-cleaner.py ./rosa-cleaner.py
COPY --chown=1001:0 ./requirements.txt ./requirements.txt

# Install the dependencies
RUN pip install -U "pip>=19.3.1" && \
    pip install -r requirements.txt

# Run the application
CMD ./rosa-cleaner.py