---
name: combinatorial-test-table-generator
description: 将用户提供的多因子、多水平测试信息整理为结构化数据，并调用组合测试表生成器输出严格正交表或两两覆盖表；适用于需要从测试条件生成 JSON、Markdown 或 CSV 用例表的任务。
metadata:
  short-description: 生成组合测试表
  domain: software-test
---

# 组合测试表生成器

将用户明确提供的因子和水平整理为生成器输入，并生成测试组合。

## 工作边界

- 保留用户给出的因子顺序、名称和水平原文，不擅自改名、合并或删除。
- 不推断业务约束、禁止组合或预期结果。
- 用户询问使用方法时，说明既可以自然语言提供因子和水平，也可以直接提供结构化 JSON。

## 执行流程

1. 从请求或用户指定文件中提取因子、水平、输出格式和模式。
2. 按 [输入与输出参考](references/input-and-output.md) 校验数量、唯一性和模式。自然语言输入无法无歧义转换为 JSON 时，再向用户确认。
3. 从当前加载的 `SKILL.md` 路径确定技能根目录。核心程序必须以技能根目录为工作目录运行，不能假定用户当前工作区已经安装了 Python 包。
4. 将输入和输出放在用户当前任务的工作区或用户指定目录，不要默认写入技能根目录。未指定输入文件名时使用工作区中的 `factors.json`；覆盖已有文件前先确认它属于本次任务。
5. 使用绝对输入、输出路径运行：

   ```powershell
   python -m combinatorial_test_table_generator `
     --input "<输入文件绝对路径>" `
     --format markdown `
     --output "<输出文件绝对路径>"
   ```

6. 默认使用 `auto`：等水平输入匹配已验证 OA 时生成严格正交表，否则降级为 pairwise。只有用户明确要求时才使用 `-o` 或 `-p`。
7. 检查命令退出码、生成方法、覆盖率、警告和输出路径。两两覆盖率必须为 `1.0`；严格 OA 还必须包含 `orthogonal_array` 来源和验证信息。
8. 返回生成文件，并简要说明 Case 数、实际方法、覆盖率和任何降级原因。

## 命令约定

在技能根目录手动零参数运行时，程序使用 `factors.json`、`auto`、Markdown 和 `case_table.md`：

```powershell
python -m combinatorial_test_table_generator
```

常用模式：

```powershell
python -m combinatorial_test_table_generator -a
python -m combinatorial_test_table_generator -o
python -m combinatorial_test_table_generator -p
```

- `-a`：自动模式
- `-o`：严格正交模式
- `-p`：两两覆盖模式

需要机器可读结果时使用 JSON，并显式给出输出文件：

```powershell
python -m combinatorial_test_table_generator `
  --input "<输入文件绝对路径>" `
  --format json `
  --output "<输出文件绝对路径>"
```
