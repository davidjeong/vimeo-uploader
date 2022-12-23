FROM public.ecr.aws/lambda/python:3.9

COPY requirements.txt  .
RUN pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

COPY app.py ${LAMBDA_TASK_ROOT}
COPY core ${LAMBDA_TASK_ROOT}/core
COPY ffmpeg-5.1.1-amd64-static /tmp/ffmpeg

ENV PATH "${PATH}:/tmp/ffmpeg"
RUN chmod 755 /tmp/ffmpeg

CMD ["app.handler"]
