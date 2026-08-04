from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import Any, Callable


PackIrregular = Callable[..., tuple[list[tuple[int, str]], int, int]]
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())

PACK_OPTION_KEYS = {
    "offset",
    "tolerance",
    "partial_solution",
    "rotations",
    "persist",
    "include_stock",
    "stock_inset",
}


class InputError(ValueError):
    """Raised when a RunPod job input cannot be mapped to Packaide."""


def handler(job: Mapping[str, Any]) -> dict[str, Any]:
    """RunPod entry point."""

    try:
        job_input = _extract_job_input(job)
        return pack_job_input(job_input)
    except InputError as error:
        LOGGER.warning("Invalid Packaide worker input: %s", error)
        return {"error": str(error)}


def pack_job_input(job_input: Mapping[str, Any]) -> dict[str, Any]:
    stock_svgs = _extract_stock_svgs(job_input)
    shapes_svg = _extract_shapes_svg(job_input)
    pack_options = _extract_pack_options(job_input)
    LOGGER.info(
        "Starting Packaide job: stock_count=%d stock_chars=%d shapes_chars=%d options=%s",
        len(stock_svgs),
        sum(len(svg) for svg in stock_svgs),
        len(shapes_svg),
        sorted(pack_options),
    )

    pack_irregular = _load_pack_irregular()
    outputs, placed, unplaced = pack_irregular(
        stock_svgs,
        shapes_svg,
        **pack_options,
    )
    LOGGER.info(
        "Finished Packaide job: outputs=%d placed=%d unplaced=%d",
        len(outputs),
        placed,
        unplaced,
    )

    serialized_outputs = [
        {"sheet_index": int(sheet_index), "svg": svg}
        for sheet_index, svg in outputs
    ]
    result: dict[str, Any] = {
        "outputs": serialized_outputs,
        "placed": int(placed),
        "unplaced": int(unplaced),
    }
    if len(serialized_outputs) == 1:
        result["svg"] = serialized_outputs[0]["svg"]
    return result


def _extract_job_input(job: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(job, Mapping):
        raise InputError("RunPod job must be a JSON object.")
    if "input" not in job:
        raise InputError('RunPod job is missing the "input" object.')

    job_input = job["input"]
    if not isinstance(job_input, Mapping):
        raise InputError('RunPod job "input" must be a JSON object.')
    return job_input


def _extract_stock_svgs(job_input: Mapping[str, Any]) -> list[str]:
    has_stock_svg = "stock_svg" in job_input
    has_stock_svgs = "stock_svgs" in job_input
    if has_stock_svg and has_stock_svgs:
        raise InputError('Provide either "stock_svg" or "stock_svgs", not both.')
    if not has_stock_svg and not has_stock_svgs:
        raise InputError('Job input must include "stock_svg" or "stock_svgs".')

    if has_stock_svg:
        stock_svg = job_input["stock_svg"]
        if not _is_nonempty_string(stock_svg):
            raise InputError('"stock_svg" must be a non-empty SVG string.')
        return [stock_svg]

    stock_svgs = job_input["stock_svgs"]
    if (
        not isinstance(stock_svgs, Sequence)
        or isinstance(stock_svgs, (str, bytes))
        or not stock_svgs
    ):
        raise InputError('"stock_svgs" must be a non-empty list of SVG strings.')
    if not all(_is_nonempty_string(svg) for svg in stock_svgs):
        raise InputError('"stock_svgs" must contain only non-empty SVG strings.')
    return list(stock_svgs)


def _extract_shapes_svg(job_input: Mapping[str, Any]) -> str:
    for key in ("parts_svg", "shapes_svg"):
        value = job_input.get(key)
        if value is not None:
            if not _is_nonempty_string(value):
                raise InputError(f'"{key}" must be a non-empty SVG string.')
            return value
    raise InputError('Job input must include "parts_svg" or "shapes_svg".')


def _extract_pack_options(job_input: Mapping[str, Any]) -> dict[str, Any]:
    options: dict[str, Any] = {}

    nested_options = job_input.get("pack_options", {})
    if nested_options is None:
        nested_options = {}
    if not isinstance(nested_options, Mapping):
        raise InputError('"pack_options" must be a JSON object when provided.')

    for key, value in nested_options.items():
        if key in PACK_OPTION_KEYS:
            options[key] = value

    for key in PACK_OPTION_KEYS:
        if key in job_input:
            options[key] = job_input[key]

    return options


def _load_pack_irregular() -> PackIrregular:
    from packaide_irregular_stock import pack_irregular

    return pack_irregular


def _is_nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


if __name__ == "__main__":
    import runpod

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    runpod.serverless.start({"handler": handler})
