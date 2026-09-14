# 0.8.0 构建与验证记录

日期：2026-09-14。范围：已有倒空间操作数据的带反幺正分级磁群识别，不修改论文，不修改原始 O(3) 表示来源。

## 完成情况

- 已匹配标签：67,475 / 67,475；未匹配：0。
- 不同输入操作证书：3,953；不同 BNS 磁群类型：1,136。
- 标签类型计数：I 5,535；II 27,647；III 27,549；IV 6,744。
- 旧普通空间群接口保留，另提供显式 family group 接口。
- 新增磁群识别与输入/标准操作对应表，保留所有 antiunitary 标记。

## 验证

1. `validate_magnetic_space_groups.py`：PASS；完整证书逐项精确重放，加上全部标签与原始操作集绑定及 family 投影核查；295.885 秒。
2. `python3 -m unittest test_magnetic_space_groups test_standard_space_groups`：7 项 PASS。
3. `test_magnetic_space_groups.wl`：9 项 PASS。
4. `test_ssg_database.wl`：PASS，原查询覆盖数与跨空间群样例保持正常。
5. `test_standard_space_groups.wl`：PASS，原普通群查询兼容。
6. `test_installed_magnetic_database.wl`：在 `/tmp/ssg080-wolfram-install` 实际执行 PacletInstall，安装、加载、版本、磁群/family 查询和表格均 PASS。没有改动用户现有的 Wolfram 安装目录。
7. ZIP 中全部 491 个文件逐字节哈希比对 PASS。

## 标准数据例外

`audit_magnetic_reference.py` 检查全部 517 个 type-IV 标准条目。spglib 2.7.0 的 UNI 282、284 二进制操作集与其官方磁 Hall 源表给出的幺正子群类型不一致。仅这两项改用官方磁 Hall 生成元和普通 Hall 182 重建；闭合性与目标类型检查通过，并记录于各证书。8 个标签使用该来源。上游尚未确认这一问题，不能把本地核查称为上游勘误。

本结果覆盖数据库已保存的参数代表，不额外证明连续参数所有特殊值下的分类。这里的测试是算法与数据一致性验证，不替代独立科学审稿。

## 安装包

`dist/SSGReciprocalDatabase-0.8.0.paclet`

SHA256：`cddf03ed2d156695f63ec7402739aec64b4c4ac3a91090399ac5caa4529ff985`

采用单一版本目录的归档布局，避免把 Data 误识别为 paclet 根目录。未发布到 GitHub。
