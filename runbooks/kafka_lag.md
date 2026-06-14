# 📘 Runbook: Kafka Consumer Lag Spike

## Alert

consumer_lag increasing continuously

## Severity

High → Critical

## Diagnosis

sudo docker exec kafka /opt/kafka/bin/kafka-consumer-groups.sh \
  --describe --group trade-event-consumers \
  --bootstrap-server localhost:9092

ps aux | grep consumer

## Recovery

scale consumers
rebalance group
increase partitions

## Verification

lag decreasing
