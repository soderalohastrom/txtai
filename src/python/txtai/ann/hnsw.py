"""
HNSW module
"""

import numpy as np

# pylint: disable=E0611
from hnswlib import Index

from .base import ANN


class HNSW(ANN):
    """
    Builds an ANN model using the hnswlib library.
    """

    def __init__(self, config):
        # Parent constructor
        super().__init__(config)

        # Track number of successful deletes
        self.deletes = 0

    def load(self, path):
        # Load index
        self.model = Index(dim=self.config["dimensions"], space=self.config["metric"])
        self.model.load_index(path)

    def index(self, embeddings):
        # Inner product is equal to cosine similarity on normalized vectors
        self.config["metric"] = "ip"

        # Lookup index settings
        efconstruction = self.setting("efconstruction", 200)
        m = self.setting("m", 16)
        seed = self.setting("randomseed", 100)

        # Create index
        self.model = Index(dim=self.config["dimensions"], space=self.config["metric"])
        self.model.init_index(max_elements=embeddings.shape[0], ef_construction=efconstruction, M=m, random_seed=seed)

        # Add items
        self.model.add_items(embeddings, np.arange(embeddings.shape[0]))

        # Update id offset
        self.offset = embeddings.shape[0]

    def append(self, embeddings):
        new = embeddings.shape[0]

        # Resize index
        self.model.resize_index(self.offset + new)

        # Append new ids
        self.model.add_items(embeddings, np.arange(self.offset, self.offset + new))

        # Update id offset
        self.offset += new

    def delete(self, ids):
        # Mark elements as deleted to omit from search results
        for uid in ids:
            try:
                self.model.mark_deleted(uid)
                self.deletes += 1
            except RuntimeError:
                # Ignore label not found error
                continue

    def search(self, queries, limit):
        # Set ef query param
        ef = self.setting("efsearch")
        if ef:
            self.model.set_ef(ef)

        # Run the query
        ids, distances = self.model.knn_query(queries, k=limit)

        # Map results to [(id, score)]
        results = []
        for x, distance in enumerate(distances):
            # Convert distances to similarity scores
            scores = [1 - d for d in distance]

            results.append(list(zip(ids[x], scores)))

        return results

    def count(self):
        return self.model.get_current_count() - self.deletes

    def save(self, path):
        # Write index
        self.model.save_index(path)
