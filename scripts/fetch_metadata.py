#!/usr/bin/env python3
import argparse
import json
import re
import sys
import traceback
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Union


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch metadata from configured sources.")
    parser.add_argument("--config", required=True, help="Path to config JSON file.")
    parser.add_argument("--source", required=True, help="Source id in config.")
    parser.add_argument(
        "--param",
        action="append",
        default=[],
        help="Request parameter in key=value format. Repeat for multiple params.",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty print output JSON.")
    return parser.parse_args()


def parse_kv(params: List[str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for item in params:
        if "=" not in item:
            raise ValueError(f"invalid --param: {item}, expected key=value")
        key, value = item.split("=", 1)
        out[key] = value
    return out


def load_config(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_source(conf: Dict[str, Any], source_id: str) -> Dict[str, Any]:
    for source in conf.get("sources", []):
        if source.get("id") == source_id:
            return source
    raise KeyError(f"source not found: {source_id}")


def ensure_required_params(source: Dict[str, Any], params: Dict[str, str]) -> None:
    required = source.get("required_params", [])
    missing = [p for p in required if p not in params]
    if missing:
        raise ValueError(f"missing required params for {source.get('id')}: {', '.join(missing)}")


def http_get(url: str, ua: str, timeout: int) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP error {e.code} for URL: {url}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error for URL: {url}: {e.reason}") from e


def parse_response(raw: str, response_type: str) -> Union[str, Dict[str, Any], List[Any]]:
    if response_type == "json":
        return json.loads(raw)
    return raw


def parse_path_segments(path: str) -> List[Union[str, int]]:
    tokens: List[Union[str, int]] = []
    for chunk in path.split("."):
        if not chunk:
            continue
        m = re.match(r"^([^\[\]]+)(\[\d+\])*$", chunk)
        if not m:
            tokens.append(chunk)
            continue
        key = m.group(1)
        tokens.append(key)
        idx_parts = re.findall(r"\[(\d+)\]", chunk)
        for idx in idx_parts:
            tokens.append(int(idx))
    return tokens


def get_by_path(data: Any, path: str) -> Optional[Any]:
    cur = data
    for token in parse_path_segments(path):
        if isinstance(token, int):
            if not isinstance(cur, list) or token < 0 or token >= len(cur):
                return None
            cur = cur[token]
            continue
        if not isinstance(cur, dict) or token not in cur:
            return None
        cur = cur[token]
    return cur


def metadata_label_value(data: Any, path: str, label: str) -> Optional[Any]:
    arr = get_by_path(data, path)
    if not isinstance(arr, list):
        return None
    for item in arr:
        if not isinstance(item, dict):
            continue
        if str(item.get("label")) == label:
            return item.get("value")
    return None


def extract_regex(text: str, pattern: str, group: int = 1) -> Optional[str]:
    try:
        m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    except re.error as e:
        raise ValueError(f"invalid regex pattern: {pattern}") from e
    if not m:
        return None
    try:
        return m.group(group).strip()
    except IndexError as e:
        raise ValueError(f"regex group {group} not found for pattern: {pattern}") from e


def extract_value(spec: Union[str, Dict[str, Any]], payload: Any) -> Optional[Any]:
    if isinstance(spec, str):
        return get_by_path(payload, spec)

    if not isinstance(spec, dict):
        return None

    from_type = spec.get("from")
    if from_type == "const":
        return spec.get("value")

    if from_type == "regex":
        if not isinstance(payload, str):
            return None
        pattern = spec.get("pattern", "")
        try:
            group = int(spec.get("group", 1))
        except (TypeError, ValueError) as e:
            raise ValueError(f"invalid regex group in mapping spec: {spec}") from e
        return extract_regex(payload, pattern, group=group)

    if from_type == "path":
        return get_by_path(payload, spec.get("path", ""))

    if from_type == "metadata_label":
        return metadata_label_value(payload, spec.get("path", ""), spec.get("label", ""))

    if from_type == "first_non_empty":
        for candidate in spec.get("candidates", []):
            value = extract_value(candidate, payload)
            if value not in (None, "", [], {}):
                return value
        return None

    return None


def run(source: Dict[str, Any], conf: Dict[str, Any], params: Dict[str, str]) -> Dict[str, Any]:
    url_template = source.get("url_template")
    if not isinstance(url_template, str) or not url_template:
        raise ValueError(f"invalid or missing url_template in source config: {source.get('id')}")
    url = url_template.format(**params)
    ua = conf.get("user_agent", "metadata-crawler/1.0")
    try:
        timeout = int(conf.get("timeout_seconds", 30))
    except (TypeError, ValueError) as e:
        raise ValueError(f"invalid timeout_seconds in config: {conf.get('timeout_seconds')}") from e
    raw = http_get(url, ua, timeout)
    payload = parse_response(raw, source.get("response_type", "json"))

    result: Dict[str, Any] = {
        "source_id": source.get("id"),
        "source_name": source.get("name"),
        "source_url": url,
        "params": params,
        "metadata": {},
    }

    mappings = source.get("mappings", {})
    for key, spec in mappings.items():
        result["metadata"][key] = extract_value(spec, payload)

    return result


def main() -> int:
    try:
        args = parse_args()
        conf = load_config(args.config)
        params = parse_kv(args.param)
        source = get_source(conf, args.source)
        ensure_required_params(source, params)
        result = run(source, conf, params)
        if args.pretty:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"[ERROR] {e}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
