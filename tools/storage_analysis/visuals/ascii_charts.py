from __future__ import annotations
from typing import List, Dict, Any, Tuple


class AsciiCharts:
    """
    Renders clean, interpretable ASCII-based charts, distributions,
    and data tables for terminal-based episodic memory analysis.
    """

    @staticmethod
    def render_header(title: str, width: int = 60) -> str:
        border = "=" * width
        padded_title = title.center(width)
        return f"\n{border}\n{padded_title}\n{border}"

    @staticmethod
    def render_bar_chart(
        data: Dict[str, float | int], title: str = "", max_bar_width: int = 35
    ) -> str:
        """Renders a horizontal bar chart mapping category names to numerical values."""
        if not data:
            return "No data available for chart."

        lines = []
        if title:
            lines.append(f"\n--- {title} ---")

        max_val = max(data.values()) if data.values() else 1.0
        max_val = max(max_val, 1.0)  # Prevent division by zero

        # Find max key length for clean alignment
        max_key_len = max(len(str(k)) for k in data.keys())

        for key, val in data.items():
            bar_len = int((val / max_val) * max_bar_width)
            bar = "█" * bar_len
            formatted_key = str(key).ljust(max_key_len)
            lines.append(f"  {formatted_key} | {bar} ({val:,})")

        return "\n".join(lines)

    @staticmethod
    def render_histogram(
        values: List[float | int], bins: int = 5, title: str = "Distribution Histogram"
    ) -> str:
        """Renders a frequency distribution histogram for continuous or discrete metrics."""
        if not values:
            return f"\n--- {title} ---\nNo values available."

        min_val = min(values)
        max_val = max(values)

        if min_val == max_val:
            return f"\n--- {title} ---\nAll values are identical: {min_val} (Count: {len(values)})"

        bin_width = (max_val - min_val) / bins
        bin_counts = [0] * bins
        bin_ranges = []

        for i in range(bins):
            b_start = min_val + i * bin_width
            b_end = min_val + (i + 1) * bin_width
            bin_ranges.append((b_start, b_end))

        for val in values:
            # Handle edge case for maximum value falling into the last bin
            idx = int((val - min_val) / bin_width)
            if idx >= bins:
                idx = bins - 1
            bin_counts[idx] += 1

        max_count = max(bin_counts) if bin_counts else 1
        max_bar_width = 30

        lines = [f"\n--- {title} ---"]
        for i, count in enumerate(bin_counts):
            start, end = bin_ranges[i]
            bar_len = int((count / max_count) * max_bar_width) if max_count > 0 else 0
            bar = "█" * bar_len
            range_label = f"[{start:,.1f} - {end:,.1f}]".ljust(22)
            lines.append(f"  {range_label} | {bar} ({count} items)")

        return "\n".join(lines)

    @staticmethod
    def render_table(headers: List[str], rows: List[List[Any]], title: str = "") -> str:
        """Renders a cleanly formatted ASCII data table."""
        if not rows:
            return f"\n--- {title} ---\nNo rows available."

        # Compute column widths
        col_widths = [len(str(h)) for h in headers]
        for row in rows:
            for i, val in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(val)))

        # Format border separator
        separator = "+" + "+".join(["-" * (w + 2) for w in col_widths]) + "+"

        lines = []
        if title:
            lines.append(f"\n{title}")

        lines.append(separator)

        # Header row
        header_str = (
            "|"
            + "|".join([str(h).center(w + 2) for h, w in zip(headers, col_widths)])
            + "|"
        )
        lines.append(header_str)
        lines.append(separator)

        # Data rows
        for row in rows:
            row_str = (
                "|"
                + "|".join([str(val).ljust(w + 2) for val, w in zip(row, col_widths)])
                + "|"
            )
            lines.append(row_str)

        lines.append(separator)
        return "\n".join(lines)
