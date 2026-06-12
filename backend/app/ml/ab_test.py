import hashlib
import random

class ABTest:
    def __init__(self, champion_model, challenger_model, traffic_split=0.1):
        self.champion = champion_model
        self.challenger = challenger_model
        self.traffic_split = traffic_split
        self.results = {"champion": [], "challenger": []}

    def predict(self, features, customer_id):
        # Deterministic split based on customer_id
        hash_val = int(hashlib.md5(str(customer_id).encode()).hexdigest(), 16)
        use_challenger = (hash_val % 100) < (self.traffic_split * 100)

        if use_challenger and self.challenger:
            model = self.challenger
            version = "challenger"
        else:
            model = self.champion
            version = "champion"

        pred = model.predict(features)
        pred["ab_version"] = version
        return pred

    def log_outcome(self, customer_id, actual, predicted, version):
        self.results[version].append({"customer_id": customer_id, "actual": actual, "predicted": predicted})

    def evaluate(self):
        # Basic comparison of conversion rates
        report = {}
        for ver, logs in self.results.items():
            if logs:
                conv = sum(1 for l in logs if l['actual'] == 1) / len(logs)
                report[ver] = {"conversion_rate": conv, "sample_size": len(logs)}
        return report
