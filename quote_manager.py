#!/usr/bin/env python3
"""JSONL形式の名言集を管理するCUIアプリケーション。"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any, Iterable


DEFAULT_DATA_FILE = Path(__file__).parent / "data" / "quotes.jsonl"
REQUIRED_FIELDS = {"id", "type", "text", "author", "tag"}


class QuoteStoreError(Exception):
    """データファイルを処理できない場合の例外。"""


class QuoteStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []

        records: list[dict[str, Any]] = []
        try:
            with self.path.open("r", encoding="utf-8") as file:
                for line_number, line in enumerate(file, start=1):
                    if not line.strip():
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise QuoteStoreError(
                            f"{self.path} の {line_number} 行目が不正なJSONです: {exc.msg}"
                        ) from exc
                    self._validate_record(record, line_number)
                    records.append(record)
        except OSError as exc:
            raise QuoteStoreError(f"データファイルを読み込めません: {exc}") from exc
        return records

    def add(self, text: str, author: str, tags: Iterable[str]) -> dict[str, Any]:
        record = {
            "id": uuid.uuid4().hex[:12],
            "type": "quote",
            "text": _required_value(text, "text"),
            "author": _required_value(author, "author"),
            "tag": _normalize_tags(tags),
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self.path.open("a", encoding="utf-8", newline="\n") as file:
                file.write(json.dumps(record, ensure_ascii=False) + "\n")
        except OSError as exc:
            raise QuoteStoreError(f"名言を保存できません: {exc}") from exc
        return record

    def delete(self, record_id: str) -> bool:
        records = self.load()
        remaining = [record for record in records if record["id"] != record_id]
        if len(remaining) == len(records):
            return False
        self._rewrite(remaining)
        return True

    def search(
        self,
        query: str | None = None,
        author: str | None = None,
        tag: str | None = None,
        record_id: str | None = None,
    ) -> list[dict[str, Any]]:
        records = self.load()
        query_folded = query.casefold() if query else None
        author_folded = author.casefold() if author else None
        tag_folded = tag.casefold() if tag else None

        def matches(record: dict[str, Any]) -> bool:
            if record_id and record["id"] != record_id:
                return False
            if author_folded and author_folded not in record["author"].casefold():
                return False
            if tag_folded and not any(
                tag_folded == item.casefold() for item in record["tag"]
            ):
                return False
            if query_folded:
                searchable = [
                    record["id"],
                    record["type"],
                    record["text"],
                    record["author"],
                    *record["tag"],
                ]
                if not any(query_folded in str(value).casefold() for value in searchable):
                    return False
            return True

        return [record for record in records if matches(record)]

    def _rewrite(self, records: Iterable[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                newline="\n",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as file:
                temporary_path = Path(file.name)
                for record in records:
                    file.write(json.dumps(record, ensure_ascii=False) + "\n")
            os.replace(temporary_path, self.path)
        except OSError as exc:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise QuoteStoreError(f"データファイルを更新できません: {exc}") from exc

    @staticmethod
    def _validate_record(record: Any, line_number: int) -> None:
        if not isinstance(record, dict):
            raise QuoteStoreError(f"{line_number} 行目はJSONオブジェクトではありません。")
        missing = REQUIRED_FIELDS - record.keys()
        if missing:
            raise QuoteStoreError(
                f"{line_number} 行目に必須項目がありません: {', '.join(sorted(missing))}"
            )
        if not all(isinstance(record[key], str) for key in ("id", "type", "text", "author")):
            raise QuoteStoreError(f"{line_number} 行目の文字列項目が不正です。")
        if not isinstance(record["tag"], list) or not all(
            isinstance(tag, str) for tag in record["tag"]
        ):
            raise QuoteStoreError(f"{line_number} 行目の tag は文字列の配列ではありません。")


def _required_value(value: str, name: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"{name} は空にできません。")
    return cleaned


def _normalize_tags(tags: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for raw_tag in tags:
        for tag in raw_tag.split(","):
            cleaned = tag.strip()
            key = cleaned.casefold()
            if cleaned and key not in seen:
                result.append(cleaned)
                seen.add(key)
    return result


def _print_records(records: list[dict[str, Any]]) -> None:
    if not records:
        print("該当する名言はありません。")
        return
    for record in records:
        tags = ", ".join(record["tag"]) if record["tag"] else "-"
        print(f'[{record["id"]}] {record["text"]}')
        print(f'  author: {record["author"]}  tag: {tags}  type: {record["type"]}')


def _run_interactive(store: QuoteStore) -> int:
    while True:
        print("\n名言集: 1) 登録  2) 削除  3) 検索  4) 一覧  0) 終了")
        choice = input("> ").strip()
        if choice == "0":
            return 0
        if choice == "1":
            text = input("text (English): ")
            author = input("author: ")
            tags = input("tag (カンマ区切り、省略可): ")
            record = store.add(text, author, [tags])
            print(f'登録しました。id: {record["id"]}')
        elif choice == "2":
            record_id = input("削除するid: ").strip()
            print("削除しました。" if store.delete(record_id) else "そのidは見つかりません。")
        elif choice == "3":
            query = input("検索語（text / author / tag / id）: ").strip()
            _print_records(store.search(query=query))
        elif choice == "4":
            _print_records(store.load())
        else:
            print("0〜4を入力してください。")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="JSONL形式の名言集を管理します。")
    parser.add_argument(
        "--file", type=Path, default=DEFAULT_DATA_FILE, help="JSONLファイルのパス"
    )
    subparsers = parser.add_subparsers(dest="command")

    add_parser = subparsers.add_parser("add", help="名言を登録")
    add_parser.add_argument("--text", required=True, help="英語の名言本文")
    add_parser.add_argument("--author", required=True, help="著者名")
    add_parser.add_argument(
        "--tag", action="append", default=[], help="タグ（複数回またはカンマ区切りで指定可）"
    )

    delete_parser = subparsers.add_parser("delete", help="IDを指定して削除")
    delete_parser.add_argument("id", help="削除する名言のID")

    search_parser = subparsers.add_parser("search", help="名言を検索")
    search_parser.add_argument("query", nargs="?", help="全項目を対象にする検索語")
    search_parser.add_argument("--author", help="著者名（部分一致）")
    search_parser.add_argument("--tag", help="タグ（完全一致、大文字小文字は無視）")
    search_parser.add_argument("--id", dest="record_id", help="ID（完全一致）")

    subparsers.add_parser("list", help="すべての名言を表示")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    store = QuoteStore(args.file)
    try:
        if args.command is None:
            return _run_interactive(store)
        if args.command == "add":
            record = store.add(args.text, args.author, args.tag)
            print(f'登録しました。id: {record["id"]}')
        elif args.command == "delete":
            if not store.delete(args.id):
                print("そのidは見つかりません。", file=sys.stderr)
                return 1
            print("削除しました。")
        elif args.command == "search":
            _print_records(store.search(args.query, args.author, args.tag, args.record_id))
        elif args.command == "list":
            _print_records(store.load())
        return 0
    except (QuoteStoreError, ValueError) as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 2
    except (EOFError, KeyboardInterrupt):
        print("\n終了しました。")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
