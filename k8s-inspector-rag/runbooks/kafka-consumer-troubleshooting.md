# Kafka consumer troubleshooting

**Owner:** Data Platform Engineering  
**Last updated:** 2026-04-01  
**Severity:** P1 if message processing is stopped, P2 if delayed  
**Tags:** kafka, consumer, lag, rebalance, batch, throughput, memory

## 1. Consumer lag diagnosis

Consumer lag is the difference between the latest produced offset and the consumer's committed offset. Lag means messages are being produced faster than consumed.

**Checking consumer lag:**

```bash
# Using kafka-consumer-groups CLI
kafka-consumer-groups.sh --bootstrap-server <broker>:9092 \
  --group <consumer-group> --describe

# Key columns: CURRENT-OFFSET, LOG-END-OFFSET, LAG
# LAG > 0 means the consumer is behind
```

**Lag thresholds:**
- Lag < 100: normal for most workloads
- Lag 100-1000: consumer is slightly behind, monitor
- Lag 1000-10000: consumer is falling behind, investigate throughput
- Lag > 10000: consumer is significantly behind, likely stuck or too slow

**Common causes of increasing lag:**
- Consumer processing is too slow (complex business logic per message)
- Consumer is crash-looping and not consuming during restarts
- Recent increase in producer throughput without matching consumer scaling
- Batch size too large relative to available memory, causing OOM (see section 3)

## 2. Consumer group rebalancing issues

Rebalancing occurs when consumers join or leave a group. During rebalancing, no messages are processed.

**Signs of rebalancing problems:**
- Frequent "Consumer group rebalanced" log messages
- `session.timeout.ms` exceeded — consumer is being kicked out
- Processing time per batch exceeds `max.poll.interval.ms` — Kafka assumes the consumer is dead

**Fix for slow processing causing rebalances:**
- Increase `max.poll.interval.ms` (default 300000ms = 5 min)
- Decrease `max.poll.records` (batch size) so each poll completes faster
- Optimize processing logic to reduce per-record time

## 3. Batch size and memory relationship

**This is the most common cause of Kafka consumer OOM in our environment.**

The Kafka consumer polls records in batches. Each batch is held entirely in memory during processing. The memory formula:

```
memory_per_batch = max.poll.records × average_record_size × processing_overhead_multiplier
```

**Example:**
- `max.poll.records = 500` (batch size)
- Average record size = 2KB
- Processing overhead (deserialization, validation, transformation) = 3x
- Memory per batch = 500 × 2KB × 3 = 3MB per batch

But if the consumer processes batches concurrently or holds references to previous batches:
- 4 partitions × 3MB = 12MB of in-flight batch data
- Plus application heap, libraries, and framework overhead

**The dangerous scenario:**
1. Batch size is increased (e.g., from 100 to 500) for throughput
2. Memory limit stays the same
3. Larger batches consume more heap per poll cycle
4. GC pressure increases — GC pauses get longer
5. Long GC pauses can exceed `session.timeout.ms` → rebalance → restart → more lag
6. Eventually: OOMKilled when heap exhaustion exceeds container limit

**Fix:**
- **Immediate:** Reduce `max.poll.records` back to the previous value
- **Or:** Increase container memory limit proportionally to the batch size increase
- **Rule of thumb:** If batch size doubles, memory limit should increase by 30-50% (not 2x, because batch memory is only part of total usage)
- **Right-sizing formula:** Set container memory limit to at least `(max.poll.records × avg_record_size × 3 × partition_count × 2) + base_heap`. The `×2` provides headroom for GC.

## 4. Consumer performance tuning

**Throughput optimization settings:**

```properties
# Increase batch size for higher throughput (watch memory!)
max.poll.records=500

# Fetch more data per request to reduce network round trips
fetch.min.bytes=1048576
fetch.max.wait.ms=500

# Larger fetch buffer
max.partition.fetch.bytes=1048576
```

**Latency optimization settings (opposite of throughput):**

```properties
# Small batches, process immediately
max.poll.records=10
fetch.min.bytes=1
fetch.max.wait.ms=100
```

**Our standard production settings for order processing:**

```properties
max.poll.records=100
fetch.min.bytes=16384
fetch.max.wait.ms=200
max.poll.interval.ms=300000
session.timeout.ms=45000
heartbeat.interval.ms=15000
```

Note: the default `max.poll.records` for order processing is 100. Increasing beyond this requires proportional memory limit increases and load testing approval.

## 5. Scaling Kafka consumers

Kafka parallelism is bounded by partition count. You cannot have more active consumers in a group than partitions.

**Scaling rules:**
- Current partition count = max consumer instances
- To scale beyond current partitions: request partition increase (irreversible in Kafka)
- When scaling consumers, allow 2 minutes for rebalance to complete
- Monitor lag after scaling — if lag doesn't decrease, the bottleneck is per-partition processing speed, not parallelism

```bash
# Check partition count for a topic
kafka-topics.sh --bootstrap-server <broker>:9092 \
  --topic <topic> --describe

# Scale the consumer deployment
kubectl scale deployment/<consumer-app> -n <namespace> --replicas=<partition_count>
```

**Anti-pattern:** Scaling consumers beyond partition count. Extra consumers will be idle (no partitions assigned), wasting resources.