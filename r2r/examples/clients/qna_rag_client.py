import asyncio
import glob
import os

import fire

from r2r.client import R2RClient
from r2r.core.utils import generate_id_from_label


class QnARAGClient:
    def __init__(self, base_url="http://localhost:8000", user_id=None):
        self.client = R2RClient(base_url)
        if not user_id:
            self.user_id = generate_id_from_label("user_id")
        self.titles = {
            "lyft_2021.pdf": "Title: Lyft 10k",
            "uber_2021.pdf": "Title: Uber 10k",
            "the_republic.pdf": "Title: The Republic - Plato",
            "meditations.pdf": "Title: Meditations - Aurelius",
        }
        self.history = []

    def ingest(self, document_filter="lyft_2021.pdf"):
        current_file_directory = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(current_file_directory, "..", "data")
        for file_path in glob.glob(os.path.join(data_path, "*.pdf")):
            file_name = file_path.split(os.path.sep)[-1]
            if (
                document_filter.lower() == "all"
                or file_name.lower().startswith(document_filter.lower())
            ):
                if file_name in self.titles:
                    document_id = generate_id_from_label(file_path)
                    metadata = {
                        "user_id": self.user_id,
                        "chunk_prefix": self.titles[file_name],
                    }
                    settings = {}
                    upload_response = self.client.upload_and_process_file(
                        document_id, file_path, metadata, settings
                    )
                    print("Upload response = ", upload_response)

    def search(self, query, search_limit=25, rerank_limit=15):
        search_response = self.client.search(
            query,
            search_limit=search_limit,
            rerank_limit=rerank_limit,
            filters={"user_id": self.user_id},
        )
        for i, response in enumerate(search_response):
            text = response["metadata"]["text"]
            title, body = text.split("\n", 1)
            print(f"Result {i + 1}: {title}")
            print(body[:500])
            print("\n")

    def rag_completion(
        self,
        query,
        model="gpt-4-turbo-preview",
        search_limit=25,
        rerank_limit=15,
    ):
        rag_response = self.client.rag_completion(
            query,
            search_limit=search_limit,
            rerank_limit=rerank_limit,
            filters={"user_id": self.user_id},
            generation_config={"model": model},
        )
        print("rag_response = ", rag_response)

    def rag_completion_streaming(self, query, model="gpt-4-turbo-preview"):
        async def stream_rag_completion():
            async for chunk in self.client.stream_rag_completion(
                query,
                10,
                filters={"user_id": self.user_id},
                generation_config={"stream": True, "model": model},
            ):
                print(chunk, end="", flush=True)

        asyncio.run(stream_rag_completion())

    def delete_document(self, document_path: str):
        document_id = generate_id_from_label(document_path)
        response = self.client.filtered_deletion("document_id", document_id)
        print("Deletion response = ", response)

    def get_logs(self):
        print("Fetching logs after all steps...")
        logs_response = self.client.get_logs()
        print(f"Logs response:\n{logs_response}\n")

    def get_logs_summary(self):
        print("Fetching logs summary after all steps...")
        logs_summary_response = self.client.get_logs_summary()
        print(f"Logs summary response:\n{logs_summary_response}\n")

    def list_user_ids(self):
        user_ids_response = self.client.get_user_ids()
        print("User IDs response = ", user_ids_response)

    def list_user_documents(self):
        if not self.user_id:
            print("User ID is not set. Cannot fetch documents.")
            return
        user_documents_response = self.client.get_user_documents(self.user_id)
        print(f"Documents for user {self.user_id} = ", user_documents_response)


if __name__ == "__main__":
    fire.Fire(QnARAGClient)
