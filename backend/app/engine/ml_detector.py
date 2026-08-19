import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

class SecurityAnomalyDetector:
    def __init__(self, contamination: float = 0.08):
        self.model = IsolationForest(contamination=contamination, random_state=42)

    def extract_features(self, logs: list[dict]) -> pd.DataFrame:
        df = pd.DataFrame(logs)
        df['port_norm'] = df['dest_port'] / 65535.0
        df['bytes_norm'] = np.log1p(df['bytes_out'])
        df['proto_cat'] = df['proto'].astype('category').cat.codes
        return df[['port_norm', 'bytes_norm', 'proto_cat']]

    def fit_predict(self, logs: list[dict]):
        features = self.extract_features(logs)
        self.model.fit(features)
        preds = self.model.predict(features)
        return [logs[i] for i, pred in enumerate(preds) if pred == -1]
