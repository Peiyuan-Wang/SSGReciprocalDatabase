# SSGReciprocalDatabase 0.6.0 全量构建报告

## 结果

程序包已为 Xiao 分类中的全部 67,475 个 SSG 生成倒空间对称群记录，覆盖
230 个母空间群。记录中不存在 `Missing` 或 `Unsupported` 状态。

每个 SSG 记录包含：

- 物理 Bloch 晶格 `LB`；
- 每个生成元的实空间整数矩阵 `SpatialPointMatrix`，即 `M_g`；
- 幺正/反幺正 grading `Grading`，即 `s_g`；
- 动量线性作用 `MomentumLinearPart=LinearPart=s_g M_g^(-T)`；
- 分数倒格平移 `FractionalTranslation=Q_g`；
- 倒空间 Seitz 对 `(A_g,Q_g)`；
- 保留 grading 的完整群闭包；
- 忘掉 grading 后的动量作用群；
- 共同动量原点移动的 Smith 型可解性结果和 nonsymmorphic 判定。

## 数据约定

表示矩阵取自官方 ISO-IR Miller--Love/CDML 数据，并转换到 primitive
direct-lattice basis。若同一 Xiao 类包含多个等价的 ISO-IR PIR 实现，完整
O(3) 数据源保留全部 alternatives；预计算倒空间数据库固定采用 alternative 1
作为确定性的代表元。连续参数族采用官方重建方式中的精确 generic 参数
`(11/100,3/25,13/100)`；特殊端点应按其对应的 Xiao 高对称标签另行查询。

## 验证结果

- Python 单元测试：26/26 通过。
- Mathematica 源码接口测试：通过。
- Mathematica 安装后全新 Kernel 测试：通过。
- 全库逐条验证：`PASS`，67,475 条，失败 0。
- Xiao nonsymmorphic 标记冲突：0。
- nonsymmorphic：18,801 条。
- symmorphic：48,674 条。

全库验证检查标签完整性、`M_g^T A_g=s_g I`、`Q_g` 的半量子化、`L_B`
不变性、graded 群闭包，以及遗忘 grading 后的群同态一致性。

## 文件与哈希

- 完整主数据库：`full_database/SSGReciprocalDatabase.full.json`
  (`SHA-256 794f585cf9f37e1af59e19b975d2af94ba9754459b8f49f0594f540b6e287387`)
- O(3) 数据源：`official_sources/iso_ir/XiaoO3RepresentationSource.json`
  (`SHA-256 43afe9de18d4af23f92a18835bce8a3aa2103803a2fd52f3d5cc17ab345df27c`)
- 分片索引：`SSGReciprocalDatabase/Data/Reciprocal/metadata.json`
  (`SHA-256 d1128c72b6b342d86c5f3ed9893d47b420a5d9ba14fb68fa8bf1c95fbeb77de6`)
- 验证记录：`SSGReciprocalDatabase/Data/SSGReciprocalDatabaseValidation.json`
  (`SHA-256 4d9fc571ec2ffd30be838fee2cb39ae645dd0df4459e0bc30e2afb09296451da`)

## Mathematica 调用

```wl
<< "SSGReciprocalDatabase`"

Length[SSGReciprocalDatabaseLabels[]]
SSGReciprocalDatabaseStatus[]

getSSGReciprocalData["N6.9.19"]
getSSGNonsymmorphic["N6.9.19"]
getSSGLB["N6.9.19"]
SSGReciprocalGenElem["N6.9.19"]
SSGReciprocalGroupElements["N6.9.19"]
SSGGradedReciprocalGroupElements["N6.9.19"]
getSSGReciprocalGenTab["N143.10.1"]
showSSGReciprocalGenTab["N143.10.1"]
```

显式 `Get`（即 `<<`）会先清除程序包旧的公开与私有定义，再重新载入，行为与
`SpaceGroupIrep` 一致；`Needs` 仍用于首次按需载入。新表格固定列出三个母晶格
平移 `T1,T2,T3` 和全部选定点群生成元，点群名称来自 `SpaceGroupIrep` 的
Jones-symbol 数据表。

Paclet 已安装到：

- `/Users/wpy/Library/Wolfram/Applications/SSGReciprocalDatabase`
- `/Users/wpy/Library/Mathematica/Applications/SSGReciprocalDatabase`

## 科学状态

以上结论是数据库完整性和代数一致性的机械验证。按照项目的独立审稿规则，
理论新颖性、物理解释和投稿可靠性的最终科学判断仍标记为
`BLOCKED_PENDING_INDEPENDENT_SCIENTIFIC_REVIEW`，等待导师或独立审稿人确认。
