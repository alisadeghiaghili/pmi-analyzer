"""Validators for Shamkh metrics."""

from typing import List
from pmi_analyzer.types import ShamkhMetrics
from pmi_analyzer.exceptions import ValidationError


def validate_metrics(metrics: List[ShamkhMetrics]) -> None:
    """
    Validate a list of ShamkhMetrics.

    Args:
        metrics: List of ShamkhMetrics to validate

    Raises:
        ValidationError: If validation fails
    """
    if not metrics:
        raise ValidationError("No metrics provided")

    for i, m in enumerate(metrics):
        if not m.month:
            raise ValidationError(f"Record {i}: month is required")
        if not m.validate():
            raise ValidationError(
                f"Record {i} (month={m.month}): at least one metric value is required"
            )

        for field in [
            "production",
            "new_orders",
            "sales",
            "raw_materials_inv",
            "final_goods_inv",
            "input_price",
            "production_expectations",
            "employment",
            "exports",
            "delivery_speed",
            "business_activity",
        ]:
            val = getattr(m, field, None)
            if val is not None and not (0 <= val <= 100):
                raise ValidationError(
                    f"Record {i} (month={m.month}): {field}={val} is out of valid PMI range [0, 100]"
                )
