from __future__ import annotations


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
        if not isinstance(targets_obj, list):
            raise ValueError(
                "matching_template_args_in_mpp_verse must be a list when present"
            )

        targets: list[dict[str, str]] = []
        for target in targets_obj:
            if not isinstance(target, dict):
                raise ValueError(
                    "matching_template_args_in_mpp_verse must contain only objects"
                )

            template_name = target.get("template_name")
            argument_key = target.get("argument_key")
            argument_text = target.get("argument_text")
            if not isinstance(template_name, str):
                raise ValueError("matching template argument record missing template_name")
            if not isinstance(argument_key, str):
                raise ValueError("matching template argument record missing argument_key")
            if not isinstance(argument_text, str):
                raise ValueError("matching template argument record missing argument_text")

            targets.append(
                {
                    "template_name": template_name,
                    "argument_key": argument_key,
                    "argument_text": argument_text,
                }
            )

        out[str(row_number)] = targets

    return out
