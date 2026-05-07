# Card Battle Visual Prototype

React + Babel-standalone 单页可视化原型，用来探索拿破仑战争卡牌对战的画面表现与
战场氛围。**不是**模拟器，也不与 `card-battle-sim/` 共享代码，仅作为视觉/交互方向探索。

## Hypothesis

- 三线战场（左/中/右）+ 油画 / 沙盘 / 纹章三套美术语汇能否让玩家在静帧下就读懂对局节奏。
- 部署、攻击、阵亡的烟雾/火星/闪光动画是否足以表达战场量感而无需 3D。
- 三阵营（法兰西 / 普鲁士 / 俄罗斯）是否在视觉上足够区分（颜色、纹章、卡面风格）。

## How To Run

不需要构建步骤，只需一个静态服务器：

```
cd prototypes/card-battle-visual-prototype
python3 -m http.server 8010
# 浏览器打开 http://localhost:8010/
```

首次加载会从 unpkg 拉取 React 18.3.1、ReactDOM、@babel/standalone 7.29，请保持联网。

## Files

| 文件 | 作用 |
|---|---|
| `index.html` | 入口，加载 React/Babel 与所有 JSX 源文件 |
| `app.jsx` | 顶层 App，定义三个对局组合（法/普、法/俄、普/俄）和 Tweak 面板 |
| `battlefield.jsx` | 战场主视图：三线、单位、动画 |
| `cards.jsx` | 卡牌渲染（油画/纹章/极简三种卡面） |
| `factions.jsx` | 阵营牌库与配色（法兰西/普鲁士/俄罗斯激活；英/奥/西保留为后续素材） |
| `design-canvas.jsx` | 设计画布与背景层（战画/沙盘/地图） |
| `tweaks-panel.jsx` | 右上角的视觉调参面板（背景、色调、卡面、动画速度） |
| `original-inline-prototype.html` | 拆分前的最早版本快照，仅作参考，勿编辑 |
| `.design-canvas.state.json` | 画布临时状态（运行时写入） |

## Status

**进行中（视觉方向探索）。** 目前画面已可演示三种对局组合和实时调参，但：

- 卡牌动作流为脚本化演示，**没有接入** `card-battle-sim/` 的回放 JSON。
- 阵营牌库为占位数据，未与 v0.3B 卡表（每阵营 33 张）保持一致。
- 没有键盘 / 移动端适配。

## Findings (累积更新)

- 三线 + 油画背景在桌面 1280px 下可读性可接受；沙盘风格更适合战略地图态。
- Tweak 面板中"按对局"默认值最方便快速比较，建议保留为默认项。
- _更多发现等到下一次评审时回填。_

## Next Step Options

1. 接入 `card-battle-sim/match_data.json`，让原型直接播 Python 模拟器的真实回放。
2. 继续作为纯视觉探索，不接入回放，作为美术风格 RFC。
3. 归档：如果决定走 KARDS-style HTML viewer（`card-battle-sim/viewer.html`），则保留快照后冻结。

参考迁移计划：`docs/superpowers/plans/2026-05-05-visual-prototype-data-migration.md`
