from __future__ import annotations

SUPPORTED_QERE_DOC_PREFIXES = ("א-קרי=", "ל-קרי=")


def matching_template_arguments_in_mpp_verse_by_row_number(
    payload: dict[str, object],
) -> dict[str, list[dict[str, str]]]:
    """Return matching template argument records keyed by table row number."""
    rows_obj = payload.get("mam_plus_rows_matching_mpp_verse_template_arg")
    if rows_obj is None:
        return {}
    if not isinstance(rows_obj, list):
        raise ValueError(
            "table_data.json mam_plus_rows_matching_mpp_verse_template_arg must be a list"
        )

    out: dict[str, list[dict[str, str]]] = {}
    for row in rows_obj:
        if not isinstance(row, dict):
            raise ValueError(
                "table_data.json mam_plus_rows_matching_mpp_verse_template_arg must contain only objects"
            )

        row_number = row.get("row_number")
        if not isinstance(row_number, int):
            raise ValueError(
                "mam_plus_rows_matching_mpp_verse_template_arg row has invalid row_number"
            )

        targets_obj = row.get("matching_template_args_in_mpp_verse")
        if targets_obj is None:
            out[str(row_number)] = []
            continue
        out[str(row_number)] = _validated_template_arg_records(
            targets_obj,
            field_name="matching_template_args_in_mpp_verse",
        )

    return out


def supported_qere_wrapper_by_row_number(
    payload: dict[str, object],
) -> dict[str, dict[str, str]]:
    rows_obj = payload.get("mam_plus_rows_matching_mpp_verse_template_arg")
    if rows_obj is None:
        return {}
    if not isinstance(rows_obj, list):
        raise ValueError(
            "table_data.json mam_plus_rows_matching_mpp_verse_template_arg must be a list"
        )

    out: dict[str, dict[str, str]] = {}
    for row in rows_obj:
        if not isinstance(row, dict):
            raise ValueError(
                "mam_plus_rows_matching_mpp_verse_template_arg must contain only objects"
            )

        row_number = row.get("row_number")
        if not isinstance(row_number, int):
            raise ValueError(
                "mam_plus_rows_matching_mpp_verse_template_arg row has invalid row_number"
            )

        matching_args_raw = row.get("matching_template_args_in_mpp_verse")
        if matching_args_raw is None:
            matching_args = []
        else:
            matching_args = _validated_template_arg_records(
                matching_args_raw,
                field_name="matching_template_args_in_mpp_verse",
            )

        all_args_raw = row.get("template_args_in_mpp_verse")
        if all_args_raw is None:
            all_args = []
        else:
            all_args = _validated_template_arg_records(
                all_args_raw,
                field_name="template_args_in_mpp_verse",
            )

        wrapper = supported_qere_wrapper_from_template_args(matching_args, all_args)
        if wrapper is not None:
            out[str(row_number)] = wrapper

    return out


def supported_qere_wrapper_from_template_args(
    matching_template_args_in_mpp_verse: list[dict[str, str]],
    template_args_in_mpp_verse: list[dict[str, str]],
) -> dict[str, str] | None:
    candidates: list[tuple[str, str, str]] = []
    for match in matching_template_args_in_mpp_verse:
        candidate = _supported_qere_wrapper_candidate_for_match(
            match,
            template_args_in_mpp_verse,
        )
        if candidate is None or candidate in candidates:
            continue
        candidates.append(candidate)

    if len(candidates) != 1:
        return None

    template_name, ketiv, qere = candidates[0]
    return {
        "template_name": template_name,
        "ketiv": ketiv,
        "qere": qere,
    }


def _validated_template_arg_records(
    targets_obj: object,
    *,
    field_name: str,
) -> list[dict[str, str]]:
    if not isinstance(targets_obj, list):
        raise ValueError(f"{field_name} must be a list when present")

    targets: list[dict[str, str]] = []
    for target in targets_obj:
        if not isinstance(target, dict):
            raise ValueError(f"{field_name} must contain only objects")

        template_name = target.get("template_name")
        argument_key = target.get("argument_key")
        argument_text = target.get("argument_text")
        if not isinstance(template_name, str):
            raise ValueError(f"{field_name} record missing template_name")
        if not isinstance(argument_key, str):
            raise ValueError(f"{field_name} record missing argument_key")
        if not isinstance(argument_text, str):
            raise ValueError(f"{field_name} record missing argument_text")

        targets.append(
            {
                "template_name": template_name,
                "argument_key": argument_key,
                "argument_text": argument_text,
            }
        )

    return targets


def _supported_qere_wrapper_candidate_for_match(
    match: dict[str, str],
    template_args_in_mpp_verse: list[dict[str, str]],
) -> tuple[str, str, str] | None:
    template_name = match.get("template_name")
    argument_key = match.get("argument_key")
    argument_text = match.get("argument_text")
    if argument_key not in {"1", "2"}:
        return None
    if template_name is None or argument_text is None:
        return None

    candidates: list[tuple[str, str, str]] = []
    for index, raw_arg in enumerate(template_args_in_mpp_verse):
        if raw_arg.get("template_name") != template_name:
            continue
        if raw_arg.get("argument_key") != argument_key:
            continue
        if raw_arg.get("argument_text") != argument_text:
            continue

        candidate = _supported_qere_wrapper_candidate_from_index(
            template_name=template_name,
            argument_key=argument_key,
            argument_text=argument_text,
            template_args_in_mpp_verse=template_args_in_mpp_verse,
            index=index,
        )
        if candidate is None or candidate in candidates:
            continue
        candidates.append(candidate)

    if len(candidates) != 1:
        return None
    return candidates[0]


def _supported_qere_wrapper_candidate_from_index(
    *,
    template_name: str,
    argument_key: str,
    argument_text: str,
    template_args_in_mpp_verse: list[dict[str, str]],
    index: int,
) -> tuple[str, str, str] | None:
    partner_index = index + 1 if argument_key == "1" else index - 1
    if partner_index < 0 or partner_index >= len(template_args_in_mpp_verse):
        return None

    partner = template_args_in_mpp_verse[partner_index]
    if partner.get("template_name") != template_name:
        return None

    partner_key = partner.get("argument_key")
    if partner_key not in {"1", "2"}:
        return None
    expected_partner_key = "2" if argument_key == "1" else "1"
    if partner_key != expected_partner_key:
        return None

    partner_text = partner.get("argument_text")
    if partner_text is None:
        return None

    args_by_key = {
        argument_key: argument_text,
        partner_key: partner_text,
    }
    if set(args_by_key) != {"1", "2"}:
        return None

    if template_name == 'קו"כ-אם':
        qere = _strip_supported_qere_doc(args_by_key["2"])
        if qere is None:
            return None
        return template_name, args_by_key["1"], qere

    if template_name == "קרי ולא כתיב":
        return template_name, args_by_key["1"], args_by_key["2"]

    if template_name == "כתיב ולא קרי":
        return None

    if 'כו"ק' in template_name or 'קו"כ' in template_name:
        return template_name, args_by_key["1"], args_by_key["2"]

    return None


def _strip_supported_qere_doc(text: str) -> str | None:
    for prefix in SUPPORTED_QERE_DOC_PREFIXES:
        if text.startswith(prefix):
            return text[len(prefix) :]
    return None
