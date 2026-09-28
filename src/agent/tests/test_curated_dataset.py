from pathlib import Path

from src.training.curated_dataset import prepare


REPO = Path(__file__).resolve().parents[3]


def test_curated_gold_dataset_matches_frozen_contract() -> None:
    train, validation, provenance = prepare(
        REPO / "data/training/curated-gold-v1.jsonl",
        REPO / "data/evaluation/lightweight-v1/dataset-v2.jsonl",
        REPO / "data/training/fine-tuning-scope-v1.json",
        REPO / "src/agent/.agent_configs/baseline/instructions.md",
    )

    assert len(train) == 20
    assert len(validation) == 4
    assert provenance["lever"] == "curated_gold_responses"
    assert provenance["train_count"] == 20
    assert provenance["validation_count"] == 4