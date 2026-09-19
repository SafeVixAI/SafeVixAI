# RB-002: Database Failover

**Severity:** P0  
**Last Updated:** 2026-06-16  
**Owner:** Backend Team / SRE  

## Symptoms

- Backend health check fails
- `SELECT 1` probe fails
- CloudWatch alarm `safevixai-rds-connections` triggered
- All API endpoints return 500

## Diagnosis

```bash
# Check RDS status (AWS CLI)
aws rds describe-db-instances \
  --db-instance-identifier safevixai-postgres-db \
  --query 'DBInstances[0].{Status:DBInstanceStatus,MultiAZ:MultiAZ,Endpoint:Endpoint.Address}'

# Check if replica is healthy
aws rds describe-db-instances \
  --db-instance-identifier safevixai-postgres-replica \
  --query 'DBInstances[0].DBInstanceStatus'
```

## Resolution

### Automatic (Multi-AZ)
RDS is configured with Multi-AZ. AWS automatically fails over to the standby in a different AZ. Expected downtime: 60-120 seconds.

### Manual Failover (if Auto fails)
```bash
aws rds reboot-db-instance \
  --db-instance-identifier safevixai-postgres-db \
  --force-failover
```

### Promote Read Replica (if Primary is lost)
```bash
# Step 1: Promote replica to primary
aws rds promote-read-read-replica \
  --db-instance-identifier safevixai-postgres-replica

# Step 2: Update backend to use new primary
kubectl set env deployment/safevixai-backend -n safevixai \
  DATABASE_REPLICA_URL=""  # Old replica is now primary
```

### Recovery Verification
```bash
# Verify database is accepting connections
curl -f http://localhost:8000/health | jq '.dependencies[] | select(.name=="database")'

# Run smoke test
cd load-testing && k6 run k6/smoke.test.js
```

## Prevention
- Multi-AZ deployment (automatic failover)
- Read replica for read-heavy queries
- `deletion_protection = true` prevents accidental deletion
- Automated backups every 30 days
- Cross-region backup replication
- Enhanced Monitoring (15s granularity)
