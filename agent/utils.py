import json

def extract_json(raw: str, target_key: str):
    data = None

    start_index = raw.find(target_key)
    if start_index == -1:
        return data

    colon_index = raw.find(":", start_index)
    if colon_index == -1:
        return data
    
    potential_json_str = raw[colon_index + 1:].strip()
    
    try:
        decoder = json.JSONDecoder()
        data, end_pos = decoder.raw_decode(potential_json_str)
    except json.JSONDecodeError as e:
        print(f"解析 JSON 失败: {e}")
        return data

    return data

import subprocess
import shlex
from typing import Union, Sequence, Optional

def wrapper(cmd: str, args: Union[str, Sequence[str], None] = None, *, timeout: Optional[float] = None) -> str:
    """
    Run external command and return ALL output as a single string (stdout + stderr merged).

    Usage:
        out = wrapper("ls", "-la")
        out = wrapper("git", ["status", "-sb"])
        out = wrapper("python", "-c \"print('hi')\"")

    Notes:
        - stdout and stderr are merged to keep output order.
        - raises RuntimeError if return code != 0.
    """
    if args is None:
        arg_list = []
    elif isinstance(args, str):
        # Allow user passing a single string like "-la /tmp"
        arg_list = shlex.split(args)
    else:
        arg_list = list(args)

    full_cmd = [cmd, *arg_list]

    try:
        r = subprocess.run(
            full_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # merge stderr into stdout
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError as e:
        raise RuntimeError(f"Command not found: {cmd}") from e
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"Command timed out: {' '.join(full_cmd)}") from e

    output = r.stdout or ""
    if r.returncode != 0:
        # You can remove this if you don't want exceptions on failure
        raise RuntimeError(
            f"Command failed (code={r.returncode}): {' '.join(full_cmd)}\n"
            f"---- output ----\n{output}"
        )

    return output

