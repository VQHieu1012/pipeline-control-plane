                    ┌────────────────────┐
User / UI / Airflow │    REST API        │
───────────────────→│     FastAPI        │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │    Core Library    │
                    │                    │
                    │ schema             │
                    │ planner            │
                    │ type mapping       │
                    │ spec builder       │
                    │ state machine      │
                    └─────────┬──────────┘
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
        ┌─────────────────┐       ┌─────────────────┐
        │ Planner Service │       │   Reconciler    │
        │ PyFlink 2.2.x   │       │ long-running   │
        └─────────────────┘       └────────┬────────┘
                                          │
                       ┌──────────────────┼─────────────────┐
                       ▼                  ▼                 ▼
                 Kafka / Connect    Flink Operator      Schema Registry