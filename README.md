# 组合测试表生成器

一个可离线运行、结果确定的命令行工具。它根据自定义因子和水平优先生成严格正交表，无法匹配时生成两两覆盖（pairwise covering array）测试 Case 表，并在输出前独立验证覆盖率。

当前版本为 **v0.3.0**。核心生成器实现 `auto`、`orthogonal`、`pairwise` 三种模式、内置且已验证的 Sloane OA 参考表、覆盖率验证，以及 JSON、Markdown、CSV 输出；v0.3 增加 Codex Skill，将用户明确提供的因子和水平整理为 JSON 后调用核心程序。

## 环境要求

- Python 3.11 或更高版本
- 无第三方运行时依赖

## 快速开始

项目读取根目录的 `factors.json`，作为默认输入文件。因此可以直接运行：

```powershell
python -m combinatorial_test_table_generator
```

默认行为是：读取 `factors.json`、使用 `auto` 模式、生成 Markdown，并保存为 `case_table.md`。

指定其他输入和格式：

```powershell
python -m combinatorial_test_table_generator `
  --input examples/refund_factors.json `
  -p `
  --format csv
```

以上命令会强制使用两两覆盖，并自动输出到 `case_table.csv`。

也可以安装为命令行程序：

```powershell
python -m pip install .
combinatorial-test-table-generator
```

命令行默认值和简写：

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--input` | `factors.json` | JSON 输入文件 |
| `--format` | `markdown` | 可选 `json`、`markdown`、`csv` |
| `--output` | `case_table.<格式>` | 使用 `--output -` 可写入标准输出 |
| 模式 | `auto` | `--mode a/o/p`，或直接使用 `-a/-o/-p` |

完整模式名仍可使用，例如 `--mode orthogonal`。

## 输入格式

接受 UTF-8 JSON 文件，支持 2～8 个因子，每个因子支持 2～10 个互不重复的字符串水平：

```json
{
  "mode": "pairwise",
  "strength": 2,
  "factors": [
    {
      "name": "浏览器",
      "levels": ["Chrome", "Firefox", "Edge"]
    },
    {
      "name": "网络",
      "levels": ["Wi-Fi", "5G"]
    },
    {
      "name": "身份",
      "levels": ["会员", "访客"]
    }
  ]
}
```

`mode` 和 `strength` 可省略，分别按 `auto` 和 `2` 处理。

模式行为：

- `auto`：优先匹配严格 OA，无法匹配时降级为两两覆盖并给出原因；
- `orthogonal`：只允许严格 OA，没有匹配参考表时明确报错；
- `pairwise`：直接生成两两覆盖表。

## 输出说明

JSON 输出包含：

- 生成方法与 Case 数；
- 应覆盖、已覆盖和未覆盖的两两组合；
- 覆盖率；
- 按原始因子顺序排列的测试 Case；
- 严格 OA 的数组编号、参数、SHA-256 和 Sloane 来源；未使用时该字段为 `null`。

Markdown 会输出生成摘要和 Case 表；CSV 只输出 Case 表。两种表格格式的第一列均为 `case_id`。

## 严格正交表

v0.2 内置规格说明书列出的 10 张 Sloane OA 原表，位于 `reference_data/orthogonal_arrays/`。`catalog.json` 记录每张表的来源 URL、下载日期、SHA-256、参数和本地验证结果。

程序使用 OA 前会再次检查文件哈希并验证：

- 矩阵行数、列数与声明一致；
- 所有值位于 `0～s-1`；
- 任取两列，每种水平组合的出现次数完全相同；
- 取前 N 列映射用户因子后仍满足严格正交性和 100% 两两覆盖。

需要重新获取原表时，手动执行：

```powershell
python scripts\fetch_orthogonal_references.py
```

下载或验证失败的文件不会登记为可用参考表。

## 两两覆盖生成策略

生成器先枚举所有必须覆盖的两因子水平组合，再反复选择排序最靠前的未覆盖组合作为种子，以确定性贪心方式补全一行。完成覆盖后，它会移除不影响 100% 覆盖率的冗余行。

该策略保证：

- 任意两个因子的每一对水平至少出现一次；
- 相同输入得到相同输出；
- 支持不同因子拥有不同数量的水平；
- 不承诺 Case 行数达到数学意义上的绝对最少。

每次生成完成后，独立验证器都会重新计算覆盖率。若覆盖率不是 100%，程序会按内部错误退出，不会输出不完整结果。

## 输入校验

程序会对以下问题给出中文错误：

- JSON 语法错误或顶层不是对象；
- 因子数量超出 2～8；
- 因子名称为空、重复或使用保留字段 `case_id`；
- 水平数量超出 2～10；
- 水平为空、重复或不是字符串；
- `mode` 或 `strength` 不受当前版本支持；
- 强制严格 OA 时找不到匹配或已验证参考表。

命令行输入错误返回退出码 `2`，内部生成错误返回退出码 `1`。

## 业务场景边界

生成器不理解具体业务，也不判断哪些组合不成立。输入中的每个水平默认都需要参与组合。

如果某个水平一旦出现，预期结果便与其他因子完全无关，应由业务方先将它拆成一条独立用例，再从组合输入中移除该水平。例如“订单状态=未送达”会直接结束退款流程时：

```text
独立用例：订单状态=未送达，其他因子=N/A
组合输入：订单状态仅保留仍需与其他因子组合的水平
```

只有确认其他所有因子都不会改变结果时才能这样拆分。程序报告的 100% 覆盖率只针对拆分后的组合空间。

项目不实现 `forbidden_combinations`、场景规则推理或预期结果判断，以保持核心工具通用且可解释。

## Codex Skill

本仓库本身也是可被 Codex 直接发现的 Skill，入口为根目录的 [SKILL.md](./SKILL.md)。它负责：

- 从用户明确提供的描述中整理因子和水平；
- 生成符合输入规范的 JSON；
- 调用核心命令行程序；
- 返回生成方法、覆盖率、降级原因和输出文件；
- 对可能的终止型水平先请求确认，不自行推断业务规则。

核心程序无需 Skill 也能独立运行。Skill 只是输入整理和调用入口，不改变生成算法。Skill 调用核心程序时以本仓库为工作目录，并把本次任务的输入和输出保留在用户当前工作区。

需要保留 GitHub 更新能力时，直接将整个仓库克隆到个人 Codex Skill 目录：

```powershell
git clone `
  https://github.com/d732654719/combinatorial-test-table-generator.git `
  "$env:USERPROFILE\.codex\skills\combinatorial-test-table-generator"
```

该目录同时是完整 Git 工作区和 Skill 目录；更新时在目录中执行 `git pull`。如果 Codex 没有立即发现新 Skill，请重启 Codex。

安装后可在 Codex 中提出：

```text
使用 $combinatorial-test-table-generator，根据以下因子生成 Markdown 测试表……
```

## 运行测试

测试使用 Python 标准库 `unittest`，无需额外安装依赖：

```powershell
python -m unittest discover -s unit_tests -v
```

测试覆盖输入校验、10 张 OA 的本地目录与选择范围、严格正交性、列投影、auto 降级、混合水平数、两两覆盖上限（8 个因子且每个 10 个水平）、结果确定性、三种输出格式和零参数命令行运行。

## 版本边界

- v0.1：两两覆盖核心
- v0.2：内置并验证严格正交表，提供 `auto` 和 `orthogonal` 模式（核心完成版本）
- v0.3：Codex Skill 包装（当前完成版本）

项目不再规划核心业务约束版本；业务场景裁剪由使用者在组合生成前完成。
