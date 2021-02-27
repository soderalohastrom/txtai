"""
Annoy module
"""

from annoy import AnnoyIndex

from .base import ANN


class Annoy(ANN):
    """
    Builds an ANN model using the Annoy library.
    """

    def load(self, path):
        # Load index
        self.model = AnnoyIndex(self.config["dimensions"], self.config["metric"])
        self.model.load(path)

    def index(self, embeddings):
        # Inner product is equal to cosine similarity on normalized vectors
        self.config["metric"] = "dot"

        # Create index
        self.model = AnnoyIndex(self.config["dimensions"], self.config["metric"])

        # Add items
        for x in range(embeddings.shape[0]):
            self.model.add_item(x, embeddings[x])

        # Build index
        self.model.build(self.setting("ntrees", 10))

    def search(self, queries, limit):
        # Lookup search k setting
        searchk = self.setting("searchk", -1)

        # Annoy doesn't have a built in batch query method
        results = []
        for query in queries:
            # Run the query
            ids, scores = self.model.get_nns_by_vector(query, n=limit, search_k=searchk, include_distances=True)

            # Map results to [(id, score)]
            results.append(list(zip(ids, scores)))

        return results

    def save(self, path):
        # Write index
        self.model.save(path)
