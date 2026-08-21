# 输入与输出参考

## 输入范围

- UTF-8 JSON 文件；
- 2～8 个因子；
- 每个因子 2～10 个互不重复的字符串水平；
- 因子名称唯一且不能使用 `case_id`；
- `strength` 仅支持 `2`；
- `mode` 支持 `auto`、`orthogonal`、`pairwise`，默认 `auto`。

## 最小输入模板

```json
{
  "factors": [
    {
      "name": "浏览器",
      "levels": ["Chrome", "Firefox"]
    },
    {
      "name": "网络",
      "levels": ["Wi-Fi", "5G"]
    }
  ]
}
```

仅在需要覆盖默认值时添加：

```json
{
  "mode": "pairwise",
  "strength": 2,
  "factors": []
}
```

## 模式选择

- `auto`：默认；优先严格 OA，无法匹配时降级 pairwise。
- `orthogonal`：必须使用严格 OA，无法匹配时报错。
- `pairwise`：直接生成两两覆盖表。

不同因子水平数不一致时无法使用当前等水平严格 OA，`auto` 会正常降级。

## 输出核对

JSON 结果至少核对：

- `method`；
- `case_count`；
- `coverage.coverage_rate == 1.0`；
- `coverage.uncovered_combinations` 为空；
- `warnings`；
- 使用严格 OA 时，`orthogonal_array.validation_passed == true` 且包含来源 URL。
