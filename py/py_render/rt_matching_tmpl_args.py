from __future__ import annotations

SUPPORTED_QERE_DOC_PREFIXES = ("א-קרי=",)


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
                raise ValueError(
                    "matching template argument record missing template_name"
                )
            if not isinstance(argument_key, str):
                raise ValueError(
                    "matching template argument record missing argument_key"
                )
            if not isinstance(argument_text, str):
                raise ValueError(
                    "matching template argument record missing argument_text"
                )

            targets.append(
                {
                    "template_name": template_name,
                    "argument_key": argument_key,
                    "argument_text": argument_text,
                }
            )

        out[str(row_number)] = targets

    return out


def mpp_template_calls_by_row_number(
    payload: dict[str, object],
) -> dict[str, list[str]]:
    """Return full MPP template call strings (from נוסח args) for rows with matching templates."""
    rows_obj = payload.get("mam_plus_rows_matching_mpp_verse_template_arg")
    if rows_obj is None:
        return {}
    if not isinstance(rows_obj, list):
        raise ValueError(
            "table_data.json mam_plus_rows_matching_mpp_verse_template_arg must be a list"
        )

    out: dict[str, list[str]] = {}
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

        matching_args = row.get("matching_template_args_in_mpp_verse") or []
        all_args_raw = row.get("template_args_in_mpp_verse")
        all_args: list = all_args_raw if isinstance(all_args_raw, list) else []
        out[str(row_number)] = _nusakh_calls_for_row(matching_args, all_args)

    return out


def _nusakh_calls_for_row(matching_args: list, all_args: list) -> list[str]:
    calls: list[str] = []
    for match in matching_args:
        tmpl_name = match.get("template_name", "")
        if tmpl_name == "נוסח":
            arg_text = match.get("argument_text", "")
            if arg_text and arg_text not in calls:
                calls.append(arg_text)
        else:
            for arg in all_args:
                if arg.get("template_name") != "נוסח":
                    continue
                arg_text = arg.get("argument_text", "")
                if (
                    f"{{{{{tmpl_name}|" in arg_text
                    or arg_text == f"{{{{{tmpl_name}}}}}"
                ):
                    if arg_text not in calls:
                        calls.append(arg_text)
                    break
    if calls:
        return calls

    synthesized_call = _synthesized_single_template_call(all_args)
    if synthesized_call is not None:
        return [synthesized_call]

    return calls


def _synthesized_single_template_call(all_args: list) -> str | None:
    template_args = [arg for arg in all_args if isinstance(arg, dict)]
    if not template_args:
        return None
    if any(arg.get("template_name") == "נוסח" for arg in template_args):
        return None

    template_names = {
        arg.get("template_name")
        for arg in template_args
        if isinstance(arg.get("template_name"), str)
    }
    if len(template_names) != 1:
        return None

    args_by_key: dict[str, str] = {}
    for arg in template_args:
        argument_key = arg.get("argument_key")
        argument_text = arg.get("argument_text")
        if not isinstance(argument_key, str) or not isinstance(argument_text, str):
            return None
        if argument_key not in {"1", "2"} or argument_key in args_by_key:
            return None
        args_by_key[argument_key] = argument_text

    if set(args_by_key) != {"1", "2"}:
        return None

    qere_doc = args_by_key["2"]
    if not any(qere_doc.startswith(prefix) for prefix in SUPPORTED_QERE_DOC_PREFIXES):
        return None

    template_name = next(iter(template_names))
    return f"{{{{{template_name}|{args_by_key['1']}|{qere_doc}}}}}"
