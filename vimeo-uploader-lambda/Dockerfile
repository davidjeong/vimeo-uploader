FROM public.ecr.aws/lambda/python:3.12

COPY requirements.txt  .
RUN pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

COPY app.py ${LAMBDA_TASK_ROOT}
COPY core ${LAMBDA_TASK_ROOT}/core
COPY ffmpeg-master-latest-linux64-gpl/bin /usr/local/bin/ffmpeg

ENV PATH "${PATH}:/usr/local/bin/ffmpeg"

CMD ["app.handler"]
