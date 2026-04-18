#!/bin/bash
set -e

export HADOOP_HOME=/opt/hadoop
export PATH=$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$PATH

# Configuration HDFS
cat > $HADOOP_HOME/etc/hadoop/core-site.xml <<EOF
<configuration>
  <property>
    <name>fs.defaultFS</name>
    <value>hdfs://namenode:8020</value>
  </property>
</configuration>
EOF

cat > $HADOOP_HOME/etc/hadoop/hdfs-site.xml <<EOF
<configuration>
    <property>
      <name>dfs.webhdfs.enabled</name>
      <value>true</value>
    </property>

    <property>
      <name>dfs.replication</name>
      <value>1</value>
    </property>

    <property>
      <name>dfs.namenode.name.dir</name>
      <value>file:///hadoop/dfs/name</value>
    </property>
</configuration>
EOF

# Format si nécessaire
if [ ! -d "//hadoop/dfs/name/current" ]; then
  echo "[NameNode] Format HDFS..."
  hdfs namenode -format -force
fi

# Démarrage
hdfs namenode &

until hdfs dfs -ls / >/dev/null 2>&1; do
  echo "Waiting for HDFS..."
  sleep 2
done

echo "[HDFS] Initialisation..."

hdfs dfs -mkdir -p /data_lake/{raw,processed,curated}
hdfs dfs -mkdir -p /checkpoints/raw
hdfs dfs -chmod -R 777 /data_lake

echo "[HDFS] Ready."
echo "[HDFS] NameNode started"

wait