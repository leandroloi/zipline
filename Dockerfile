#
# Dockerfile for an image with the currently checked out version of zipline installed. To build:
#
#    docker build -t quantopian/zipline .
# 
# To run the container:
#
#    docker run -v=/path/to/your/notebooks:/projects -p 8888:8888/tcp --name zipline -it quantopian/zipline
#
# To access Jupyter when running docker locally (you may need to add NAT rules):
#
#    https://127.0.0.1
#
# default password is jupyter.  to provide another, see:
#    http://jupyter-notebook.readthedocs.org/en/latest/public_server.html#preparing-a-hashed-password
# 
# once generated, you can pass the new value via `docker run --env` the first time
# you start the container.
# 
# You can also run an algo using the docker exec command.  For example:
#
#    docker exec -it zipline run_algo.py -f /projects/my_algo.py --start 2015-1-1 --end 2016-1-1 \
#         --symbols XOP -o /projects/result.pickle
#
# For developers who want to access source inside the zipline container, try running this from 
# within the root of the zipline source tree:
# 
#    docker run -v=/path/to/your/notebooks:/projects -v=`pwd`:/zipline -p 443:8888/tcp \
#         --name zipline -it quantopian/zipline
# 

FROM python:2.7

#
# set up environment
# 
ENV PROJECT_DIR=/projects \
    NOTEBOOK_PORT=8888 \
    SSL_CERT_PEM=/root/.jupyter/jupyter.pem \
    SSL_CERT_KEY=/root/.jupyter/jupyter.key \
    PW_HASH="u'sha1:31cb67870a35:1a2321318481f00b0efdf3d1f71af523d3ffc505'" \
    CONFIG_PATH=/root/.jupyter/jupyter_notebook_config.py

# 
# install TA-Lib and other prerequisites
# 

RUN mkdir ${PROJECT_DIR} \
    && apt-get -y update \
    && apt-get -y install libfreetype6-dev libpng-dev libopenblas-dev liblapack-dev gfortran \
    && curl -L http://downloads.sourceforge.net/project/ta-lib/ta-lib/0.4.0/ta-lib-0.4.0-src.tar.gz | tar xvz 

#
# build and install zipline from source.  install TA-Lib after to ensure
# numpy is available.
# 

WORKDIR /ta-lib

RUN pip install numpy==1.9.2 \
  && pip install scipy==0.15.1 \
  && pip install pandas==0.16.1 \
  && ./configure --prefix=/usr \
  && make \
  && make install \
  && pip install TA-Lib \
  && pip install jupyter

#
# This is then only file we need from source to remain in the
# image after build and install.
#

ADD ./etc/docker_cmd.sh /

# 
# make port available. /zipline is made a volume
# for developer testing.
# 
EXPOSE ${NOTEBOOK_PORT}

#
# build and install the zipline package into the image
#

ADD . /zipline
WORKDIR /zipline
RUN python setup.py install

#
# clean up the build artifacts and recreate the folder for 
# developer mount
#

RUN rm -rf /zipline && mkdir /zipline

#
# start the jupyter server
#

WORKDIR ${PROJECT_DIR}
CMD /docker_cmd.sh
