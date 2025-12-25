# TODO: 
- Move s3 paths from hardcode to ENVs

# Set ENVs:
```
export S3_ACCESS_KEY='CHANGE_ME'
export S3_SECRET_KEY='CHANGE_ME'
export S3_API_URL='https://hb.bizmrg.com' 

```

https://hb.bizmrg.com - это VKCloud


# Add the Helm repository
```
helm repo add --force-update spark-operator https://kubeflow.github.io/spark-operator

helm repo update

helm search repo spark-operator/spark-operator --versions

```

# Install SparkOperator
```
helm install spark-operator spark-operator/spark-operator \
    --namespace spark-operator \
    --create-namespace \
    --set webhook.enable=true \
    --version 2.2.1
```

```
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: spark
  namespace: default
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: default
  name: spark-role
rules:
- apiGroups: [""]
  resources: ["*"]
  verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: spark-role-binding
  namespace: default
subjects:
- kind: ServiceAccount
  name: spark
  namespace: default
roleRef:
  kind: Role
  name: spark-role
  apiGroup: rbac.authorization.k8s.io
EOF
```

# Create PVC for external spark-submit runs
```
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: spark-uploads
  namespace: spark-operator
spec:
  accessModes: [ReadWriteMany]
  resources:
    requests:
      storage: 1Gi
EOF
```


# Fix limits:
```
kubectl describe limitrange -n default

Name:       mem-cpu-limit-range
Namespace:  default
Type        Resource  Min  Max  Default Request  Default Limit  Max Limit/Request Ratio
----        --------  ---  ---  ---------------  -------------  -----------------------
Container   cpu       -    -    100m             500m           -
Container   memory    -    -    64Mi             512Mi          -


kubectl edit limitrange  mem-cpu-limit-range -n default
```

# Run Example
```
cat <<'EOF' | kubectl apply -f -
apiVersion: sparkoperator.k8s.io/v1beta2
kind: SparkApplication
metadata:
  name: spark-pi
  namespace: default
spec:
  type: Scala
  mode: cluster
  image: docker.io/library/spark:3.5.5
  imagePullPolicy: IfNotPresent
  mainClass: org.apache.spark.examples.SparkPi
  mainApplicationFile: local:///opt/spark/examples/jars/spark-examples.jar
  sparkVersion: 3.5.5
  arguments:
    - "5000"
  driver:
    cores: 1
    memory: 512m
    serviceAccount: spark-operator-spark
  executor:
    cores: 1
    instances: 1
    memory: 512m
EOF
```

# Check status
```
kubectl get sparkapp

kubectl describe sparkapp spark-pi

kubectl get all 

kubectl logs pod/spark-pi-driver

kubectl delete sparkapp spark-pi
```

# Create NS:
```
kubectl create ns spark-history-server
```

# Create S3-secret CHANGE_VALUES! :
```
kubectl create secret generic s3-secret --from-literal=S3_ACCESS_KEY=$S3_ACCESS_KEY --from-literal=S3_SECRET_KEY=$S3_SECRET_KEY -n spark-history-server
```

# KubedAI Spark History Server:
```
cat <<EOF > ~/spark-history-server-config.yaml
## -----------------------------------------
## Storage backend configuration
## -----------------------------------------

image:
  repository: ghcr.io/kubedai/spark-history-server
  tag: "3.5.5"
  pullPolicy: IfNotPresent

# Tell the chart to use S3
logStore:
  # storage type: "s3" | "abfs" | "local"
  type: s3

  # Amazon S3 specific settings
  s3:
    # The S3 bucket name (without s3a:// prefix)
    bucket: npl-de-kuber-cluster
    # The path within the bucket to store/read event logs
    eventLogsPath: spark-hs
    # Optional: custom endpoint for S3 compatible storage # CHANGE_ME
    endpoint: https://hb.bizmrg.com
    # region is sometimes required by SDKs, but not always; leave blank if not needed
    region: ""

    # If you are NOT using IRSA or instance profile,
    # then omit irsaRoleArn and set access/secretKey values via envVars
    irsaRoleArn: ""

## -----------------------------------------
## Credentials from Kubernetes secret
## -----------------------------------------

# Provide AWS credentials via environment variables from secret
extraEnv:
  - name: AWS_ACCESS_KEY_ID
    valueFrom:
      secretKeyRef:
        name: s3-secret
        key: S3_ACCESS_KEY
  - name: AWS_SECRET_ACCESS_KEY
    valueFrom:
      secretKeyRef:
        name: s3-secret
        key: S3_SECRET_KEY

  # explicitly disable IRSA / WebIdentity
  - name: AWS_WEB_IDENTITY_TOKEN_FILE
    value: ""

  - name: AWS_ROLE_ARN
    value: ""

## -----------------------------------------
## Service configuration
## -----------------------------------------

service:
  # Expose via LoadBalancer (like old chart)
  type: LoadBalancer
  # If needed: override targetPort / port
  port: 80
  targetPort: 18080

## -----------------------------------------
## Optional UI / general settings
## -----------------------------------------

# Replicas of the history server
replicaCount: 1

# (Optional) Set a custom image or tag if desired
image:
  repository: "ghcr.io/kubedai/spark-history-server"
  tag: "latest"
  pullPolicy: IfNotPresent

# SPARK CONFIG:
sparkConf: |-
  spark.hadoop.fs.s3a.impl=org.apache.hadoop.fs.s3a.S3AFileSystem

  # Endpoint & access style
  spark.hadoop.fs.s3a.endpoint=https://hb.bizmrg.com
  spark.hadoop.fs.s3a.path.style.access=true
  spark.hadoop.fs.s3a.connection.ssl.enabled=true

  # REQUIRED for S3-compatible providers
  spark.hadoop.fs.s3a.aws.credentials.provider=org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider
  # TODO: Check maybe can delete keys ? 
  spark.hadoop.fs.s3a.access.key=CHANGE_ME
  spark.hadoop.fs.s3a.secret.key=CHANGE_ME

  # 🔑 CRITICAL fixes
  spark.hadoop.fs.s3a.region=us-east-1
  spark.hadoop.fs.s3a.endpoint.region=us-east-1

  # Disable DNS bucket resolution
  spark.hadoop.fs.s3a.bucket.all.committer.magic.enabled=false

  # Stability
  spark.hadoop.fs.s3a.connection.maximum=100
  spark.hadoop.fs.s3a.attempts.maximum=3


## -----------------------------------------
## Resource limits
## -----------------------------------------

resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 500m
    memory: 6Gi
EOF
```

``` 
## -----------------------------------------
## Logging and other configs
## -----------------------------------------

# Additional Spark configuration that might help S3
sparkConf: |-
  spark.hadoop.fs.s3a.access.key={{ .Values.s3AccessKey }}
  spark.hadoop.fs.s3a.secret.key={{ .Values.s3SecretKey }}
  spark.hadoop.fs.s3a.endpoint https://hb.bizmrg.com
  spark.hadoop.fs.s3a.connection.maximum 100
  spark.hadoop.fs.s3a.path.style.access true

  # FORCE static credentials (THIS FIXES THE CRASH)
  spark.hadoop.fs.s3a.aws.credentials.provider=org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider

  # Optional but recommended
  spark.hadoop.fs.s3a.impl=org.apache.hadoop.fs.s3a.S3AFileSystem
  spark.hadoop.fs.s3a.connection.maximum=100
```


### Add repo
```
helm repo add kubedai https://kubedai.github.io/spark-history-server

helm repo update
```

### Install SHS
```
helm upgrade --install spark-history-server \
  kubedai/spark-history-server \
  -n spark-history-server \
  -f ~/spark-history-server-config.yaml \
  --set s3AccessKey=$(kubectl get secret s3-secret -n spark-history-server -o jsonpath='{.data.S3_ACCESS_KEY}' | base64 -d) \
  --set s3SecretKey=$(kubectl get secret s3-secret -n spark-history-server -o jsonpath='{.data.S3_SECRET_KEY}' | base64 -d)

```

### Debug SHS:
```
kubectl get all -n spark-history-server

kubectl logs pod/spark-history-server-7f697f6cfd-k5qh8  -n spark-history-server

helm uninstall spark-history-server -n spark-history-server
```


# ---------------
# Install spark connect
# ---------------

# Install Java
```
sudo apt update

sudo apt install openjdk-17-jdk -y

java -version

```

# Install spark on ubuntu
```
sudo mkdir -p /opt/spark

cd /opt/spark

wget https://archive.apache.org/dist/spark/spark-3.5.5/spark-3.5.5-bin-hadoop3.tgz

ls -la 

sudo tar -xzvf spark-3.5.5-bin-hadoop3.tgz

cp ~/.bashrc ~/.bashrc.bak

cat << EOF >> ~/.bashrc
# Spark Setup
export SPARK_HOME="/opt/spark/spark-3.5.5-bin-hadoop3"

export PATH=$PATH:$SPARK_HOME/bin

export PYTHONPATH=$SPARK_HOME/python:$SPARK_HOME/python/lib/py4j-0.10.9.7-src.zip:$PYTHONPATH

EOF

source ~/.bashrc

pyspark --version
```

# Create pyspark app file

```
cat << EOF > ~/pyspark_test_app.py
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("spark-submit-test-from-kuber")
    .getOrCreate()
)

df = spark.sql("select 1+1 as sum_val")
df.show()

spark.stop()
EOF
```

# Execute pyspark app on kubernetes ! Change IP and port of kubernetes API server
```
spark-submit \
  --master k8s://https://95.163.211.130:6443 \
  --deploy-mode cluster \
  --name pyspark-app \
  --class org.apache.spark.deploy.PythonRunner \
  --conf spark.executor.instances=1 \
  --conf spark.kubernetes.container.image=apache/spark:3.5.5 \
  --conf spark.kubernetes.authenticate.driver.serviceAccountName=spark \
  --conf spark.kubernetes.file.upload.path='s3a://npl-de-kuber-cluster/spark-uploads' \
  --conf spark.hadoop.fs.s3a.access.key=$S3_ACCESS_KEY \
  --conf spark.hadoop.fs.s3a.secret.key=$S3_SECRET_KEY \
  --conf spark.hadoop.fs.s3a.endpoint=$S3_API_URL \
  --conf spark.eventLog.enabled=true \
  --conf spark.eventLog.dir='s3a://npl-de-kuber-cluster/spark-hs' \
  --conf spark.history.fs.logDirectory='s3a://npl-de-kuber-cluster/spark-hs' \
  --conf spark.history.ui.port=18080 \
  --packages org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262 \
  --conf spark.jars.ivy=/tmp/.ivy2 \
  ~/pyspark_test_app.py

```
