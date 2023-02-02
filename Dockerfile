FROM public.ecr.aws/lambda/python:3.9
RUN yum -y install krb5-server krb5-libs && yum clean all
RUN  pip3 install arcgis==2.1.0 --target "${LAMBDA_TASK_ROOT}"
COPY app.py ${LAMBDA_TASK_ROOT}
CMD [ "app.handler" ]