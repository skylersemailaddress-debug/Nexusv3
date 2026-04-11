from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from psycopg.types.json import Json

from app.core.state_paths import REPO_ROOT, ensure_state_root


CONNECTOR_ROOT = REPO_ROOT / "state" / "connectors"


@dataclass
class ConnectorWriteResult:
    connector_id: str
    document_id: str
    path: str
    payload: dict[str, Any]


class ConnectorInterface:
    connector_id = "base"

    def write(self, project_id: str, title: str, payload: dict[str, Any]) -> ConnectorWriteResult:
        raise NotImplementedError

    def read(self, project_id: str, document_id: str) -> dict[str, Any]:
        raise NotImplementedError


class MockGoogleDriveConnector(ConnectorInterface):
    connector_id = "mock-google-drive"

    def _root(self, project_id: str) -> Path:
        ensure_state_root()
        root = CONNECTOR_ROOT / "mock_google_drive" / project_id
        root.mkdir(parents=True, exist_ok=True)
        return root

    def write(self, project_id: str, title: str, payload: dict[str, Any]) -> ConnectorWriteResult:
        document_id = f"mockdoc_{uuid4().hex[:16]}"
        path = self._root(project_id) / f"{document_id}.json"
        body = {
            "connector_id": self.connector_id,
            "project_id": project_id,
            "document_id": document_id,
            "title": title,
            "payload": payload,
        }
        path.write_text(json.dumps(body, indent=2), encoding="utf-8")
        try:
            relative_path = str(path.relative_to(REPO_ROOT)).replace("\\", "/")
        except ValueError:
            relative_path = str(path)
        return ConnectorWriteResult(
            connector_id=self.connector_id,
            document_id=document_id,
            path=relative_path,
            payload=body,
        )

    def read(self, project_id: str, document_id: str) -> dict[str, Any]:
        path = self._root(project_id) / f"{document_id}.json"
        return json.loads(path.read_text(encoding="utf-8"))


def get_connector(connector_id: str) -> ConnectorInterface:
    if connector_id == "mock-google-drive":
        return MockGoogleDriveConnector()
    raise ValueError(f"Unsupported connector: {connector_id}")


def write_artifact_via_connector(
    cur,
    project_id: str,
    connector_id: str,
    title: str,
    payload: dict[str, Any],
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    connector = get_connector(connector_id)
    result = connector.write(project_id, title, payload)
    artifact_id = f"connector_{uuid4().hex[:16]}"
    connector_payload = {
        "connector_id": result.connector_id,
        "document_id": result.document_id,
        "path": result.path,
        "content": result.payload,
    }
    cur.execute(
        """
        insert into artifacts (id, project_id, kind, title, path, payload, meta)
        values (%s, %s, 'connector_sync', %s, %s, %s, %s)
        returning *
        """,
        (
            artifact_id,
            project_id,
            title,
            result.path,
            Json(connector_payload),
            Json({"connector_id": connector_id, **(meta or {})}),
        ),
    )
    return cur.fetchone()


def read_artifact_via_connector(project_id: str, connector_id: str, document_id: str) -> dict[str, Any]:
    connector = get_connector(connector_id)
    return connector.read(project_id, document_id)
