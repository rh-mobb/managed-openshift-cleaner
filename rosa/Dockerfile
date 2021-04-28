FROM registry.access.redhat.com/ubi8/python-38
ADD --chown=1001:0 . .

# Install the dependencies
RUN pip install -U "pip>=19.3.1" && \
    pip install -r requirements.txt

# Run the application
CMD ./rosa-list-clusters.py