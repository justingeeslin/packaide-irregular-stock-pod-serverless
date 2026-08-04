from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import rp_handler


class RunPodPackaideHandlerTests(unittest.TestCase):
    def test_handler_passes_input_to_pack_irregular(self) -> None:
        pack_irregular = Mock(return_value=([(0, "<svg>packed</svg>")], 2, 0))
        job = {
            "input": {
                "stock_svg": "<svg>stock</svg>",
                "parts_svg": "<svg>parts</svg>",
                "tolerance": 0.02,
                "offset": 0,
                "rotations": 1,
                "persist": False,
            }
        }

        with patch.object(
            rp_handler,
            "_load_pack_irregular",
            return_value=pack_irregular,
        ):
            result = rp_handler.handler(job)

        pack_irregular.assert_called_once_with(
            ["<svg>stock</svg>"],
            "<svg>parts</svg>",
            tolerance=0.02,
            offset=0,
            rotations=1,
            persist=False,
        )
        self.assertEqual(
            result,
            {
                "outputs": [{"sheet_index": 0, "svg": "<svg>packed</svg>"}],
                "placed": 2,
                "unplaced": 0,
                "svg": "<svg>packed</svg>",
            },
        )

    def test_handler_accepts_multiple_stock_svgs_and_nested_options(self) -> None:
        pack_irregular = Mock(return_value=([(1, "<svg>sheet-b</svg>")], 1, 1))
        job = {
            "input": {
                "stock_svgs": ["<svg>stock-a</svg>", "<svg>stock-b</svg>"],
                "shapes_svg": "<svg>parts</svg>",
                "pack_options": {
                    "partial_solution": True,
                    "include_stock": False,
                    "ignored": "ignored",
                },
                "include_stock": True,
            }
        }

        with patch.object(
            rp_handler,
            "_load_pack_irregular",
            return_value=pack_irregular,
        ):
            result = rp_handler.handler(job)

        pack_irregular.assert_called_once_with(
            ["<svg>stock-a</svg>", "<svg>stock-b</svg>"],
            "<svg>parts</svg>",
            partial_solution=True,
            include_stock=True,
        )
        self.assertEqual(result["placed"], 1)
        self.assertEqual(result["unplaced"], 1)
        self.assertEqual(result["svg"], "<svg>sheet-b</svg>")

    def test_handler_returns_validation_error_for_missing_svg_input(self) -> None:
        result = rp_handler.handler({"input": {"stock_svg": "<svg>stock</svg>"}})

        self.assertEqual(
            result,
            {"error": 'Job input must include "parts_svg" or "shapes_svg".'},
        )

    def test_handler_returns_validation_error_for_non_object_input(self) -> None:
        result = rp_handler.handler({"input": "not-an-object"})

        self.assertEqual(
            result,
            {"error": 'RunPod job "input" must be a JSON object.'},
        )


if __name__ == "__main__":
    unittest.main()
