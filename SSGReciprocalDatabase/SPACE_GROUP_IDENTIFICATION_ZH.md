# 倒空间群的标准空间群识别

## 使用

```wl
<< "SSGReciprocalDatabase`"
sg = getSSGReciprocalSpaceGroup["N143.16.1"];
sg["InternationalNumber"]
sg["InternationalSymbol"]
sg["ArithmeticCrystalClassSymbol"]
sg["CoordinateMatrix"]
sg["OriginShift"]
```

`getSSGReciprocalData[label]["ReciprocalSpaceGroup"]` 也返回同一份记录。
有理数沿用数据库 JSON 约定，以整数或 `"1/2"` 形式保存。

识别的是全部倒空间操作的普通几何空间群。原数据库中的反幺正标记、
自旋表示和 LB 保留各自的物理意义，不由这个普通空间群编号代替。
不同 SSG 可以对应同一个空间群编号。

## 输入和坐标

使用每个标签的 `ReciprocalMomentumGroupElements`。证书保留完整
`InputOperations`；换基及原点位移适用于这组输入操作。
表格显示功能可能已经使用另一原点消除了可去掉的 Q，不能把证书中的
原点位移直接套在已经变换过的表格上。

首先从恒等线性部分的操作收集完整纯平移格子，加上原来的整数周期。
结果是 `SourceTranslationBasis`，列向量用输入 BZ 坐标表示。
如果它不同于单位矩阵，这意味着几何群含额外纯平移；它不是对原来的
电子 Bloch 晶格 LB 定义作修改。

## 计算

1. 在完整操作集合上去重，缓存相同输入群的计算。
2. 用整数点群的平均不变度量，以及三个不同颜色的一般位置轨道构造辅助晶体。
3. spglib 2.7.0 提供标准 Hall setting 和候选换基。辅助晶体只是获取候选的计算工具。
4. 从 spglib 标准 Seitz 数据提取完整平移晶格，并转到标准原胞。
5. 精确检查候选换基将输入完整平移格子映到标准原胞整数格子。
6. 对每个对应线性矩阵建立共同原点方程，并用 Smith 标准型求解。
7. 用有理数逐项验证变换后全部操作集合与标准群相等；不只检查生成元或群阶。

坐标约定是

$$
\mathbf k'=C\mathbf k+\theta.
$$

在标准原胞中，匹配方程为

$$
A'_g=CA_gC^{-1},\qquad
(I-A'_g)\theta\equiv Q_g^{\rm std}-CQ_g\pmod{\mathbb Z^3}.
$$

`CoordinateMatrix` 和 `OriginShift` 对应 C 和 theta。
`StandardPrimitiveBasis` 的列向量用 Hall setting 的标准惯用胞坐标表示。
`ConventionalCoordinateMatrix` 和 `ConventionalOriginShift` 则直接给出到
该惯用胞的变换。不要在有心惯用胞中误用 mod Z^3 代替完整平移格子。

采用候选识别后精确验证，无需遍历所有候选：一个候选通过完整群相等检验
即给出该标准类型的构造性证书。若候选不通过，程序记录失败，不能据此宣称
该输入不属于任何标准空间群。本次程序没有实现失败后的完整整数正规化子搜索。
空间群编号及 setting 遵循 spglib/Hall 标准；没有额外合并对映编号。

## 复现

在本目录执行：

```sh
python3 identify_standard_space_groups.py
python3 validate_space_group_identification.py
python3 -m unittest test_standard_space_groups -v
```

计算脚本可使用 `--parent 143 --output /tmp/sg143-identification.json` 做单群检查。
完整结果写在包内 `Data/SpaceGroupIdentification.json`，验证报告在
`Data/SpaceGroupIdentificationValidation.json`。
候选生成依赖 numpy、sympy、spglib，Smith 求解复用本项目的
`enumerate_reciprocal_groups.py`。用户查询已打包数据不需要 Python。

验证范围是已有倒空间群与标准数据库的精确匹配，不是重新计算 O(3) 数据源
或重新证明 SSG 到倒空间群的物理推导。几何空间群采用完整纯平移格子，
其 symmorphic 性质与原始 BZ 上逐个操作的原点消除条件应分别理解。

## 来源

- spglib 标准空间群数据库：https://spglib.readthedocs.io/en/stable/database.html
- spglib 坐标变换约定：https://spglib.readthedocs.io/en/stable/definition.html
- CARAT 的 cocycle/空间群扩张识别：https://lbfm-rwth.github.io/carat/doc/progs/Vector_systems.html
- IUCr 算术晶类定义：https://dictionary.iucr.org/Arithmetic_crystal_class
- Zhang et al., General Theory of Momentum-Space Nonsymmorphic Symmetry, PRL 130, 256601 (2023)：https://arxiv.org/abs/2306.14410

本次 Q 的输入仍来自我们已有的 SSG 计算；新增步骤是标准空间群识别。
候选标准操作取自 spglib，coboundary 验证使用本项目的 Smith 求解器。
