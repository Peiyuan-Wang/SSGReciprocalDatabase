# 倒空间磁群识别：0.8.0

## 查询

```wl
PacletInstall["/absolute/path/SSGReciprocalDatabase-0.8.0.paclet"]
<< "SSGReciprocalDatabase`"
getSSGReciprocalMagneticSpaceGroup["N143.10.1"]
showSSGReciprocalMagneticGroup["N143.10.1"]
getSSGReciprocalFamilySpaceGroup["N143.10.1"]
```

更新后建议首次使用重启内核，以免内存中仍保留旧版本。普通查询只需要 Mathematica 和 paclet，不需要 Python 或 spglib。

旧函数 `getSSGReciprocalSpaceGroup` 保留兼容性，仍返回忽略反幺正标记后的普通 family space group，不是原始实空间 parent group。新增磁群函数返回完整的带标记倒空间群的 BNS/UNI 编号。

## 计算对象

每个操作保留三个量：

$$
(A_g,Q_g,s_g),\qquad A_g=s_gM_g^{-T},\qquad s_g\in\{+1,-1\}.
$$

其对倒空间坐标的作用及乘法是

$$
k\mapsto A_gk+Q_g,
$$

$$
(A,Q,s)(B,t,u)=(AB,Q+At,su).
$$

`A` 已含反幺正对动量带来的负号。匹配标准磁群时，把 `A` 作为几何矩阵，把 `s=-1` 记作 prime；不能再对 `A` 乘一次 `s`。这是倒空间的带标记几何群，与通常实空间磁群的标准 Seitz 表作坐标群同构比较。不是把原始实空间矩阵 `M` 直接拿去命名，也不是将反幺正操作改成了幺正操作。

## 两个平移晶格

输入坐标的周期为整数格子。标准磁群的幺正平移晶格由所有 `A=I,s=+1` 的平移和整数周期共同生成；忽略标记后的 family 格子还纳入 `A=I,s=-1` 的平移。二者在 type IV 中不同。如果一开始就把反幺正半平移当作普通周期，就会丢失 type IV 信息。

这些用于磁群命名的晶格不覆盖原记录中的 `LB`。`LB` 仍是原计算定义 Bloch 坐标所用的幺正中心子晶格。

## 精确证书

spglib 提供候选编号与设置。最终接受条件不是浮点容差匹配，而是以下有理数证书。设标准幺正原胞坐标为

$$
k'=Ck+\theta.
$$

所有操作必须同时满足

$$
A'_g=CA_gC^{-1},\qquad
Q'_g=CQ_g+(I-A'_g)\theta\pmod{\mathbb Z^3},\qquad s'_g=s_g.
$$

用 Smith 标准型求同一个 `theta`，并验证完整带标记操作集合相等、幺正平移晶格相等。这里的 `theta` 是标准设置变换，不限于半整数；它可以包含三分之一等数值，并不表示新增了这种阶数的内禀分数平移。

## 输出字段

| 字段 | 意义 |
|---|---|
| `BNSNumber`, `UNINumber`, `OGNumber` | 标准磁群编号；BNS 和 OG 是不同命名设置 |
| `MagneticType` | 1、2、3、4 对应 I、II、III、IV |
| `FamilySpaceGroup` | 忽略 prime 后的普通倒空间群 |
| `SourceUnitaryTranslationBasis` | 输入倒空间坐标中的幺正几何平移基，列向量 |
| `SourceFamilyTranslationBasis` | 忽略 prime 后的全部几何平移基，列向量 |
| `StandardUnitaryPrimitiveBasis` | 标准常规胞中的幺正原胞基，列向量 |
| `CoordinateMatrix`, `OriginShift` | 上式中的 `C,theta`，目标是标准幺正原胞 |
| `ConventionalCoordinateMatrix`, `ConventionalOriginShift` | 目标改为数据库常规胞的坐标变换 |
| `InputOperations` | 完整输入操作集，含反幺正标记 |
| `StandardPrimitiveOperations` | 标准幺正原胞中的完整带标记操作集 |
| `InputToStandardOperations` | 逐项对应，`InputIndex` 指向证书的 `InputOperations` |
| `ExactUnitaryLatticeEquality`, `ExactGradedOperationSetEquality` | 精确检查结果 |
| `ReferenceHallNumber` | 数据库设置索引；0 表示 API 的默认设置 |
| `StandardOperationsSource`, `StandardOperationsReference` | 新生成证书的标准操作来源；旧缓存默认 spglib 数据库 |

JSON 为精确性将非整数有理数保存为字符串，例如 `"1/2"`。

## 结果与范围

67,475 个已有标签均得到匹配，包含 3,953 个不同输入操作证书和 1,136 个 BNS 类型。按标签统计：I 型 5,535，II 型 27,647，III 型 27,549，IV 型 6,744。

| Xiao 标签 | BNS | UNI | 类型 | Family |
|---|---|---|---|---|
| N143.10.1 | 147.15 | 1245 | III | 147, P-3 |
| N143.16.1 | 143.1 | 1231 | I | 143, P3 |
| N65.9.123 | 37.186 | 284 | IV | 42, Fmm2 |

这些是现有数据库各标签所存参数代表的识别结果，不新增连续参数全域分层的证明。磁群编号保留反幺正分级，但不包含完整自旋表示矩阵、投影乘子或反幺正算符在 Bloch fiber 上的平方。因此不能仅凭 BNS 编号判定 Kramers 简并或拓扑电荷。

## 标准源交叉检查

spglib 2.7.0 二进制数据中，UNI 282、284（BNS 37.184、37.186）的幺正子群被识别为 SG36，而其官方磁 Hall 源表要求 SG37。这里不强行接受这两个二进制操作集，而是采用官方源表的生成元：`C 2 -2c 1c'` 和 `C 2 -2c 1bc'`。从普通 Hall 182 的 Ccc2 操作集，加上相应反幺正半平移，精确闭合生成标准磁群。证书明确记录此替代来源。8 个 SG65/SG67 标签用到这一重建。

来源：[spglib 官方磁 Hall 表](https://github.com/spglib/spglib/blob/develop/database/msg/magnetic_hall_symbols.yaml)，[官方磁群数据约定](https://spglib.readthedocs.io/en/stable/magnetic_dataset.html)。这是本地对数据源的交叉核对，不宣称已获上游确认。

## 重现

在脚本目录安装 `requirements-spacegroup.txt` 所列 Python 依赖后：

```sh
python3 identify_magnetic_space_groups.py
python3 validate_magnetic_space_groups.py
python3 -m unittest test_magnetic_space_groups test_standard_space_groups
```

识别器可复用缓存；`--retry-failures` 只重算失败记录。全库验证逐证书重放精确变换，再逐标签绑定原始数据，不只是统计成功标志。验证不等于独立科学审稿。
