import argparse
import json
from pathlib import Path


def _load_dependencies():
    try:
        import pandas as pd
        from joblib import load
        from sklearn.metrics import accuracy_score, classification_report
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependencies. Install with: pip install pandas scikit-learn joblib"
        ) from exc

    return {
        "pd": pd,
        "load": load,
        "accuracy_score": accuracy_score,
        "classification_report": classification_report,
    }


def compare_models(args):
    deps = _load_dependencies()
    pd = deps["pd"]

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    df = pd.read_csv(dataset_path)
    if "p1_wins" not in df.columns:
        raise ValueError("Dataset must include p1_wins column.")

    drop_columns = ["p1_wins"]
    if "iteration" in df.columns:
        drop_columns.append("iteration")

    X = df.drop(columns=drop_columns)
    y = df["p1_wins"].astype(int)

    summary = {
        "dataset": str(dataset_path),
        "rows": int(len(df)),
        "models": [],
    }

    for model_path_str in args.models:
        model_path = Path(model_path_str)
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")

        model = deps["load"](str(model_path))
        preds = model.predict(X)
        acc = float(deps["accuracy_score"](y, preds))
        report = deps["classification_report"](y, preds)

        summary["models"].append(
            {
                "model_path": str(model_path),
                "accuracy": acc,
                "classification_report": report,
            }
        )

    summary["models"] = sorted(summary["models"], key=lambda item: item["accuracy"], reverse=True)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_json = output_dir / "ml_iteration_comparison.json"
    out_txt = output_dir / "ml_iteration_comparison.txt"

    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [
        "ML Iteration Comparison",
        f"Dataset: {dataset_path}",
        f"Rows: {len(df)}",
        "",
    ]
    for idx, model_stats in enumerate(summary["models"], 1):
        lines.append(f"{idx}. {model_stats['model_path']}")
        lines.append(f"   Accuracy: {model_stats['accuracy']:.4f}")
    out_txt.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Comparison saved to: {out_json}")
    print(f"Summary saved to: {out_txt}")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare ML models (e.g., different iteration-trained models).")
    parser.add_argument("--dataset", type=str, required=True, help="Dataset CSV used for evaluation")
    parser.add_argument("--models", type=str, nargs="+", required=True, help="One or more model paths (.joblib)")
    parser.add_argument("--output-dir", type=str, default="ML/reports", help="Output directory for comparison files")
    return parser


if __name__ == "__main__":
    parser = build_arg_parser()
    args = parser.parse_args()
    compare_models(args)
