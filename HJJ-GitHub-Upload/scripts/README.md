# 构建脚本说明

这些脚本只用于生成或更新图集，不参与 Codex 运行时。依赖 Python 3.9+ 和 Pillow：

    python -m pip install -r scripts/requirements.txt

## 基础图集构建器

hjj_pet_builder.py 接收一张 HJJ 分镜图、一张 Nai-wa v2 精灵图，并输出宠物图集和预览文件：

    python scripts/hjj_pet_builder.py \
      --storyboard /path/to/hjj-storyboard.png \
      --nai-wa-sheet third_party/nai-wa/spritesheet.webp \
      --output-dir build/base

## 跑步行融合构建器

hjj_fused_running_builder.py 复用基础图集中的其他动画行，并从 4 列 × 2 行的跑步参考图生成左右跑步行：

    python scripts/hjj_fused_running_builder.py \
      --base-sheet /path/to/base-spritesheet.webp \
      --running-reference /path/to/running-reference-4x2.png \
      --output-dir build/fused-running

原始 HJJ 分镜图和中间生成素材没有纳入公开包。请使用你有权公开和改编的输入图像；上游 Nai-wa 图集的使用须保留其 CC BY 4.0 署名。
