# PipelineForge — Orchestration

## Role

This module orchestrates the PipelineForge data pipeline using Prefect.

The workflow automates the following steps:

1. Check that the raw PubMed corpus exists.
2. Run the transformation pipeline.
3. Run the automated quality tests.
4. Validate the transformed corpus.
5. Confirm that the validated dataset is ready for embeddings.

## Workflow

```text
data/raw/
   |
   v
Transformation
   |
   v
Pytest quality checks
   |
   v
Quality validation
   |
   v
data/validated/
   |
   v
Ready for Embeddings