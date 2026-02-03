from typing import List, Dict, Any


class N1ChamadosDB:
    """
    Beta version of the N1 Chamados database service.
    Currently returns dummy data instead of querying the SQL database.
    """

    def __init__(self):
        # Database name: n1_chamados
        self.db_name = "n1_chamados"

        self.demo_data = [
            {
                "id_acrecido": 1,
                "kb_id": "KB0017882",
                "source_id": "78c88ca6-6adb-4b90-ad2e-8c6c2bb8a05a",
                "index_id": "0211f006-78fe-4df2-9b48-9471b0cbf70e",
            },
            {
                "id_acrecido": 2,
                "kb_id": "KB0017882",
                "source_id": "78c88ca6-6adb-4b90-ad2e-8c6c2bb8a05a",
                "index_id": "c3df6a39-0151-4dfa-b49f-53f7bb8e91f8",
            },
            {
                "id_acrecido": 3,
                "kb_id": "KB0034986",
                "source_id": "a7f04be7-d2c2-4de9-8cc8-0e79c2839414",
                "index_id": "0211f006-78fe-4df2-9b48-9471b0cbf70e",
            },
            {
                "id_acrecido": 4,
                "kb_id": "KB0034986",
                "source_id": "c7539b23-a266-4797-ab0c-7018c739c6ce",
                "index_id": "0211f006-78fe-4df2-9b48-9471b0cbf70e",
            },
            {
                "id_acrecido": 5,
                "kb_id": "KB0019150",
                "source_id": "a27dc02f-690e-45fb-90b6-1f1ad4429205",
                "index_id": "0211f006-78fe-4df2-9b48-9471b0cbf70e",
            },
            {
                "id_acrecido": 6,
                "kb_id": "KB0019150",
                "source_id": "542846e4-380a-41b7-b6f9-b190810f2c26",
                "index_id": "0211f006-78fe-4df2-9b48-9471b0cbf70e",
            },
            {
                "id_acrecido": 7,
                "kb_id": "KB0033197",
                "source_id": "4254bd03-024a-4477-a50f-ee7289b9ee1e",
                "index_id": "0211f006-78fe-4df2-9b48-9471b0cbf70e",
            },
            {
                "id_acrecido": 8,
                "kb_id": "KB0033197",
                "source_id": "b2cb9057-b837-470d-bd4e-d3cc55428479",
                "index_id": "0211f006-78fe-4df2-9b48-9471b0cbf70e",
            },
            {
                "id_acrecido": 9,
                "kb_id": "KB0018415",
                "source_id": "4a11c507-9381-4701-bfd2-01844262667a",
                "index_id": "0211f006-78fe-4df2-9b48-9471b0cbf70e",
            },
        ]

    def get_all_data(self) -> List[Dict[str, Any]]:
        """
        Returns all data from the beta version table.
        """
        return self.demo_data

    def get_by_kb_id(self, kb_id: str) -> List[Dict[str, Any]]:
        """
        Filters data by KB ID.
        """
        return [item for item in self.demo_data if item["kb_id"] == kb_id]

    def get_by_source_id(self, source_id: str) -> List[Dict[str, Any]]:
        """
        Filters data by source ID.
        """
        return [item for item in self.demo_data if item["source_id"] == source_id]

    # Placeholder for future SQL implementation
    # def connect(self):
    #     pass

    # def query(self, sql: str):
    #     pass
