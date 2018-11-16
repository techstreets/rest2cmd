FROM centos:7.5.1804
MAINTAINER bradojevic@gmail.com

# install common tools
RUN yum install -y epel-release
RUN yum install -y which net-tools curl wget vim git
RUN yum install -y python36

# install pip
RUN curl -fsSL https://bootstrap.pypa.io/get-pip.py | python36 -
RUN pip3 install --upgrade pip

ENV GUNICORN_VERSION 19.9.0
ENV PYTHONDONTWRITEBYTECODE true
ENV APP_ROOT /opt/app
ENV HTTP_MAP_PATH ${APP_ROOT}/http_map.yaml
# Create working dir
RUN mkdir -p ${APP_ROOT}

# install gunicorn
RUN pip install gunicorn==${GUNICORN_VERSION}

# install all project defined dependencies
COPY ./requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt

WORKDIR ${APP_ROOT}
VOLUME ${APP_ROOT}

EXPOSE 8000

CMD /usr/local/bin/gunicorn -w 4 -b 0.0.0.0:8000 app:app
