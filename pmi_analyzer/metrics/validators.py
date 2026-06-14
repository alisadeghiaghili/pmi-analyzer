"""Validators for Shamkh metrics."""

from typing import List

from pmi_analyzer.exceptions import ValidationError
from pmi_analyzer.types import ShamkhMetrics

_NUMERIC_FIELDS = [
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
]


class MetricsValidator:
    """Validate a single ShamkhMetrics instance.

    Raises ValidationError for:
    - empty month string
    - all numeric fields None (no data)
    - any numeric field outside [0, 100]
    """

    def validate(self, metrics: ShamkhMetrics) -> bool:
        """Validate a single ShamkhMetrics.

        Args:
            metrics: ShamkhMetrics instance to validate.

        Returns:
            True if valid.

        Raises:
            ValidationError: if any rule is violated.
        """
        if not metrics.month or not metrics.month.strip():
            raise ValidationError("month is required and cannot be empty")

        if not metrics.validate():
            raise ValidationError(f"month={metrics.month}: at least one metric value is required")

        for field in _NUMERIC_FIELDS:
            val = getattr(metrics, field, None)
            if val is not None and not (0 <= val <= 100):
                raise ValidationError(
                    f"month={metrics.month}: {field}={val} is out of valid PMI range [0, 100]"
                )

        return True


def validate_metrics(metrics: List[ShamkhMetrics]) -> None:
    """Validate a list of ShamkhMetrics.

    Args:
        metrics: List of ShamkhMetrics to validate.

    Raises:
        ValidationError: if validation fails.
    """
    if not metrics:
        raise ValidationError("No metrics provided")

    validator = MetricsValidator()
    for i, m in enumerate(metrics):
        try:
            validator.validate(m)
        except ValidationError as e:
            raise ValidationError(f"Record {i}: {e}") from e
