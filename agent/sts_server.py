from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
THIRD = ROOT / "3rd" / "gym-sts"
sys.path.insert(0, str(THIRD))

import argparse
import json
import socketserver
import traceback

from gym_sts.envs.base import SlayTheSpireGymEnv


class StsServer(socketserver.TCPServer):
    allow_reuse_address = True

    def __init__(self, server_address, handler_class, env):
        super().__init__(server_address, handler_class)
        self.env = env


class StsRequestHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        raw = self.rfile.readline()
        if not raw:
            return

        try:
            payload = json.loads(raw.decode("utf-8"))
            response = self._dispatch(payload)
        except Exception as exc:
            response = {
                "ok": False,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }

        self.wfile.write((json.dumps(response) + "\n").encode("utf-8"))

    def _dispatch(self, payload: dict) -> dict:
        op = payload.get("op")
        if op == "reset":
            return self._handle_reset(payload)
        if op == "command":
            return self._handle_command(payload)
        raise ValueError(f"Unsupported op: {op}")

    def _handle_reset(self, payload: dict) -> dict:
        env = self.server.env

        character = payload.get("character")
        if character is not None:
            env.character = character

        ascension = payload.get("ascension")
        if ascension is not None:
            env.ascension = ascension

        options = {}
        sts_seed = payload.get("sts_seed")
        if sts_seed is not None:
            options["sts_seed"] = sts_seed

        _, info = env.reset(seed=payload.get("seed"), options=options)
        obs = info["observation"]
        return {"ok": True, "state": obs.state}

    def _handle_command(self, payload: dict) -> dict:
        action = payload.get("action")
        if not action:
            raise ValueError("Missing action.")

        obs = self.server.env._do_action(action)
        if obs is None:
            raise RuntimeError(f"Remote action failed: {action}")
        return {"ok": True, "state": obs.state}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("lib_dir")
    parser.add_argument("mods_dir")
    parser.add_argument("out_dir")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--character", default="IRONCLAD")
    parser.add_argument("--ascension", type=int, default=20)
    parser.add_argument("--sts-seed", default="0")
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()

    env = SlayTheSpireGymEnv(
        args.lib_dir,
        args.mods_dir,
        args.out_dir,
        headless=args.headless,
        character=args.character,
        ascension=args.ascension,
        sts_seed=args.sts_seed,
        communication_timeout=args.timeout,
    )

    with StsServer((args.host, args.port), StsRequestHandler, env) as server:
        print(f"STS server listening on {args.host}:{args.port}")
        server.serve_forever()


if __name__ == "__main__":
    main()
