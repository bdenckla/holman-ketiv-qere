from __future__ import annotations


def matching_nusach_targets_in_mpp_verse_by_row_number(
    payload: dict[str, object],
) -> dict[str, list[str]]:
    """Return matching נוסח targets keyed by table row number (as string)."""
    rows_obj = payload.get("mam_plus_rows_matching_mpp_verse_nusach_target")
    if rows_obj is None:
        return {}
    if not isinstance(rows_obj, list):
        raise ValueError(
            "table_data.json mam_plus_rows_matching_mpp_verse_nusach_target must be a list"
        )

    out: dict[str, list[str]] = {}
    for row in rows_obj:
        if not isinstance(row, dict):
            raise ValueError(
                "table_data.json mam_plus_rows_matching_mpp_verse_nusach_target must contain only objects"
            )

        row_number = row.get("row_number")
        if not isinstance(row_number, int):
            raise ValueError(
                "mam_plus_rows_matching_mpp_verse_nusach_target row has invalid row_number"
            )

        targets_obj = row.get("matching_nusach_targets_in_mpp_verse")
        if targets_obj is None:
            out[str(row_number)] = []
            continue
        if not isinstance(targets_obj, list):
            raise ValueError(
                "matching_nusach_targets_in_mpp_verse must be a list when present"
            )

        targets: list[str] = []
        for target in targets_obj:
            if not isinstance(target, str):
                raise ValueError(
                    "matching_nusach_targets_in_mpp_verse must contain only strings"
                )
            targets.append(target)

        out[str(row_number)] = targets

    return out
