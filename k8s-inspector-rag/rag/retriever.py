
class RetreiverClient:

    def __init__(self, collection):
        self.collection = collection

    def search(self,query,top_k):

        results =  self.collection.query(
            query_texts=[query],
            n_results=top_k,
        )

        return self._format_results(results)

    def _format_results(self,results):

        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0]

        chunks = []

        for doc, meta, dist in zip(docs, metas, distances):
            header = f"[Source: {meta["source"]} > {meta["section"]} | Relevance: {round(dist)}]"
            chunks.append(f"{header}\n{doc}")
        

        return "\n\n--\n\n".join(chunks)
    

