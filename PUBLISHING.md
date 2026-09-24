# 上传到 GitHub

本目录的内容就是仓库根目录。上传时要上传本目录中的文件和子目录的内容，不要再套一层 `HJJ-Collection-GitHub-Upload` 文件夹。

## 第一次整理仓库

建议在 GitHub 的 `main`（如果你的默认分支仍叫 `master`，就使用 `master`）上维护一份完整合集：

1. 在仓库首页选择 **Add file → Upload files**。
2. 打开本目录，选中里面的全部内容，拖入上传区；不要选中外层文件夹本身。
3. 确认上传预览中能直接看到 `README.md`、`pets/`、`assets/`、`install.ps1` 和 `install.sh`。
4. 提交信息可以写 `Organize pet collection`，再提交到默认分支。
5. 上传后检查仓库首页是否显示 README，并进入 `pets/` 确认五个桌宠目录都在。

不要把 ZIP 当作仓库唯一内容上传。ZIP 可以作为 GitHub Release 的下载附件，但仓库本身应该展示可阅读的目录结构。

## 日常协作

不要为每个桌宠长期维护一个分支。新增桌宠或修改现有桌宠时，从默认分支创建短期分支，例如：

```text
add-teal-hair-pet
repair-hjj-running
update-install-script
```

完成后通过 Pull Request 合并回默认分支。默认分支始终保持可安装、可阅读；稳定版本再使用 Git tag 或 GitHub Release 标记。

上传前请确认没有 `scripts/__pycache__/`、`.pyc`、密钥、私人照片或未经授权的第三方素材；`.gitignore` 已忽略常见 Python 缓存文件。
