#!/usr/bin/env python3
"""Parse independent SBZ labels from Xiao et al. Appendix F rows."""

from __future__ import annotations

import re


# In pdftotext output the check mark in the Commute/Symmorphic columns is
# usually lost, while a cross is retained.  Column position is recoverable
# from the number of trailing placeholder fields.
_NONCOMMUTING_SUFFIX = re.compile(r"×\s+-\s+-\s+-\s+-\s+-$")
_NONSYMMORPHIC_SUFFIX = re.compile(r"×\s+-\s+-$")


def appendix_f_labels(ssg_label: str, display: str) -> dict[str, object]:
    """Return Appendix-F labels without using representation matrices.

    Collinear rows do not define commuting or nonsymmorphic SBZ labels in
    Xiao et al. and therefore return ``None`` for both fields.
    """

    if not ssg_label or ssg_label[0] not in "LPN":
        raise ValueError(f"invalid Xiao SSG label: {ssg_label!r}")
    if ssg_label[0] == "L":
        return {
            "translation_projectivity": None,
            "noncommuting": None,
            "nonsymmorphic": None,
        }
    normalized = " ".join(display.split())
    noncommuting = bool(_NONCOMMUTING_SUFFIX.search(normalized))
    nonsymmorphic = bool(_NONSYMMORPHIC_SUFFIX.search(normalized)) and not noncommuting
    if "×" in normalized and not (noncommuting or nonsymmorphic):
        raise ValueError(
            f"cannot assign Appendix-F cross to a table column for {ssg_label}: {display!r}"
        )
    return {
        "translation_projectivity": "noncommuting" if noncommuting else "commuting",
        "noncommuting": noncommuting,
        "nonsymmorphic": nonsymmorphic,
    }

