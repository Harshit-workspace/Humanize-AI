
import csv
import re
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from sklearn.model_selection import train_test_split

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)


# ==========================================
# CONFIGURATION
# ==========================================

DATA_PATH = Path(__file__).with_name("training_data.csv")

MINIMUM_WORDS = 30
MINIMUM_SAMPLES = 10


# ==========================================
# AI DETECTOR
# ==========================================

class AIDetector:

    def __init__(self):

        self.model = None

        self.training_count = 0

        self.metrics = {}

        self.classes = ["human", "ai"]


    # ======================================
    # TEXT PREPROCESSING
    # ======================================

    def preprocess_text(self, text):

        if not isinstance(text, str):
            return ""

        # Remove unnecessary whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove leading and trailing spaces
        text = text.strip()

        return text


    # ======================================
    # LOAD TRAINING DATA
    # ======================================

    def load_data(self):

        texts = []
        labels = []

        if not DATA_PATH.exists():

            raise FileNotFoundError(
                f"Training dataset not found: {DATA_PATH}"
            )

        with DATA_PATH.open(
            "r",
            encoding="utf-8-sig",
            newline=""
        ) as file:

            reader = csv.DictReader(file)

            if not reader.fieldnames:

                raise ValueError(
                    "Training CSV is empty or missing headers."
                )

            if not {"text", "label"}.issubset(
                set(reader.fieldnames)
            ):

                raise ValueError(
                    "CSV must contain 'text' and 'label' columns."
                )

            seen = {}

            for row in reader:

                text = self.preprocess_text(
                    row.get("text", "")
                )

                label = row.get(
                    "label", ""
                ).strip().lower()

                if not text:
                    continue

                if label not in ["human", "ai"]:
                    continue

                # Avoid duplicate training examples
                normalized_text = text.casefold()

                if normalized_text in seen:

                    # Exclude conflicting duplicate labels
                    if seen[normalized_text] != label:
                        seen[normalized_text] = None

                    continue

                seen[normalized_text] = label

            # Keep only unambiguous examples
            for text_key, label in seen.items():

                if label is not None:

                    texts.append(text_key)
                    labels.append(label)

        if not texts:

            raise ValueError(
                "No valid training examples found in the CSV."
            )

        return texts, labels


    # ======================================
    # CREATE MACHINE LEARNING MODEL
    # ======================================

    def create_model(self):

        return Pipeline([

            (
                "tfidf",

                TfidfVectorizer(

                    lowercase=True,

                    ngram_range=(1, 2),

                    max_features=30000,

                    sublinear_tf=True,

                    min_df=1,

                    max_df=0.98,

                    strip_accents="unicode",

                    token_pattern=r"(?u)\b\w\w+\b"
                )
            ),

            (
                "classifier",

                LogisticRegression(

                    max_iter=1500,

                    class_weight="balanced",

                    C=1.0,

                    solver="liblinear",

                    random_state=42
                )
            )

        ])


    # ======================================
    # TRAIN MODEL
    # ======================================

    def train(self):

        texts, labels = self.load_data()

        total_samples = len(texts)

        human_count = labels.count("human")

        ai_count = labels.count("ai")

        # Check minimum dataset size
        if total_samples < MINIMUM_SAMPLES:

            raise ValueError(
                f"At least {MINIMUM_SAMPLES} valid examples are required. "
                f"Currently available: {total_samples}."
            )

        # Check both classes
        if human_count == 0 or ai_count == 0:

            raise ValueError(
                "Both human and AI examples are required."
            )

        if min(human_count, ai_count) < 2:

            raise ValueError(
                "At least two examples per class are required."
            )

        # Split data into training and testing
        X_train, X_test, y_train, y_test = train_test_split(

            texts,

            labels,

            test_size=0.33,

            random_state=42,

            stratify=labels
        )

        # Train evaluation model
        evaluation_model = self.create_model()

        evaluation_model.fit(
            X_train,
            y_train
        )

        # Predict unseen test examples
        predictions = evaluation_model.predict(X_test)

        # Calculate confusion matrix
        tn, fp, fn, tp = confusion_matrix(
            y_test,
            predictions,
            labels=["human", "ai"]
        ).ravel()

        # Calculate evaluation metrics
        self.metrics = {

            "accuracy": accuracy_score(
                y_test,
                predictions
            ),

            "precision": precision_score(
                y_test,
                predictions,
                pos_label="ai",
                zero_division=0
            ),

            "recall": recall_score(
                y_test,
                predictions,
                pos_label="ai",
                zero_division=0
            ),

            "f1_score": f1_score(
                y_test,
                predictions,
                pos_label="ai",
                zero_division=0
            ),

            "test_samples": len(y_test),

            "training_samples": len(y_train),

            "true_negative": int(tn),

            "false_positive": int(fp),

            "false_negative": int(fn),

            "true_positive": int(tp),

            "human_samples": human_count,

            "ai_samples": ai_count
        }

        # Display evaluation results
        print("\n")
        print("=" * 45)
        print("         HUMAN TEXT AI DETECTOR")
        print("             MODEL EVALUATION")
        print("=" * 45)

        print("\nDATASET INFORMATION")

        print("Total samples:", total_samples)

        print("Human samples:", human_count)

        print("AI samples:", ai_count)

        print("\nCLASSIFICATION REPORT")

        print(
            classification_report(
                y_test,
                predictions,
                labels=["human", "ai"],
                zero_division=0
            )
        )

        print("PERFORMANCE METRICS")

        print(
            "Accuracy:",
            round(self.metrics["accuracy"] * 100, 2),
            "%"
        )

        print(
            "Precision:",
            round(self.metrics["precision"] * 100, 2),
            "%"
        )

        print(
            "Recall:",
            round(self.metrics["recall"] * 100, 2),
            "%"
        )

        print(
            "F1 Score:",
            round(self.metrics["f1_score"] * 100, 2),
            "%"
        )

        print("\nCONFUSION MATRIX")

        print("True Negative:", tn)

        print("False Positive:", fp)

        print("False Negative:", fn)

        print("True Positive:", tp)

        print("=" * 45)

        # Train final model using all available data
        self.model = self.create_model()

        self.model.fit(
            texts,
            labels
        )

        self.training_count = total_samples

        return self.metrics


    # ======================================
    # PREDICT TEXT
    # ======================================

    def predict(self, text):

        if self.model is None:

            raise RuntimeError(
                "Train the model first."
            )

        text = self.preprocess_text(text)

        if not text:

            raise ValueError(
                "Please enter some text."
            )

        word_count = len(text.split())

        if word_count < MINIMUM_WORDS:

            raise ValueError(
                f"Please enter at least {MINIMUM_WORDS} words. "
                f"Your text contains {word_count} words."
            )

        # Get prediction probabilities
        probabilities = self.model.predict_proba(
            [text]
        )[0]

        # Find AI class probability
        class_index = list(
            self.model.classes_
        ).index("ai")

        ai_probability = float(
            probabilities[class_index]
        )

        # Classification threshold
        if ai_probability >= 0.5:

            prediction = "AI-like patterns"

        else:

            prediction = "Human-like patterns"

        # Preserve existing return format
        return ai_probability, prediction


    # ======================================
    # GET MODEL INFORMATION
    # ======================================

    def get_model_info(self):

        return {

            "model_name": "TF-IDF + Logistic Regression",

            "training_samples": self.training_count,

            "metrics": self.metrics.copy(),

            "model_trained": self.model is not None

        }
