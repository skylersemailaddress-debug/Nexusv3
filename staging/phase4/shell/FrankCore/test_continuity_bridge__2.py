from app.routes import messages as messages_module
from app.services import state_builder as state_builder_module


class FakeCursor:
    def __init__(self):
        self.results = []
        self.fetchone_result = None
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append((" ".join(sql.split()), params))
        normalized = " ".join(sql.split()).lower()
        if "select coalesce(max(sequence_no), 0) + 1 as next_sequence_no from messages" in normalized:
            self.fetchone_result = {"next_sequence_no": 4}
        elif "returning id, project_id, role, content, content_text, content_structured, meta, sequence_no, created_at" in normalized:
            self.fetchone_result = {
                "id": 99,
                "project_id": "default",
                "role": "user",
                "content": "hello",
                "content_text": "hello",
                "content_structured": {"text": "hello"},
                "meta": {"external_id": "msg_test"},
                "sequence_no": 4,
                "created_at": "2026-04-01T00:00:00Z",
            }
        else:
            self.fetchone_result = None
            self.results = []

    def fetchone(self):
        return self.fetchone_result

    def fetchall(self):
        return self.results

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeConn:
    def __init__(self, cursor):
        self._cursor = cursor
        self.commits = 0

    def cursor(self):
        return self._cursor

    def commit(self):
        self.commits += 1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_append_message_uses_database(monkeypatch):
    cursor = FakeCursor()
    conn = FakeConn(cursor)
    monkeypatch.setattr(messages_module, "get_conn", lambda: conn)

    result = messages_module.append_message(
        messages_module.AppendMessageRequest(project_id="default", role="user", content="hello", meta={"source": "test"})
    )

    assert result["ok"] is True
    assert result["message"]["project_id"] == "default"
    assert result["message"]["sequence_no"] == 4
    sql_text = "\n".join(call[0] for call in cursor.calls)
    assert "insert into messages" in sql_text.lower()
    assert conn.commits == 1


def test_state_builder_no_filesystem_reads():
    source = state_builder_module.__file__
    text = open(source, "r", encoding="utf-8").read()
    assert "MESSAGES_PATH" not in text
    assert "_load_json" not in text
    assert "from app.core.state_paths" not in text
