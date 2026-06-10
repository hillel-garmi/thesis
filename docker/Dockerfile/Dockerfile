# Start from the official SageMath image
FROM sagemath/sagemath:latest

# 1. Switch to root to install 'wget'
USER root
RUN apt-get update && apt-get install -y wget

# 2. Switch back to the default 'sage' user 
USER sage

# 3. Download, extract, and dynamically move the files
RUN wget https://mirrors.mit.edu/sage/spkg/upstream/database_jones_numfield/database_jones_numfield-4.tar.gz -O /tmp/jones.tar.gz \
    && SAGE_SHARE=$(sage -c "from sage.env import SAGE_SHARE; print(SAGE_SHARE)") \
    && mkdir -p "$SAGE_SHARE/jones" \
    && mkdir -p /tmp/jones_extract \
    && tar -xzf /tmp/jones.tar.gz -C /tmp/jones_extract \
    && find /tmp/jones_extract -type f -exec mv {} "$SAGE_SHARE/jones/" \; \
    && rm -rf /tmp/jones.tar.gz /tmp/jones_extract