FROM public.ecr.aws/lambda/python:3.9

COPY requirements.txt  .
RUN pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

COPY app.py ${LAMBDA_TASK_ROOT}
COPY src/shared/ ${LAMBDA_TASK_ROOT}/src/shared
COPY tests ${LAMBDA_TASK_ROOT}/tests
COPY ffmpeg-5.1.1-arm64-static /usr/local/bin/ffmpeg

ENV PATH "${PATH}:/usr/local/bin/ffmpeg"

CMD ["app.handler"]
