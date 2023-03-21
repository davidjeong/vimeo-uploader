FROM public.ecr.aws/lambda/python:3.9

COPY requirements.txt  .
RUN pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# This is a temporary workaround until official PyTube release fixes the regex handling
RUN sed -i 's/transform_plan_raw =.*/transform_plan_raw = js/g' pytube/cipher.py

COPY app.py ${LAMBDA_TASK_ROOT}
COPY core ${LAMBDA_TASK_ROOT}/core
COPY ffmpeg-*-amd64-static /usr/local/bin/ffmpeg

ENV PATH "${PATH}:/usr/local/bin/ffmpeg"

CMD ["app.handler"]
