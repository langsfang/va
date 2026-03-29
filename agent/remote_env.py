from __future__ import annotations

import json
import socket
from typing import Any

from gym_sts.spaces.observations import Observation


class RemoteEnvError(RuntimeError):
    pass


class RemoteEnv:
    def __init__(self, host: str, port: int, timeout: float = 30.0):
        self.host = host
        self.port = port
        self.timeout = timeout

    def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        message = (json.dumps(payload) + "\n").encode("utf-8")
        with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
            sock.settimeout(self.timeout)
            sock.sendall(message)

            data = b""
            while not data.endswith(b"\n"):
                chunk = sock.recv(65536)
                if not chunk:
                    break
                data += chunk

        if not data:
            raise RemoteEnvError("No response from remote STS server.")

        response = json.loads(data.decode("utf-8"))
        if not response.get("ok"):
            raise RemoteEnvError(response.get("error", "Unknown remote error."))

        return response

    def reset(
        self,
        *,
        seed: int | None = None,
        character: str | None = None,
        ascension: int | None = None,
        sts_seed: str | None = None,
    ) -> Observation:
        payload: dict[str, Any] = {"op": "reset"}
        if seed is not None:
            payload["seed"] = seed
        if character is not None:
            payload["character"] = character
        if ascension is not None:
            payload["ascension"] = ascension
        if sts_seed is not None:
            payload["sts_seed"] = sts_seed

        response = self._request(payload)
        return Observation(response["state"])

    def _do_action(self, action: str) -> Observation:
        response = self._request({"op": "command", "action": action})
        return Observation(response["state"])
