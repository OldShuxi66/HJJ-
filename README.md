# HJJ — Codex 桌宠合集

这是一个适用于 Codex Desktop 自定义宠物功能的社区桌宠合集。当前包含 HJJ 和另外四款像素风桌宠；每款桌宠都是独立的 Codex v2 资源，可以单独安装，也可以一次安装全部桌宠。

## 桌宠列表

| ID | 名称 | 预览 |
| --- | --- | --- |
| `hjj` | HJJ | [动作总览](assets/hjj-contact-sheet.png) |
| `afro-suit-pet` | 爆炸头西装桌宠 | [静止](assets/pets/afro-suit-idle.webp) / [拖动](assets/pets/afro-suit-drag.webp) |
| `green-horse-rider-pet` | 绿马骑士桌宠 | [静止](assets/pets/green-horse-idle.webp) / [拖动](assets/pets/green-horse-drag.webp) |
| `muscle-black-shirt-pet` | 健身肌肉桌宠 | [静止](assets/pets/muscle-idle.webp) / [拖动](assets/pets/muscle-drag.webp) |
| `teal-hair-pet` | 青发桌宠 | [静止](assets/pets/teal-hair-idle.webp) / [拖动](assets/pets/teal-hair-drag.webp) |

## 安装

安装脚本不需要 Python，只会把所选桌宠的 `pet.json` 和 `spritesheet.webp` 复制到 Codex 的宠物目录。已有不同版本时，脚本会先备份旧目录，不会删除其他桌宠。

### Windows

在仓库根目录打开 PowerShell：

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -PetId hjj
```

把 `hjj` 换成上表中的其他 ID 即可；安装全部桌宠：

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -All
```

### macOS / Linux

```bash
chmod +x ./install.sh
./install.sh hjj
```

安装全部桌宠：

```bash
./install.sh --all
```

如果设置了 `CODEX_HOME`，脚本使用 `$CODEX_HOME/pets/`；否则使用默认的 `~/.codex/pets/`。安装后重新打开 Codex，或刷新 Pets 设置，再选择对应桌宠。

### 手动安装

把 `pets/<桌宠ID>/` 整个目录复制到：

```text
$CODEX_HOME/pets/<桌宠ID>/
```

每个目录只需要以下两个运行文件：

```text
pet.json
spritesheet.webp
```

## 文件结构

```text
.
├── pets/                         # 每款桌宠一个独立目录
│   ├── hjj/
│   ├── afro-suit-pet/
│   ├── green-horse-rider-pet/
│   ├── muscle-black-shirt-pet/
│   └── teal-hair-pet/
├── assets/                       # README 预览图，不是安装必需文件
├── scripts/                      # HJJ 图集构建工具
├── third_party/nai-wa/           # HJJ 构建所需的上游素材及许可说明
├── verification/                 # 图集结构校验记录
├── install.ps1
├── install.sh
├── LICENSE                       # MIT：代码、脚本、文档和配置
└── ASSET-LICENSE.md              # CC BY 4.0：项目美术资产
```

HJJ 的构建脚本仍然只负责 HJJ 图集；其他桌宠已经提供最终可安装图集，不需要运行 HJJ 构建器。图集规格为 8 列 × 11 行、单格 192 × 208 像素、总尺寸 1536 × 2288、RGBA WebP，并带有 `spriteVersionNumber: 2`。

## 许可证与发布前检查

- `scripts/`、安装脚本、文档和配置：MIT，见 [LICENSE](LICENSE)。
- 项目原创或有权授权的桌宠美术、精灵图和预览图：CC BY 4.0，见 [ASSET-LICENSE.md](ASSET-LICENSE.md)。
- Nai-wa 上游素材继续遵守其原有许可和署名要求，见 [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md)。
- 由人物照片生成的桌宠还可能涉及肖像权、隐私权或其他人格权；公开上传前，请确认你有权公开这些照片对应的形象和改编作品。许可证不会自动授予这些额外权利。

欢迎通过 Issue 和 Pull Request 提交新的桌宠或改进。协作规则见 [CONTRIBUTING.md](CONTRIBUTING.md)。
