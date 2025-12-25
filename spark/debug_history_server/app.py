from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("test-sum-app")
    .getOrCreate()
)

df = spark.sql("select 1+1 as sum_val")
df.show()

spark.stop()
