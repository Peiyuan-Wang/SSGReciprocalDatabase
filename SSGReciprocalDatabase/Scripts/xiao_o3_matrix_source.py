#!/usr/bin/env python3
"""Evaluate exact O(3) representation matrices from the generated source."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

import sympy as sp


def _rational(vector: Sequence[int]) -> sp.Rational:
    if vector[3] == 0:
        return sp.S.Zero
    return sp.Rational(vector[0], vector[3])


class XiaoO3MatrixSource:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.data = json.loads(path.read_text(encoding="utf-8"))
        self.constants = [
            sp.sympify(value, locals={"sqrt": sp.sqrt})
            for value in self.data["ExactConstantTable"]
        ]

    def labels(self) -> tuple[str, ...]:
        return tuple(self.data["XiaoRecords"])

    def record(self, xiao_label: str) -> dict:
        return self.data["XiaoRecords"][xiao_label]

    def alternative_count(self, xiao_label: str) -> int:
        return len(self.record(xiao_label)["Alternatives"])

    def operator_count(self, xiao_label: str, alternative: int = 0) -> int:
        record = self.record(xiao_label)
        labels = record["Alternatives"][alternative]["Constituents"]
        first = self.data["PIRRecords"][f'{record["ParentSpaceGroup"]}:{labels[0]}']
        return len(first["Operators"])

    def seitz_operator(self, xiao_label: str, operator: int, alternative: int = 0) -> sp.Matrix:
        record = self.record(xiao_label)
        label = record["Alternatives"][alternative]["Constituents"][0]
        pir = self.data["PIRRecords"][f'{record["ParentSpaceGroup"]}:{label}']
        return sp.Matrix(pir["Operators"][operator]["AugmentedMatrix"])

    def pir_matrix(
        self,
        space_group: int,
        label: str,
        operator: int,
        parameters: Sequence[sp.Expr | float | int] = (0, 0, 0),
    ) -> sp.Matrix:
        pir = self.data["PIRRecords"][f"{space_group}:{label}"]
        op = pir["Operators"][operator]
        point = sp.Matrix([
            [self.constants[code] for code in row]
            for row in op["PointMatrixCodes"]
        ])
        if pir["KSpecial"]:
            return point
        if len(parameters) != 3:
            raise ValueError("parameters must be (alpha, beta, gamma)")
        tvector = op["IRTranslation"]
        if tvector is None or tvector[3] == 0:
            raise ValueError(f"invalid ISO-IR translation for {space_group}:{label}")
        translation = self._pir_translation_matrix(pir, tvector, parameters)
        return sp.simplify(translation * point)

    def _pir_translation_matrix(
        self,
        pir: dict,
        tvector: Sequence[int],
        parameters: Sequence[sp.Expr | float | int],
    ) -> sp.Matrix:
        dimension = pir["Dimension"]
        block_count = pir["PMKCount"]
        if dimension % block_count:
            raise ValueError(f"IR dimension is not divisible by PMKCount for {space_group}:{label}")
        block_dimension = dimension // block_count
        translation = sp.zeros(dimension)
        t = [sp.Rational(tvector[index], tvector[3]) for index in range(3)]
        for block_index, k_raw in enumerate(pir["KVectors"]):
            k = []
            for coordinate in range(3):
                value = sp.Rational(k_raw[0][coordinate], k_raw[0][3])
                for parameter_index in range(3):
                    column = k_raw[parameter_index + 1]
                    if column[3] != 0:
                        value += sp.sympify(parameters[parameter_index]) * sp.Rational(
                            column[coordinate], column[3]
                        )
                k.append(value)
            phase = sp.simplify(sum(k[index] * t[index] for index in range(3)))
            cosine = sp.cos(2 * sp.pi * phase)
            sine = sp.sin(2 * sp.pi * phase)
            start = block_index * block_dimension
            for index in range(block_dimension):
                translation[start + index, start + index] = cosine
            for index in range(block_dimension // 2):
                translation[start + index, start + block_dimension // 2 + index] = sine
                translation[start + block_dimension // 2 + index, start + index] = -sine
        return translation

    def pir_primitive_translation_matrix(
        self,
        space_group: int,
        label: str,
        translation: int,
        parameters: Sequence[sp.Expr | float | int] = (0, 0, 0),
    ) -> sp.Matrix:
        pir = self.data["PIRRecords"][f"{space_group}:{label}"]
        return self._pir_translation_matrix(
            pir, pir["PrimitiveTranslations"][translation], parameters
        )

    def matrix(
        self,
        xiao_label: str,
        operator: int,
        alternative: int = 0,
        component_parameters: Sequence[Sequence[sp.Expr | float | int]] | None = None,
    ) -> sp.Matrix:
        record = self.record(xiao_label)
        labels = record["Alternatives"][alternative]["Constituents"]
        if component_parameters is None:
            component_parameters = [(0, 0, 0)] * len(labels)
        if len(component_parameters) != len(labels):
            raise ValueError("component_parameters must have one triple per PIR constituent")
        matrices = [
            self.pir_matrix(
                record["ParentSpaceGroup"], label, operator, component_parameters[index]
            )
            for index, label in enumerate(labels)
        ]
        return sp.diag(*matrices)

    def primitive_translation_matrix(
        self,
        xiao_label: str,
        translation: int,
        alternative: int = 0,
        component_parameters: Sequence[Sequence[sp.Expr | float | int]] | None = None,
    ) -> sp.Matrix:
        record = self.record(xiao_label)
        labels = record["Alternatives"][alternative]["Constituents"]
        if component_parameters is None:
            component_parameters = [(0, 0, 0)] * len(labels)
        matrices = [
            self.pir_primitive_translation_matrix(
                record["ParentSpaceGroup"], label, translation, component_parameters[index]
            )
            for index, label in enumerate(labels)
        ]
        return sp.diag(*matrices)

    def embed_o3(self, xiao_label: str, matrix: sp.Matrix) -> sp.Matrix:
        order = xiao_label[0]
        if order == "N":
            return matrix
        if order == "P":
            return sp.diag(matrix, sp.simplify(matrix.det()))
        if order == "L":
            return sp.diag(matrix[0, 0], 1, 1)
        raise ValueError(f"invalid Xiao label: {xiao_label}")
