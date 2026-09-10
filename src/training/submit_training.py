"""Submit an SFT fine-tuning job for the Contoso Travel Concierge student model.

Uploads the curated `data/training/sft/train.jsonl` + `validation.jsonl` to the
Azure OpenAI files API, then creates the fine_tuning job. Prints the job id and
STOPS — per spec P11, we do not wait or claim completion.

Usage:
    python -m src.training.submit_training \\
        --model gpt-4.1-mini \\
        --endpoint https://cog-hqxztqzboq4bq.services.ai.azure.com
"""
from __future__ import annotations
import argparse, json, os, sys, time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TRAINING_DIR = REPO_ROOT / "data" / "training"
SFT_DIR = TRAINING_DIR / "sft"


def _client(endpoint: str):
    from openai import AzureOpenAI
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    credential = DefaultAzureCredential()
    token_provider = get_bearer_token_provider(
        credential, "https://cognitiveservices.azure.com/.default"
    )
    return AzureOpenAI(
        azure_endpoint=endpoint,
        azure_ad_token_provider=token_provider,
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-01-preview"),
    )


def _wait_for_file(client, file_id: str, timeout_s: int = 300) -> bool:
    """Poll until the uploaded file's status becomes 'processed' (Azure's precheck)."""
    started = time.time()
    while time.time() - started < timeout_s:
        f = client.files.retrieve(file_id)
        if f.status == "processed":
            return True
        if f.status in ("error", "deleted"):
            print(f"file {file_id} entered terminal state: {f.status}", file=sys.stderr)
            return False
        time.sleep(5)
    return False


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--endpoint", required=True,
                    help="Azure AI account endpoint (e.g. https://cog-…services.ai.azure.com)")
    ap.add_argument("--model", default="gpt-4.1-mini")
    ap.add_argument("--suffix", default="caldova-student-v1",
                    help="Suffix appended to the fine-tuned model name.")
    ap.add_argument("--n-epochs", type=int, default=3)
    ap.add_argument("--train", default=str(SFT_DIR / "train.jsonl"))
    ap.add_argument("--validation", default=str(SFT_DIR / "validation.jsonl"))
    args = ap.parse_args(argv)

    train_p = Path(args.train)
    val_p   = Path(args.validation)
    if not train_p.exists():
        print(f"train file not found: {train_p}", file=sys.stderr); return 2
    if not val_p.exists():
        print(f"validation file not found: {val_p}", file=sys.stderr); return 2

    print(f"Endpoint:          {args.endpoint}")
    print(f"Model:             {args.model}")
    print(f"Suffix:            {args.suffix}")
    print(f"Epochs:            {args.n_epochs}")
    print(f"Train file:        {train_p.relative_to(REPO_ROOT)} "
          f"({sum(1 for _ in train_p.open())} examples)")
    print(f"Validation file:   {val_p.relative_to(REPO_ROOT)} "
          f"({sum(1 for _ in val_p.open())} examples)")

    client = _client(args.endpoint)

    print("\n[1/3] Uploading train file…")
    with train_p.open("rb") as f:
        train_file = client.files.create(file=f, purpose="fine-tune")
    print(f"       file id: {train_file.id}   status: {train_file.status}")

    print("[2/3] Uploading validation file…")
    with val_p.open("rb") as f:
        val_file = client.files.create(file=f, purpose="fine-tune")
    print(f"       file id: {val_file.id}   status: {val_file.status}")

    print("       Waiting for both files to be processed by Azure precheck…")
    if not _wait_for_file(client, train_file.id) or not _wait_for_file(client, val_file.id):
        print("File processing failed. Aborting job creation.", file=sys.stderr)
        return 3

    print("[3/3] Creating fine-tune job…")
    job = client.fine_tuning.jobs.create(
        training_file=train_file.id,
        validation_file=val_file.id,
        model=args.model,
        suffix=args.suffix,
        hyperparameters={"n_epochs": args.n_epochs},
    )

    print()
    print("=" * 66)
    print("P11 — training job submitted")
    print("=" * 66)
    print(f"  job id:     {job.id}")
    print(f"  status:     {job.status}")
    print(f"  base model: {job.model}")
    print(f"  suffix:     {args.suffix}")
    print(f"  train_file: {train_file.id}   validation_file: {val_file.id}")
    print()

    # Persist manifest for future P12 continuation
    manifest = TRAINING_DIR / "training-job.json"
    manifest.write_text(json.dumps({
        "submitted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "endpoint": args.endpoint,
        "model": args.model,
        "suffix": args.suffix,
        "n_epochs": args.n_epochs,
        "job_id": job.id,
        "status": job.status,
        "training_file_id": train_file.id,
        "validation_file_id": val_file.id,
        "train_source": str(train_p.relative_to(REPO_ROOT)),
        "validation_source": str(val_p.relative_to(REPO_ROOT)),
    }, indent=2))
    print(f"  manifest:   {manifest.relative_to(REPO_ROOT)}")
    print()
    print("STOPPED PER SPEC P11 — not waiting for completion.")
    print("Check status later with: python -m src.training.check_training")
    return 0


if __name__ == "__main__":
    sys.exit(main())
