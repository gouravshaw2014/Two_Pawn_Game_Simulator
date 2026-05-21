import argparse
import json
from pathlib import Path


def _load_dependencies():
    try:
        import pandas as pd
        from joblib import dump
        from sklearn.compose import ColumnTransformer
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.impute import SimpleImputer
        from sklearn.metrics import accuracy_score, classification_report
        from sklearn.model_selection import train_test_split
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import OneHotEncoder
    except ImportError as exc:
        missing = str(exc)
        raise RuntimeError(
            "Missing ML dependencies. Install with:\n"
            "pip install pandas scikit-learn joblib\n"
            f"Original error: {missing}"
        ) from exc

    return {
        "pd": pd,
        "dump": dump,
        "ColumnTransformer": ColumnTransformer,
        "RandomForestClassifier": RandomForestClassifier,
        "SimpleImputer": SimpleImputer,
        "accuracy_score": accuracy_score,
        "classification_report": classification_report,
        "train_test_split": train_test_split,
        "Pipeline": Pipeline,
        "OneHotEncoder": OneHotEncoder,
    }


def resolve_model_output_path(dataset_path: Path, model_out: Path | None) -> Path:
    if model_out is not None:
        return model_out
    dataset_folder = dataset_path.parent.name
    return Path("ML") / "models" / dataset_folder / "pawn_outcome_model.joblib"


def train_model(
    dataset_path: Path,
    model_out: Path | None,
    test_size: float,
    random_state: int,
    n_estimators: int = 220,
    max_depth: int = 14,
    min_samples_leaf: int = 2,
    n_jobs: int = -1,
    max_train_rows: int | None = None,
) -> None:
    deps = _load_dependencies()
    pd = deps["pd"]

    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    df = pd.read_csv(dataset_path)
    if "p1_wins" not in df.columns:
        raise ValueError("Dataset must include 'p1_wins' column.")

    drop_columns = ["p1_wins"]
    if "iteration" in df.columns:
        drop_columns.append("iteration")

    X = df.drop(columns=drop_columns)
    y = df["p1_wins"].astype(int)

    if max_train_rows is not None and max_train_rows > 0 and len(df) > max_train_rows:
        sampled = df.sample(n=max_train_rows, random_state=random_state)
        X = sampled.drop(columns=drop_columns)
        y = sampled["p1_wins"].astype(int)

    categorical_features = [
        c
        for c in ["grabbing_rule", "ownership_mechanism", "phase", "chosen_action"]
        if c in X.columns
    ]
    numeric_features = [c for c in X.columns if c not in categorical_features]

    numeric_pipeline = deps["Pipeline"](
        steps=[("imputer", deps["SimpleImputer"](strategy="median"))]
    )
    categorical_pipeline = deps["Pipeline"](
        steps=[
            ("imputer", deps["SimpleImputer"](strategy="most_frequent")),
            ("onehot", deps["OneHotEncoder"](handle_unknown="ignore")),
        ]
    )

    preprocessor = deps["ColumnTransformer"](
        transformers=[
            ("num", numeric_pipeline, numeric_features),
            ("cat", categorical_pipeline, categorical_features),
        ]
    )

    model = deps["RandomForestClassifier"](
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
        random_state=random_state,
        n_jobs=n_jobs,
    )

    pipeline = deps["Pipeline"](
        steps=[
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )

    X_train, X_test, y_train, y_test = deps["train_test_split"](
        X,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=y if y.nunique() > 1 else None,
    )

    fallback_used = False
    fit_error = None
    try:
        pipeline.fit(X_train, y_train)
    except Exception as exc:
        fit_error = exc
        text = f"{type(exc).__name__}: {exc}"
        if "ArrayMemoryError" not in text and not isinstance(exc, MemoryError):
            raise

    if fit_error is not None:
        fallback_used = True
        fallback_model = deps["RandomForestClassifier"](
            n_estimators=min(80, max(20, n_estimators // 3)),
            max_depth=10 if max_depth is None else min(max_depth, 10),
            min_samples_leaf=max(4, min_samples_leaf),
            random_state=random_state,
            n_jobs=1,
        )
        pipeline = deps["Pipeline"](
            steps=[
                ("preprocessor", preprocessor),
                ("model", fallback_model),
            ]
        )
        pipeline.fit(X_train, y_train)

    preds = pipeline.predict(X_test)
    accuracy = deps["accuracy_score"](y_test, preds)
    report = deps["classification_report"](y_test, preds)

    resolved_model_out = resolve_model_output_path(dataset_path, model_out)
    resolved_model_out.parent.mkdir(parents=True, exist_ok=True)
    deps["dump"](pipeline, resolved_model_out)

    metadata = {
        "dataset": str(dataset_path),
        "model_path": str(resolved_model_out),
        "rows": int(len(df)),
        "features": list(X.columns),
        "categorical_features": categorical_features,
        "numeric_features": numeric_features,
        "accuracy": float(accuracy),
        "random_state": random_state,
        "test_size": test_size,
        "n_estimators": n_estimators,
        "max_depth": max_depth,
        "min_samples_leaf": min_samples_leaf,
        "n_jobs": n_jobs,
        "max_train_rows": max_train_rows,
        "fallback_used": fallback_used,
    }
    metadata_path = resolved_model_out.with_suffix(".metadata.json")
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    metrics = {
        "accuracy": float(accuracy),
        "classification_report": report,
        "rows": int(len(df)),
        "test_size": test_size,
        "random_state": random_state,
        "dataset": str(dataset_path),
        "model_path": str(resolved_model_out),
    }
    metrics_json_path = resolved_model_out.with_suffix(".metrics.json")
    metrics_json_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    metrics_text_path = resolved_model_out.with_suffix(".metrics.txt")
    metrics_text_path.write_text(
        "Accuracy: " + f"{accuracy:.4f}" + "\n\n" + "Classification report:\n\n" + report,
        encoding="utf-8",
    )

    print(f"Model saved to: {resolved_model_out}")
    print(f"Metadata saved to: {metadata_path}")
    print(f"Metrics saved to: {metrics_json_path}")
    print(f"Metrics text saved to: {metrics_text_path}")
    print(f"Accuracy: {accuracy:.4f}")
    print("Classification report:\n")
    print(report)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train ML model for Two Pawn outcomes.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=Path("ML/datasets/data/states_dataset.csv"),
        help="Path to the generated states dataset CSV.",
    )
    parser.add_argument(
        "--model-out",
        type=Path,
        default=None,
        help="Where to save the trained model. Default: ML/models/<dataset-folder>/pawn_outcome_model.joblib",
    )
    parser.add_argument("--test-size", type=float, default=0.2, help="Test split ratio.")
    parser.add_argument("--random-state", type=int, default=42, help="Random seed/state.")
    parser.add_argument("--n-estimators", type=int, default=220, help="RandomForest n_estimators.")
    parser.add_argument("--max-depth", type=int, default=14, help="RandomForest max_depth.")
    parser.add_argument("--min-samples-leaf", type=int, default=2, help="RandomForest min_samples_leaf.")
    parser.add_argument("--n-jobs", type=int, default=-1, help="RandomForest parallel workers.")
    parser.add_argument("--max-train-rows", type=int, default=None, help="Optional cap on training rows sampled from dataset.")
    return parser


if __name__ == "__main__":
    args = build_arg_parser().parse_args()
    train_model(
        dataset_path=args.dataset,
        model_out=args.model_out,
        test_size=args.test_size,
        random_state=args.random_state,
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        min_samples_leaf=args.min_samples_leaf,
        n_jobs=args.n_jobs,
        max_train_rows=args.max_train_rows,
    )
