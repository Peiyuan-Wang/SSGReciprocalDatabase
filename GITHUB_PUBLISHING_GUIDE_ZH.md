# SSGReciprocalDatabase GitHub 发布步骤

## 推荐：自动发布脚本

GitHub 不需要每次登录。首次登录或 token 失效后运行一次：

```bash
gh auth login -h github.com -p https -w
```

认证由 GitHub CLI 和 macOS 钥匙串保存，不要把 token 写入脚本或仓库。以后在仓库目录先预检：

```bash
./publish_release.sh 0.8.5
```

确认输出后自动提交指定源码和验证文件、推送当前分支、建立 `v0.8.5` Release 并上传 paclet：

```bash
./publish_release.sh 0.8.5 --publish
```

也可以指定发布说明：

```bash
./publish_release.sh 0.8.5 --publish --notes-file RELEASE_NOTES_0.8.5.md
```

脚本使用 `release-files.txt` 白名单，不会提交完整生成数据库、缓存或 `dist/` 目录；完整数据库只随 paclet 作为 Release asset 上传。脚本会拒绝版本不一致、asset 缺失和已有 staged changes，并能在网络中断后从已有发布提交继续。如果 GitHub 已留下草稿，脚本会比较安装包 SHA-256，补传缺失资源并发布原草稿，不会重复建立 Release。每次运行都会读取 macOS 系统代理：系统代理开启时使用当前代理，关闭时清除终端遗留的代理变量并直连。网络错误不是重新登录可以解决的。

## 发布前说明

完整程序包位于：

```text
dist/SSGReciprocalDatabase-0.8.5.paclet
```

发布前用 `shasum -a 256 dist/SSGReciprocalDatabase-0.8.5.paclet` 核对安装包摘要；正式摘要也会显示在 Release 说明中。

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
git commit -m "Release SSGReciprocalDatabase 0.8.5"
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
gh release create v0.8.5 dist/SSGReciprocalDatabase-0.8.5.paclet --title "SSGReciprocalDatabase 0.8.5" --notes-file RELEASE_NOTES_0.8.5.md
```

GitHub CLI 会从当前默认分支创建 `v0.6.2` tag，并把 paclet 上传为 Release asset。

## 5. 用户安装方法

全新用户可在 Mathematica 中运行下面的一条命令；安装脚本会先建立缺失的用户 paclet 仓库，再下载、安装并加载当前版本：

```wl
Get[URLDownload[
  "https://github.com/Peiyuan-Wang/SSGReciprocalDatabase/releases/download/v0.8.5/InstallSSGReciprocalDatabase.wl"
]]
```

已经下载 `.paclet` 时，使用下面的本地安装形式，以兼容尚未初始化 `Repository` 目录的 Wolfram 环境：

```wl
repo = FileNameJoin[{$UserBaseDirectory, "Paclets", "Repository"}];
If[!DirectoryQ[repo], CreateDirectory[repo, CreateIntermediateDirectories -> True]];
PacletInstall["/absolute/path/SSGReciprocalDatabase-0.8.5.paclet"];
<< "SSGReciprocalDatabase`";
showSSGReciprocalGenTab["N143.10.1"]
```

## 6. 发布后的快速检查

```bash
gh repo view --web
gh release view v0.8.5
```

在一个全新的 Mathematica Kernel 中再运行：

```wl
<< "SSGReciprocalDatabase`"
SSGReciprocalDatabaseVersion
Length[SSGReciprocalDatabaseLabels[]]
showSSGReciprocalGenTab["N143.10.1"]
```

预期版本为 `{0,8,5}`，标签数为 `67475`。
