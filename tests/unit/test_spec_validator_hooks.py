from __future__ import annotations

import pytest

from synapse_os.specs.validator import (
    SpecValidationError,
    _validate_hooks_in_raw_metadata,
)


class TestValidateHooksInRawMetadata:
    def test_no_hooks_field_passes(self) -> None:
        _validate_hooks_in_raw_metadata({"id": "F1", "type": "feature"})

    def test_empty_hooks_list_passes(self) -> None:
        _validate_hooks_in_raw_metadata({"hooks": []})

    def test_valid_hook_passes(self) -> None:
        _validate_hooks_in_raw_metadata(
            {"hooks": [{"point": "pre_step", "handler": "some.module.func"}]}
        )

    def test_hooks_not_list_raises(self) -> None:
        with pytest.raises(SpecValidationError, match="hooks must be a list"):
            _validate_hooks_in_raw_metadata({"hooks": "not_a_list"})

    def test_hook_not_dict_raises(self) -> None:
        with pytest.raises(SpecValidationError, match=r"hooks\[0\] must be a dict"):
            _validate_hooks_in_raw_metadata({"hooks": ["string"]})

    def test_hook_missing_handler_raises(self) -> None:
        with pytest.raises(SpecValidationError, match="handler is required"):
            _validate_hooks_in_raw_metadata({"hooks": [{"point": "pre_step"}]})

    def test_hook_empty_handler_raises(self) -> None:
        with pytest.raises(SpecValidationError, match="handler is required"):
            _validate_hooks_in_raw_metadata(
                {"hooks": [{"point": "pre_step", "handler": ""}]}
            )

    def test_hook_missing_point_raises(self) -> None:
        with pytest.raises(SpecValidationError, match="point is required"):
            _validate_hooks_in_raw_metadata({"hooks": [{"handler": "some.func"}]})

    def test_hook_invalid_point_raises(self) -> None:
        with pytest.raises(SpecValidationError, match="point 'invalid' is not valid"):
            _validate_hooks_in_raw_metadata(
                {"hooks": [{"point": "invalid", "handler": "some.func"}]}
            )

    def test_all_valid_points_accepted(self) -> None:
        for point in (
            "pre_step",
            "post_step",
            "pre_state_transition",
            "post_state_transition",
        ):
            _validate_hooks_in_raw_metadata(
                {"hooks": [{"point": point, "handler": "some.func"}]}
            )
