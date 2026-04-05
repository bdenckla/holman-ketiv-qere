from __future__ import annotations

from collections.abc import Iterator


def _iter_plus_verse_payloads(
    plus_json: object,
) -> Iterator[tuple[int, int, int, object]]:
    if not isinstance(plus_json, dict):
        raise ValueError("plus JSON root must be an object")

    header = plus_json.get("header")
    if not isinstance(header, dict):
        raise ValueError("plus JSON missing object key 'header'")

    he_to_int = header.get("he_to_int")
    if not isinstance(he_to_int, dict):
        raise ValueError("plus JSON header missing object key 'he_to_int'")

    book39s = plus_json.get("book39s")
    if not isinstance(book39s, list):
        raise ValueError("plus JSON missing list key 'book39s'")

    for book39_index, book39 in enumerate(book39s):
        if not isinstance(book39, dict):
            raise ValueError(f"book39 entry must be object, got {type(book39)}")
        chapters = book39.get("chapters")
        if not isinstance(chapters, dict):
            raise ValueError("book39 entry missing object key 'chapters'")

        for he_chapter, verse_map in chapters.items():
            if not isinstance(he_chapter, str):
                raise ValueError(f"chapter key must be string, got {type(he_chapter)}")
            chapter_num = he_to_int.get(he_chapter)
            if not isinstance(chapter_num, int):
                raise ValueError(f"chapter {he_chapter!r} missing in header.he_to_int")
            if not isinstance(verse_map, dict):
                raise ValueError(f"chapter value must be object, got {type(verse_map)}")

            for he_verse, verse_payload in verse_map.items():
                if not isinstance(he_verse, str):
                    raise ValueError(f"verse key must be string, got {type(he_verse)}")
                if he_verse in ("0", "תתת"):
                    continue
                verse_num = he_to_int.get(he_verse)
                if not isinstance(verse_num, int):
                    raise ValueError(f"verse {he_verse!r} missing in header.he_to_int")

                yield (book39_index, chapter_num, verse_num, verse_payload)


def _collect_text_fragments(node: object, out_parts: list[str]) -> None:
    if isinstance(node, str):
        out_parts.append(node)
        return
    if isinstance(node, list):
        for item in node:
            _collect_text_fragments(item, out_parts)
        return
    if isinstance(node, dict):
        tmpl_name = node.get("tmpl_name")
        tmpl_params = node.get("tmpl_params")
        if isinstance(tmpl_params, dict):
            if tmpl_name == "נוסח":
                # In plus JSON, param 1 is the in-verse target; param 2 is documentation.
                _collect_text_fragments(tmpl_params.get("1"), out_parts)
                return
            for value in tmpl_params.values():
                _collect_text_fragments(value, out_parts)


def _render_template_like_text(node: object) -> str:
    if isinstance(node, str):
        return node

    if isinstance(node, list):
        return "".join(_render_template_like_text(item) for item in node)

    if isinstance(node, dict):
        tmpl_name = node.get("tmpl_name")
        tmpl_params = node.get("tmpl_params")
        if isinstance(tmpl_name, str) and isinstance(tmpl_params, dict):
            return _render_template_call(tmpl_name, tmpl_params)

        # Fallback for non-template container nodes.
        return "".join(_render_template_like_text(value) for value in node.values())

    return ""


def _render_template_call(tmpl_name: str, tmpl_params: dict[object, object]) -> str:
    rendered_args: list[str] = []
    for key, value in tmpl_params.items():
        rendered_value = _render_template_like_text(value)
        if isinstance(key, str) and key.isdigit():
            rendered_args.append(rendered_value)
        else:
            rendered_args.append(f"{key}={rendered_value}")

    if not rendered_args:
        return f"{{{{{tmpl_name}}}}}"

    return f"{{{{{tmpl_name}|{'|'.join(rendered_args)}}}}}"


def _collect_nusach_targets(node: object, out_targets: list[str]) -> None:
    if isinstance(node, list):
        for item in node:
            _collect_nusach_targets(item, out_targets)
        return

    if isinstance(node, dict):
        tmpl_name = node.get("tmpl_name")
        tmpl_params = node.get("tmpl_params")
        if isinstance(tmpl_params, dict):
            if tmpl_name == "נוסח":
                target_text = _render_template_like_text(tmpl_params.get("1")).strip()
                if target_text:
                    out_targets.append(target_text)

                # Skip param 2 because it is documentation, not verse text.
                for key, value in tmpl_params.items():
                    if key in {"1", "2"}:
                        continue
                    _collect_nusach_targets(value, out_targets)
                return

            for value in tmpl_params.values():
                _collect_nusach_targets(value, out_targets)


def verse_nusach_targets_by_location(
    plus_json: object,
) -> dict[tuple[int, int, int], list[str]]:
    out: dict[tuple[int, int, int], list[str]] = {}
    for book39_index, chapter_num, verse_num, verse_payload in _iter_plus_verse_payloads(
        plus_json
    ):
        targets: list[str] = []
        _collect_nusach_targets(verse_payload, targets)
        out[(book39_index, chapter_num, verse_num)] = targets
    return out


def _collect_template_argument_records(
    node: object,
    out_records: list[dict[str, str]],
) -> None:
    if isinstance(node, list):
        for item in node:
            _collect_template_argument_records(item, out_records)
        return

    if isinstance(node, dict):
        tmpl_name = node.get("tmpl_name")
        tmpl_params = node.get("tmpl_params")
        if isinstance(tmpl_name, str) and isinstance(tmpl_params, dict):
            for key, value in tmpl_params.items():
                argument_key = str(key)
                # In plus JSON, נוסח param 2 is documentation, not verse text.
                if tmpl_name == "נוסח" and argument_key == "2":
                    continue

                argument_text = _render_template_like_text(value).strip()
                if argument_text:
                    out_records.append(
                        {
                            "template_name": tmpl_name,
                            "argument_key": argument_key,
                            "argument_text": argument_text,
                        }
                    )

                _collect_template_argument_records(value, out_records)
            return

        for value in node.values():
            _collect_template_argument_records(value, out_records)


def verse_template_argument_records_by_location(
    plus_json: object,
) -> dict[tuple[int, int, int], list[dict[str, str]]]:
    out: dict[tuple[int, int, int], list[dict[str, str]]] = {}
    for book39_index, chapter_num, verse_num, verse_payload in _iter_plus_verse_payloads(
        plus_json
    ):
        records: list[dict[str, str]] = []
        _collect_template_argument_records(verse_payload, records)
        out[(book39_index, chapter_num, verse_num)] = records
    return out


def verse_texts_by_location(
    plus_json: object,
) -> dict[tuple[int, int, int], str]:
    out: dict[tuple[int, int, int], str] = {}
    for book39_index, chapter_num, verse_num, verse_payload in _iter_plus_verse_payloads(
        plus_json
    ):
        text_parts: list[str] = []
        _collect_text_fragments(verse_payload, text_parts)
        out[(book39_index, chapter_num, verse_num)] = "".join(text_parts)
    return out