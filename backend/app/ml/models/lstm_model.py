"""
ML Model — LSTM (Long Short-Term Memory).

PyTorch-based LSTM for time-series soil moisture forecasting.
Takes sequences of feature observations and predicts future moisture.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not installed — LSTMModel will not be available")


class LSTMNetwork(nn.Module if TORCH_AVAILABLE else object):
    """PyTorch LSTM network architecture."""

    def __init__(self, input_size: int, hidden_size: int = 64, num_layers: int = 2, dropout: float = 0.2):
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is required for LSTM model")
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
        )
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(32, 3), # 3 classes: Low, Medium, High
        )

    def forward(self, x):
        """Forward pass through LSTM and fully connected layers."""
        lstm_out, _ = self.lstm(x)
        # Use output from last time step
        last_output = lstm_out[:, -1, :]
        prediction = self.fc(last_output)
        return prediction


class LSTMModel:
    """
    LSTM model for soil moisture time-series prediction.

    Requires sequential data organized into windows of observations.
    """

    def __init__(
        self,
        input_size: int = 17,
        hidden_size: int = 64,
        num_layers: int = 2,
        sequence_length: int = 10,
        learning_rate: float = 0.001,
        epochs: int = 50,
        batch_size: int = 32,
    ):
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch is required. Run: pip install torch")

        self.input_size = input_size
        self.sequence_length = sequence_length
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.batch_size = batch_size

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.network = LSTMNetwork(input_size, hidden_size, num_layers).to(self.device)
        self.optimizer = torch.optim.Adam(self.network.parameters(), lr=learning_rate)
        self.criterion = nn.CrossEntropyLoss()
        self.is_trained = False
        self.feature_names: List[str] = []
        self.feature_importances: Dict[str, float] = {}
        self.best_params: Dict[str, Any] = {}
        self.training_losses: List[float] = []

        logger.info("LSTM model initialized — device=%s, seq_len=%d", self.device, sequence_length)

    def _create_sequences(self, X: np.ndarray, y: np.ndarray) -> Tuple:
        """Create overlapping sequences from flat feature array."""
        sequences, targets = [], []
        for i in range(len(X) - self.sequence_length):
            sequences.append(X[i:i + self.sequence_length])
            targets.append(y[i + self.sequence_length])
        return np.array(sequences), np.array(targets)

    def train(self, X_train: np.ndarray, y_train: np.ndarray, feature_names: Optional[List[str]] = None) -> Dict[str, float]:
        """Train the LSTM model on sequential data."""
        logger.info("Training LSTM — samples=%d, features=%d, epochs=%d", X_train.shape[0], X_train.shape[1], self.epochs)

        if feature_names:
            self.feature_names = feature_names

        # Create sequences
        X_seq, y_seq = self._create_sequences(X_train, y_train)
        if len(X_seq) == 0:
            raise ValueError(f"Not enough data for sequence_length={self.sequence_length}")

        X_tensor = torch.FloatTensor(X_seq).to(self.device)
        y_tensor = torch.LongTensor(y_seq).to(self.device)

        dataset = TensorDataset(X_tensor, y_tensor)
        dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

        self.network.train()
        self.training_losses = []

        for epoch in range(self.epochs):
            epoch_loss = 0.0
            for batch_X, batch_y in dataloader:
                self.optimizer.zero_grad()
                output = self.network(batch_X)
                loss = self.criterion(output, batch_y)
                loss.backward()
                self.optimizer.step()
                epoch_loss += loss.item()

            avg_loss = epoch_loss / len(dataloader)
            self.training_losses.append(avg_loss)

            if (epoch + 1) % 10 == 0:
                logger.info("Epoch %d/%d — Loss: %.6f", epoch + 1, self.epochs, avg_loss)

        self.is_trained = True
        metrics = {"final_loss": self.training_losses[-1]}
        logger.info("LSTM training complete — final_loss=%.6f", metrics["final_loss"])
        return metrics

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions on sequential data."""
        if not self.is_trained:
            raise RuntimeError("Model must be trained before predictions")

        self.network.eval()
        with torch.no_grad():
            if X.ndim == 2:
                # Create a single sequence from the last sequence_length rows
                if len(X) >= self.sequence_length:
                    X = X[-self.sequence_length:].reshape(1, self.sequence_length, -1)
                else:
                    # Pad with zeros if not enough data
                    padded = np.zeros((self.sequence_length, X.shape[1]))
                    padded[-len(X):] = X
                    X = padded.reshape(1, self.sequence_length, -1)

            X_tensor = torch.FloatTensor(X).to(self.device)
            logits = self.network(X_tensor)
            predictions = torch.argmax(logits, dim=1).cpu().numpy()

        return predictions

    def predict_with_confidence(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Predict with confidence."""
        if not self.is_trained:
            raise RuntimeError("Model must be trained before predictions")
            
        self.network.eval()
        with torch.no_grad():
            if X.ndim == 2:
                if len(X) >= self.sequence_length:
                    X = X[-self.sequence_length:].reshape(1, self.sequence_length, -1)
                else:
                    padded = np.zeros((self.sequence_length, X.shape[1]))
                    padded[-len(X):] = X
                    X = padded.reshape(1, self.sequence_length, -1)

            X_tensor = torch.FloatTensor(X).to(self.device)
            logits = self.network(X_tensor)
            probs = torch.softmax(logits, dim=1)
            confidence, predictions = torch.max(probs, dim=1)

        return predictions.cpu().numpy(), confidence.cpu().numpy()

    def get_feature_importance(self, top_n: int = 10) -> List[Tuple[str, float]]:
        """LSTM doesn't provide direct feature importance — returns empty."""
        return []

    def save(self, file_path: Optional[str] = None) -> str:
        """Save model state dict to disk."""
        if file_path is None:
            model_dir = Path(settings.model_dir)
            model_dir.mkdir(parents=True, exist_ok=True)
            file_path = str(model_dir / "lstm_model.pt")
        torch.save({"model_state": self.network.state_dict(), "feature_names": self.feature_names, "input_size": self.input_size, "sequence_length": self.sequence_length}, file_path)
        logger.info("LSTM model saved to: %s", file_path)
        return file_path

    def load(self, file_path: Optional[str] = None) -> None:
        """Load model state dict from disk."""
        if file_path is None:
            file_path = str(Path(settings.model_dir) / "lstm_model.pt")
        data = torch.load(file_path, map_location=self.device)
        self.network.load_state_dict(data["model_state"])
        self.feature_names = data.get("feature_names", [])
        self.is_trained = True
        logger.info("LSTM model loaded from: %s", file_path)
