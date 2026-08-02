# veusz-plot — Veusz 科学绘图自动化 Agent Skill

用开源软件 **Veusz**（Origin 的开源替代品）把数据自动画成出版级科学图。
脚本可复现、可批量导出 PNG/PDF/SVG/EPS/TIFF/EMF，覆盖 16 种图型。

Automate publication-quality scientific plotting with Veusz — the free, open-source Origin alternative.

## 依赖 / Dependencies

- **Veusz 4.x**：官方免费，下载 https://veusz.github.io/download/
  - Windows 绿色版自带 Python + Qt + numpy，**无需单独安装 Python**（pip 源码安装会因缺 qmake 而失败，建议用绿色版）
- 下文以 Windows 为例，`<veusz-exe>` 指 Veusz 可执行文件路径

## 运行方式 / How to run

Veusz 文档脚本是 **Python 语法**，脚本内直接调用预置函数：`Add` / `Set` / `SetData` / `SetData2D` / `SetDataExpression` / `ImportFileCSV` / `ImportFile` / `To` / `Export` / `Save`，并预置 `from numpy import *`。

```powershell
$dir = "输出目录"; $script = "plot.py"
$p = Start-Process -FilePath "<veusz-exe>" `
    -ArgumentList "--export","$dir\out.png","$dir\$script" `
    -PassThru -NoNewWindow `
    -RedirectStandardError "$dir\err.log" -RedirectStandardOutput "$dir\out.log"
$p.WaitForExit(60000)   # --export 渲染完自动退出（ExitCode=0）
```

- 脚本可含多个 `Export()`（PNG/PDF/SVG/... 按扩展名）；报错看 `err.log`（Python traceback）
- **不要用** `veusz --listen`（Windows 绿色版管道 EOF 不退出，会挂死）

## 通用脚本骨架 / Script skeleton

```python
# 1. 数据
SetData('x', arange(0, 10, 0.5))                    # 1D
SetData('y', 5*exp(-0.3*x), serr=0.18)              # 带对称误差
SetData2D('z', Z, xrange=(0,100), yrange=(0,80))    # 2D
ImportFileCSV('data.csv', 'x y_meas (+-) y_fit', linked=False)  # CSV 导入

# 2. 页面与画布
Set('width', '8cm'); Set('height', '6cm'); Set('colorTheme', 'colorbrewer1')
Add('page', name='page1', autoadd=False); To('page1')
Add('graph', name='g1', autoadd=False); To('g1')
Add('axis', name='x', autoadd=False); To('x'); Set('label', 'Time (s)'); To('..')
Add('axis', name='y', autoadd=False); To('y'); Set('label', 'Value'); Set('direction', 'vertical'); To('..')

# 3. 图元：Add('typename', name='p1', autoadd=False) → To('p1') → Set(...) → To('..')

# 4. 图例 / 导出
Add('key', name='key1', autoadd=False); To('key1')
Set('Border/hide', True); Set('horzPosn', 'right'); Set('vertPosn', 'top')
To('/')
Export('out.png', dpi=150)
Export('out.pdf', pdfdpi=150)
```

## 示例 / Examples

`examples/` 内含 **16 种图型的完整脚本 + 输出 PNG**（每种一个 `.py`，运行后在同目录生成同名 `.png`）：

| 图型 | 脚本 | 图型 | 脚本 |
|---|---|---|---|
| 折线/散点/误差棒 | `xy.py` | 矢量场 | `vectorfield.py` |
| 柱状 | `bar.py` | 误差椭圆 | `covariance.py` |
| 箱线 | `boxplot.py` | 极坐标 | `polar.py` |
| 直方图 | `histo.py` | 三元图 | `ternary.py` |
| 函数曲线 | `function.py` | 3D 散点 | `point3d.py` |
| 拟合 | `fit.py` | 3D 曲面 | `surface3d.py` |
| 等高线 | `contour.py` | 多面板 | `grid.py` |
| 热图 | 见 SKILL.md 速查（`image`） | 断裂轴 / 标注形状 | `axisbroken.py` / `label_shape.py` |

运行示例：

```powershell
# 在 examples 目录下
<veusz-exe> --export bar.png bar.py
```

## 完整速查 / Full reference

图型速查、CSV descriptor 语法、3D 结构（`page → scene3d → graph3d → plotter3d`）、颜色/主题/colormap、排查清单 —— 全部在 [SKILL.md](SKILL.md)。
