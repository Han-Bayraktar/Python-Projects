import argparse
import os
import sys
import joblib
import pandas as pd
from datetime import datetime

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report, accuracy_score


def load_dataset(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dataset not found: {path}")
    df = pd.read_csv(path, encoding="latin-1")
    if df.shape[1] > 2:
        df = df.iloc[:, :2]
    df.columns = ["label", "text"]
    texts = df["text"].astype(str)
    labels = df["label"].map(lambda x: 1 if str(x).strip().lower() == "spam" else 0)
    return texts, labels


def build_pipeline(algo: str):
    if algo == "lr":
        clf = LogisticRegression(max_iter=1000, class_weight="balanced", n_jobs=None)
    elif algo == "nb":
        clf = MultinomialNB()
    elif algo == "svm":
        clf = LinearSVC(class_weight="balanced")
    else:
        raise ValueError(f"Unknown algorithm: {algo}")

    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2))),
        ("clf", clf),
    ])


def get_param_grid(algo: str):
    common_tfidf = {
        "tfidf__ngram_range": [(1, 1), (1, 2), (1, 3)],
        "tfidf__min_df": [1, 2, 5],
        "tfidf__sublinear_tf": [True, False],
        "tfidf__max_df": [1.0, 0.95, 0.90],
    }

    if algo == "lr":
        grid = {
            **common_tfidf,
            "clf__C": [0.01, 0.1, 1, 10],
            "clf__penalty": ["l2"],
        }
    elif algo == "svm":
        grid = {
            **common_tfidf,
            "clf__C": [0.01, 0.1, 1, 10],
        }
    elif algo == "nb":
        grid = {
            **common_tfidf,
            "clf__alpha": [0.1, 0.5, 1.0, 2.0, 5.0],
            "clf__fit_prior": [True, False],
        }
    else:
        raise ValueError("Parametre grid sadece lr/svm/nb için tanımlı.")
    return grid


def _append_report(save_path: str, text: str):
    """Rapora zaman damgası ile ekle (append)."""
    if not save_path:
        return
    header = f"\n\n==== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ====\n"
    with open(save_path, "a", encoding="utf-8") as f:
        f.write(header)
        f.write(text)


def _format_report(title: str, best_params=None, acc=None, cls_rep=None):
    lines = []
    lines.append(f"{title}")
    if best_params is not None:
        lines.append(f"Best params: {best_params}")
    if acc is not None:
        lines.append(f"Accuracy: {acc:.4f}")
    if cls_rep is not None:
        lines.append("Classification Report:\n" + cls_rep)
    return "\n".join(lines)


def train_and_eval(data_path: str, algo: str, model_path: str = "spam_model.joblib",
                   save_report: str = None, test_size: float = 0.2, random_state: int = 42):
    from datetime import datetime
    texts, labels = load_dataset(data_path)
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=test_size, random_state=random_state, stratify=labels
    )
    pipeline = build_pipeline(algo)
    pipeline.fit(X_train, y_train)
    preds = pipeline.predict(X_test)

    from sklearn.metrics import classification_report, accuracy_score
    accuracy = accuracy_score(y_test, preds)
    report = classification_report(y_test, preds)

    print("Accuracy:", accuracy)
    print(report)

    joblib.dump(pipeline, model_path)
    print(f"Model saved to {model_path}")

    if save_report: 
        with open(save_report, "a", encoding="utf-8") as f:
            f.write(f"\n=== {datetime.now()} ===\n")
            f.write(f"Algorithm: {algo}\n")
            f.write(f"Accuracy: {accuracy}\n")
            f.write(report)
            f.write("\n" + "="*50 + "\n")
        print(f"Classification report saved to {save_report}")



def tune_hyperparams(data_path: str, algo: str, model_path: str = "spam_model_optimized.joblib",
                     save_report: str = None, scoring: str = "f1", cv: int = 5, n_jobs: int = -1,
                     test_size: float = 0.2, random_state: int = 42, verbose: int = 2):
    texts, labels = load_dataset(data_path)
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=test_size, random_state=random_state, stratify=labels
    )

    pipeline = build_pipeline(algo)
    params = get_param_grid(algo)

    grid = GridSearchCV(
        estimator=pipeline,
        param_grid=params,
        cv=cv,
        scoring=scoring,   
        n_jobs=n_jobs,
        verbose=verbose
    )
    grid.fit(X_train, y_train)

    best_model = grid.best_estimator_
    preds = best_model.predict(X_test)

    acc = accuracy_score(y_test, preds)
    cls_rep = classification_report(y_test, preds, target_names=["ham", "spam"])

    out = _format_report(
        title=f"[TUNE] Algo={algo}, BestCV({scoring})={grid.best_score_:.4f}",
        best_params=grid.best_params_,
        acc=acc,
        cls_rep=cls_rep
    )
    print(out)
    _append_report(save_report, out)

    joblib.dump(best_model, model_path)
    print(f"Optimized model saved to {model_path}")


def predict_text(text: str, model_path: str = "spam_model.joblib"):
    if not os.path.exists(model_path):
        print(f"Model not found: {model_path}")
        return 1
    pipeline = joblib.load(model_path)
    pred = pipeline.predict([text])[0]
    label = "spam" if pred == 1 else "ham"
    print(f"Prediction: {label}")
    return 0


def cmd_train(args):
    return train_and_eval(
        data_path=args.data,
        algo=args.algo,
        model_path=getattr(args, "model_path", "spam_model.joblib"),
        save_report=getattr(args, "save_report", "classification_report.txt"),
        test_size=getattr(args, "test_size", 0.2),
        random_state=getattr(args, "random_state", 42)
    )


def cmd_tune(args):
    return tune_hyperparams(
        data_path=args.data,
        algo=args.algo,
        model_path=args.model_path,
        save_report=args.save_report,
        scoring=args.scoring,
        cv=args.cv,
        n_jobs=args.n_jobs,
        test_size=args.test_size,
        random_state=args.random_state,
        verbose=args.verbose
    )


def cmd_predict(args):
    return predict_text(args.text, model_path=args.model_path)


def main():
    parser = argparse.ArgumentParser(description="Simple Spam Detector with optional hyperparameter tuning")
    subparsers = parser.add_subparsers(dest="command")

    train_parser = subparsers.add_parser("train", help="Baseline train & evaluate")
    train_parser.add_argument("--data", required=True, help="Path to dataset CSV file")
    train_parser.add_argument("--algo", required=True, choices=["lr", "nb", "svm"], help="Algorithm to use")
    train_parser.add_argument("--model-path", default="spam_model.joblib", help="Where to save the trained model")
    train_parser.add_argument("--save-report", default=None, help="Append results to a .txt file (e.g. classification_report.txt)")
    train_parser.add_argument("--test-size", type=float, default=0.2, help="Test split size")
    train_parser.add_argument("--random-state", type=int, default=42, help="Random seed")
    train_parser.add_argument("--report", default="classification_report.txt", help="Path to save classification report")
    train_parser.set_defaults(func=cmd_train)

    tune_parser = subparsers.add_parser("tune", help="Hyperparameter tuning with GridSearchCV")
    tune_parser.add_argument("--data", required=True, help="Path to dataset CSV file")
    tune_parser.add_argument("--algo", required=True, choices=["lr", "nb", "svm"], help="Algorithm to tune")
    tune_parser.add_argument("--model-path", default="spam_model_optimized.joblib", help="Where to save the best model")
    tune_parser.add_argument("--save-report", default=None, help="Append results to a .txt file (e.g. classification_report.txt)")
    tune_parser.add_argument("--scoring", default="f1", help="Metric for GridSearchCV scoring (e.g. f1, f1_macro)")
    tune_parser.add_argument("--cv", type=int, default=5, help="Number of CV folds")
    tune_parser.add_argument("--n-jobs", type=int, default=-1, dest="n_jobs", help="Parallel jobs")
    tune_parser.add_argument("--test-size", type=float, default=0.2, help="Test split size")
    tune_parser.add_argument("--random-state", type=int, default=42, help="Random seed")
    tune_parser.add_argument("--verbose", type=int, default=2, help="GridSearchCV verbosity")
    tune_parser.set_defaults(func=cmd_tune)

    predict_parser = subparsers.add_parser("predict", help="Predict a single text")
    predict_parser.add_argument("--text", required=True, help="Text message to classify")
    predict_parser.add_argument("--model-path", default="spam_model.joblib", help="Path to a saved model")
    predict_parser.set_defaults(func=cmd_predict)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
