FROM apache/spark:v3.1.3

ENV HADOOP_VERSION=3.2.0
ENV AWS_SDK_VERSION=1.11.375

ENV SPARK_HOME=/opt/spark
ENV PYSPARK_PYTHON=python3
ENV PYSPARK_DRIVER_PYTHON=python3

USER root

RUN apt-get update \
 && apt-get install -y \
      curl \
      python3 \
      python3-distutils \
      python3-pip \
 && ln -s /usr/bin/python3 /usr/bin/python \
 && rm -rf /var/lib/apt/lists/*

# УСТАНАВЛИВАЕМ PySpark нужной версии
RUN pip3 install --no-cache-dir pyspark==3.1.3

# S3A support
RUN curl -fLo ${SPARK_HOME}/jars/hadoop-aws-${HADOOP_VERSION}.jar \
      https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/${HADOOP_VERSION}/hadoop-aws-${HADOOP_VERSION}.jar && \
    curl -fLo ${SPARK_HOME}/jars/aws-java-sdk-bundle-${AWS_SDK_VERSION}.jar \
      https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/${AWS_SDK_VERSION}/aws-java-sdk-bundle-${AWS_SDK_VERSION}.jar

USER 185
