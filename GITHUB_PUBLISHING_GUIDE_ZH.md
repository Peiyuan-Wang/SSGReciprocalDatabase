# SSGReciprocalDatabase GitHub 发布步骤

## 发布前说明

完整程序包位于：

```text
dist/SSGReciprocalDatabase-0.6.0.paclet
```

它约为 15 MB，SHA-256 为：

```text
3ca94d3a509279656ab68b629c5b20621f56841af03e976f8352ce80010de042
```

建议先发布为 private repository。公开前应确认 ISO-IR 数据、Xiao 标签数据和
`SpaceGroupIrep` 名称表快照的再发布许可与署名要求，再决定仓库许可证。

## 1. 安装并登录 GitHub CLI

```bash
brew install gh
gh auth login
gh auth status
```

不要在命令或仓库文件中填写 GitHub token；使用 `gh auth login` 的交互式登录。

## 2. 在当前目录建立本地 Git 仓库

```bash
cd /Users/wpy/Desktop/ai4s/shangjiao/theory-paper-codex-harness/try/computations/ssg_reciprocal_catalog
git init
git branch -M main
```

完整数据目录约为 558 MB。推荐只把代码、测试、文档和验证摘要提交到 Git，
把完整 `.paclet` 作为 Release asset 发布：

```bash
git add README.md FULL_DATABASE_BUILD_REPORT_ZH.md
git add SSGReciprocalDatabase_UserGuide_EN.md SSGReciprocalDatabase_UserGuide_EN.docx
git add GITHUB_PUBLISHING_GUIDE_ZH.md
git add SSGReciprocalDatabase/PacletInfo.wl SSGReciprocalDatabase/Kernel SSGReciprocalDatabase/Scripts
git add SSGReciprocalDatabase/Data/SSGReciprocalDatabaseValidation.json
git add SSGReciprocalDatabase/Data/XiaoO3RepresentationValidation.json
git add SSGReciprocalDatabase/Data/XiaoO3MultiplicationValidation.json
git add SSGReciprocalDatabase/Data/SpaceGroupIrepRotationNames.json
git add test_*.py test_*.wl validate_rotation_names.py
git commit -m "Release SSGReciprocalDatabase 0.6.0"
```

## 3. 新建远程仓库并推送

把 `YOUR_GITHUB_NAME` 替换为你的 GitHub 用户名：

```bash
gh repo create YOUR_GITHUB_NAME/SSGReciprocalDatabase --private --source=. --remote=origin --push
```

这会从当前本地仓库创建远程仓库并推送 `main`。确认许可后，可在 GitHub 设置中
把仓库改为 public。

## 4. 发布完整程序包

```bash
gh release create v0.6.0 dist/SSGReciprocalDatabase-0.6.0.paclet --title "SSGReciprocalDatabase 0.6.0" --notes "Complete Wolfram Language database for 67,475 Xiao SSG labels."
```

GitHub CLI 会从当前默认分支创建 `v0.6.0` tag，并把 paclet 上传为 Release asset。

## 5. 用户安装方法

用户下载 `.paclet` 后，可在 Mathematica 中运行：

```wl
PacletInstall["/absolute/path/SSGReciprocalDatabase-0.6.0.paclet"]
<< "SSGReciprocalDatabase`"
showSSGReciprocalGenTab["N143.10.1"]
```

## 6. 发布后的快速检查

```bash
gh repo view --web
gh release view v0.6.0
```

在一个全新的 Mathematica Kernel 中再运行：

```wl
<< "SSGReciprocalDatabase`"
SSGReciprocalDatabaseVersion
Length[SSGReciprocalDatabaseLabels[]]
showSSGReciprocalGenTab["N143.10.1"]
```

预期版本为 `{0,6,0}`，标签数为 `67475`。
