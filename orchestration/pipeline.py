from pathlib import Path
import subprocess
import sys

from prefect import flow, task


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_INDEX = PROJECT_ROOT / "data" / "raw" / "metadata_index.csv"
PROCESSED_FILE = PROJECT_ROOT / "data" / "processed" / "chunks.parquet"
VALIDATED_FILE = PROJECT_ROOT / "data" / "validated" / "chunks.parquet"


def run_command(command: list[str]) -> None:
    """Run a project command from the repository root."""
    subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        check=True,
    )


@task(name="Check raw corpus")
def check_raw_data():
    if not RAW_INDEX.exists():
        raise FileNotFoundError(
            f"Raw corpus index not found: {RAW_INDEX}"
        )

    print(f"Raw corpus found: {RAW_INDEX}")


@task(name="Transform corpus", retries=2, retry_delay_seconds=10)
def transform_corpus():
    run_command([
        sys.executable,
        "transformation/transform_corpus.py",
    ])

    if not PROCESSED_FILE.exists():
        raise FileNotFoundError(
            f"Transformation finished but output is missing: {PROCESSED_FILE}"
        )

    print(f"Processed corpus created: {PROCESSED_FILE}")


@task(name="Run quality tests", retries=1, retry_delay_seconds=5)
def run_quality_tests():
    run_command([
        sys.executable,
        "-m",
        "pytest",
        "tests/test_transformation.py",
        "-v",
    ])

    print("All quality tests passed.")


@task(name="Validate corpus", retries=1, retry_delay_seconds=5)
def validate_corpus():
    run_command([
        sys.executable,
        "quality/validate_corpus.py",
    ])

    if not VALIDATED_FILE.exists():
        raise FileNotFoundError(
            f"Quality validation did not create: {VALIDATED_FILE}"
        )

    print(f"Validated corpus created: {VALIDATED_FILE}")


@task(name="Ready for embeddings")
def ready_for_embeddings():
    print("Pipeline completed successfully.")
    print(f"Validated dataset ready for embeddings: {VALIDATED_FILE}")


@flow(name="PipelineForge Data Pipeline")
def pipelineforge_pipeline():
    check_raw_data()

    transform_corpus()

    run_quality_tests()

    validate_corpus()

    ready_for_embeddings()


if __name__ == "__main__":
    pipelineforge_pipeline()