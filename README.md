# 组合测试表生成器

一个可离线运行、结果确定的命令行工具。它根据自定义因子和水平生成两两覆盖（pairwise covering array）测试 Case 表，并在输出前独立验证覆盖率。

当前版本为 **v0.1.0**。它实现 JSON 输入、`pairwise` 模式、覆盖率验证，以及 JSON、Markdown、CSV 输出。严格正交表、业务约束和自然语言输入不在本版本范围内。

## 环境要求

- Python 3.11 或更高版本
- 无第三方运行时依赖

## 快速开始

直接在项目根目录运行：

```powershell
python -m combinatorial_test_table_generator `
  --input examples/refund_factors.json `
  --format markdown `
  --output case_table.md
```

也可以安装为命令行程序：

```powershell
python -m pip install .
combinatorial-test-table-generator `
  --input examples/refund_factors.json `
  --format json `
  --output case_table.json
```

省略 `--output` 时，结果写入标准输出。`--format` 可取 `json`、`markdown` 或 `csv`，默认值为 `json`。

## 输入格式

v0.1 接受 UTF-8 JSON 文件，支持 2～8 个因子，每个因子支持 2～10 个互不重复的字符串水平：

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

`mode` 和 `strength` 可省略；v0.1 分别按 `pairwise` 和 `2` 处理。输入 `auto` 或 `orthogonal` 会得到中文错误说明，这两种模式计划在 v0.2 提供。

## 输出说明

JSON 输出包含：

- 生成方法与 Case 数；
- 应覆盖、已覆盖和未覆盖的两两组合；
- 覆盖率；
- 按原始因子顺序排列的测试 Case；
- 为后续严格正交表版本预留的 `orthogonal_array` 字段。

Markdown 会输出生成摘要和 Case 表；CSV 只输出 Case 表。两种表格格式的第一列均为 `case_id`。

## 生成策略

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
- `mode` 或 `strength` 不受 v0.1 支持。

命令行输入错误返回退出码 `2`，内部生成错误返回退出码 `1`。

## 运行测试

测试使用 Python 标准库 `unittest`，无需额外安装依赖：

```powershell
python -m unittest discover -s unit_tests -v
```

测试覆盖输入校验、混合水平数、v0.1 上限（8 个因子且每个 10 个水平）、结果确定性、未覆盖组合报告、三种输出格式和命令行文件写入。

## 版本边界

- v0.1：两两覆盖核心（当前版本）
- v0.2：内置并验证严格正交表，提供 `auto` 和 `orthogonal` 模式
- v0.3：业务约束
- v0.4：Codex Skill 包装

完整需求和后续版本计划见 [需求规格说明书.md](./需求规格说明书.md)。
