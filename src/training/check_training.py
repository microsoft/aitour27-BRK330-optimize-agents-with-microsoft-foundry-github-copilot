"""P12 end-to-end runner: poll training job, deploy on DeveloperTier when done,
then hand off to `src.evaluation.run_baseline` and report the comparison.

Persists results at each step so a partial completion is recoverable.
"""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "data" / "training" / "training-job.json"

POLL_INTERVAL_S = 30
POLL_TIMEOUT_S  = 60 * 60  # 60 minutes


def _client(endpoint: str) -> AzureOpenAI:
    cred = DefaultAzureCredential()
    tp = get_bearer_token_provider(cred, "https://cognitiveservices.azure.com/.default")
    return AzureOpenAI(
        azure_endpoint=endpoint,
        azure_ad_token_provider=tp,
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-01-preview"),
    )


def wait_for_completion(client, job_id: str) -> dict:
    started = time.time()
    last_status = None
    while time.time() - started < POLL_TIMEOUT_S:
        job = client.fine_tuning.jobs.retrieve(job_id)
        if job.status != last_status:
            print(f"[{int(time.time()-started):>4}s] job status: {job.status}")
            last_status = job.status
        if job.status in ("succeeded", "failed", "cancelled"):
            return {
                "status": job.status,
                "fine_tuned_model": job.fine_tuned_model,
                "trained_tokens": getattr(job, "trained_tokens", None),
                "error": getattr(job, "error", None),
                "finished_at": getattr(job, "finished_at", None),
            }
        time.sleep(POLL_INTERVAL_S)
    raise TimeoutError(f"job {job_id} did not complete within {POLL_TIMEOUT_S}s")


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text())
    endpoint = manifest["endpoint"]
    job_id = manifest["job_id"]
    client = _client(endpoint)

    print(f"Endpoint:  {endpoint}")
    print(f"Job id:    {job_id}")
    print(f"Manifest:  {MANIFEST_PATH.relative_to(REPO_ROOT)}")
    print("Polling every 30 s (60 min budget)…\n")

    outcome = wait_for_completion(client, job_id)
    manifest["final"] = outcome
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))

    print()
    if outcome["status"] != "succeeded":
        print("=" * 66)
        print(f"P12 STOPPED — training did not succeed. status={outcome['status']}")
        print(f"error: {outcome.get('error')}")
        print("=" * 66)
        return 3

    fine_tuned_model = outcome["fine_tuned_model"]
    print("=" * 66)
    print("Training SUCCEEDED")
    print("=" * 66)
    print(f"  fine_tuned_model: {fine_tuned_model}")
    print(f"  trained_tokens:   {outcome.get('trained_tokens')}")
    print()
    print("Next steps (do these outside this runner because they touch az CLI):")
    print()
    print("1. Deploy the student on DeveloperTier (cheapest hosting for evaluation):")
    print()
    print("   az cognitiveservices account deployment create \\")
    print("     -g rg-brk330-concierge -n cog-hqxztqzboq4bq \\")
    print("     --deployment-name contoso-student \\")
    print(f"     --model-name {fine_tuned_model} \\")
    print(f"     --model-version 1 --model-format OpenAI \\")
    print("     --sku-name DeveloperTier --sku-capacity 250")
    print()
    print("2. Run the same 20-prompt eval against the student:")
    print()
    print("   python -m src.evaluation.run_baseline \\")
    print("     --variant student --model contoso-student --parallel 3 \\")
    print("     --project-endpoint https://cog-hqxztqzboq4bq.services.ai.azure.com/api/projects/brk330-concierge-project \\")
    print("     --agent contoso-travel")
    return 0


if __name__ == "__main__":
    sys.exit(main())
