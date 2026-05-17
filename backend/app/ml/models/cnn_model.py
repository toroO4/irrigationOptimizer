"""
ML Model — CNN (Convolutional Neural Network).

PyTorch-based 1D CNN for spatial pattern recognition in
soil moisture features. Treats the feature vector as a
1D signal and applies convolutional filters.
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


class CNN1DNetwork(nn.Module if TORCH_AVAILABLE else object):
    """1D Convolutional Neural Network for feature-based prediction."""

    def __init__(self, input_size: int, num_filters: int = 64):
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required for CNN model")
        super().__init__()
        self.conv_layers = nn.Sequential(
            nn.Conv1d(1, num_filters, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.BatchNorm1d(num_filters),
            nn.Conv1d(num_filters, num_filters * 2, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.BatchNorm1d(num_filters * 2),
            nn.AdaptiveAvgPool1d(1),
        )
        self.fc = nn.Sequential(
            nn.Linear(num_filters * 2, 32),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(32, 3), # 3 classes: Low, Medium, High
        )

    def forward(self, x):
        x = x.unsqueeze(1)  # Add channel dimension: (batch, 1, features)
        x = self.conv_layers(x)
        x = x.squeeze(-1)
        return self.fc(x)


class CNNModel:
    """
    1D CNN model for soil moisture prediction.

    Same interface as RandomForestModel for registry compatibility.
    """

    def __init__(self, input_size: int = 17, num_filters: int = 64, learning_rate: float = 0.001, epochs: int = 50, batch_size: int = 32):
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch required. Run: pip install torch")

        self.input_size = input_size
        self.epochs = epochs
        self.batch_size = batch_size
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.network = CNN1DNetwork(input_size, num_filters).to(self.device)
        self.optimizer = torch.optim.Adam(self.network.parameters(), lr=learning_rate)
        self.criterion = nn.CrossEntropyLoss()
        self.is_trained = False
        self.feature_names: List[str] = []
        self.feature_importances: Dict[str, float] = {}
        self.best_params: Dict[str, Any] = {}

        logger.info("CNN model initialized — device=%s", self.device)

    def train(self, X_train: np.ndarray, y_train: np.ndarray, feature_names: Optional[List[str]] = None) -> Dict[str, float]:
        """Train the CNN model."""
        logger.info("Training CNN — samples=%d, features=%d", X_train.shape[0], X_train.shape[1])

        if feature_names:
            self.feature_names = feature_names

        X_tensor = torch.FloatTensor(X_train).to(self.device)
        y_tensor = torch.LongTensor(y_train).to(self.device)
        dataset = TensorDataset(X_tensor, y_tensor)
        dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)

        self.network.train()
        final_loss = 0.0
        for epoch in range(self.epochs):
            epoch_loss = 0.0
            for batch_X, batch_y in dataloader:
                self.optimizer.zero_grad()
                output = self.network(batch_X)
                loss = self.criterion(output, batch_y)
                loss.backward()
                self.optimizer.step()
                epoch_loss += loss.item()
            final_loss = epoch_loss / len(dataloader)
            if (epoch + 1) % 10 == 0:
                logger.info("CNN Epoch %d/%d — Loss: %.6f", epoch + 1, self.epochs, final_loss)

        self.is_trained = True
        logger.info("CNN training complete")
        return {"final_loss": final_loss}

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions."""
        if not self.is_trained:
            raise RuntimeError("Model must be trained first")
        self.network.eval()
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X).to(self.device)
            logits = self.network(X_tensor)
            predictions = torch.argmax(logits, dim=1).cpu().numpy()
        return predictions

    def predict_with_confidence(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        if not self.is_trained:
            raise RuntimeError("Model must be trained first")
        self.network.eval()
        with torch.no_grad():
            X_tensor = torch.FloatTensor(X).to(self.device)
            logits = self.network(X_tensor)
            probs = torch.softmax(logits, dim=1)
            confidence, predictions = torch.max(probs, dim=1)
        return predictions.cpu().numpy(), confidence.cpu().numpy()

    def get_feature_importance(self, top_n: int = 10) -> List[Tuple[str, float]]:
        return []  # CNN doesn't provide direct importance

    def save(self, file_path: Optional[str] = None) -> str:
        if file_path is None:
            model_dir = Path(settings.model_dir)
            model_dir.mkdir(parents=True, exist_ok=True)
            file_path = str(model_dir / "cnn_model.pt")
        torch.save({"model_state": self.network.state_dict(), "feature_names": self.feature_names, "input_size": self.input_size}, file_path)
        logger.info("CNN model saved to: %s", file_path)
        return file_path

    def load(self, file_path: Optional[str] = None) -> None:
        if file_path is None:
            file_path = str(Path(settings.model_dir) / "cnn_model.pt")
        data = torch.load(file_path, map_location=self.device)
        self.network.load_state_dict(data["model_state"])
        self.feature_names = data.get("feature_names", [])
        self.is_trained = True
        logger.info("CNN model loaded from: %s", file_path)
