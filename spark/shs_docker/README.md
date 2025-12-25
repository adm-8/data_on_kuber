# Build history server image
```
docker build --no-cache -t spark-history-s3:3.1.3 .

```

# make config file
```
cat <<EOF > spark-defaults.conf
spark.eventLog.enabled          true
spark.eventLog.dir              s3a://npl-de-kuber-cluster/spark-hs
spark.history.fs.logDirectory   s3a://npl-de-kuber-cluster/spark-hs
spark.history.ui.port           18080
spark.hadoop.fs.s3a.endpoint    https://hb.bizmrg.com
spark.hadoop.fs.s3a.access.key  CHANGE_ME
spark.hadoop.fs.s3a.secret.key  CHANGE_ME
EOF
```

# run Spark History Server in Docker 
```
docker run \
  -p 18080:18080 \
  -v "$(pwd)/spark-defaults.conf:/opt/spark/conf/spark-defaults.conf" \
  spark-history-s3:3.1.3 \
  /opt/spark/bin/spark-class \
  org.apache.spark.deploy.history.HistoryServer

```