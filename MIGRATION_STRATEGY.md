# SustainOCPM: Migration Strategy

This document defines the strategy for migrating SustainOCPM from prototype environments to production.

---

## 1. Core Migration Streams

| Migration Stream | Description | Strategy | Rollback Action |
| :--- | :--- | :--- | :--- |
| **Prototype to Production** | Upgrading early schemas, migrating test logs, resetting seed data. | Backup databases, execute schema difference scripts, deploy clean production DB nodes. | Revert system container image to preceding stable build. |
| **Storage Migration** | Transferring local file uploads to scalable multi-tenant S3 buckets. | Batch-upload local files, rewrite metadata pointers in PostgreSQL. | Revert application database pointers to local directory path assets. |
| **Session Persistence** | Transferring cookie/token-based browser state to distributed Redis stores. | Configure Redis cluster caching, implement session token migration middleware. | Revert session management configuration to local memory storage. |
| **Multi-Tenant Separation**| Isolating legacy shared test accounts into independent RLS tenant schemas. | Run data partitioning scripts; apply PostgreSQL RLS policies. | Disable RLS policies temporarily to verify backup integrity. |
| **Knowledge Base Storage** | Migrating vectorized documentation from raw files to pgvector DB. | Parse local documents, batch-calculate embeddings, upload to vector index. | Revert search queries to local static document index. |
| **Audit Log Migration** | Transferring application activity logs to write-once-read-many (WORM) storage. | Export historical activity logs; write to immutable ledger service database. | Keep copy of legacy logs in standard PostgreSQL audit tables. |

---

## 2. Emergency Rollback Protocol
1. **Trigger Condition:** Migration fails, critical schema mismatch alerts arise, or API error rates exceed 5% post-deployment.
2. **Step 1 (Isolate):** Put the ingestion gateway into read-only mode to prevent new data loss.
3. **Step 2 (Restore):** Restore databases from the pre-migration backup (PostgreSQL dump and Neo4j database directory snapshots).
4. **Step 3 (Revert):** Revert the API server containers to the previous version tags.
5. **Step 4 (Validate):** Run the integration test suite to verify tenant data accessibility.
