# Interactive Intake

Use this guide when the user asks for an account benchmark but has not supplied the structured
fields a report call needs.

## Product Posture

Assume the user may only know their business question, not the TT4B reporting schema. Translate
natural language into the minimum benchmark request, then fill defaults where safe.

Good intake feels like:

```text
User: 帮我看看我今天这个广告好不好
Assistant: 可以。我需要先定位账号和要看的对象。请给我 ADV ID，以及你要看的对象是 Campaign、Ad Group 还是 Ad；如果你只有一个广告 ID，也可以直接发给我。
```

For broad account questions, do not force the user to know object IDs before seeing value:

```text
User: 帮我盘一下过去 7 天我的账户表现怎么样
Assistant: 可以。我会先看账号近 7 个完整自然日的 Campaign 总览，再用同样 7 天内账号
Campaign 作为 benchmark。你把 ADV ID 发我；如果你没有指定对象，我会先按消耗最高的
有消耗 Campaign 作为 benchmark 对象，并在结果里说明我选了哪一个。
```

If the eligible sample is too small, offer to extend the benchmark window:

```text
这次同窗口 benchmark 的有效样本量偏少。为了让结论更稳，我可以补充拉近 30 天同粒度
Campaign 作为 benchmark。你把 ADV ID 发我；如果你没有指定对象，我会先按消耗最高的
有消耗 Campaign 作为 benchmark 对象，并在结果里说明我选了哪一个。
```

Do not ask the user to fill every possible field up front. Ask for the smallest missing set that
blocks a read-only report.

## Request Modes

| User request shape | Interpretation | Next action |
|---|---|---|
| Has advertiser ID + entity type + object ID | Complete single-object benchmark | Proceed |
| Has advertiser ID + asks "account performance" / "账户表现" | Mandatory account overview benchmark mode | Pull same-grain account list, auto-pick a primary benchmark target, then render Benchmark scope/table/verdict in the same response; account totals/top movers are supplements only |
| Has advertiser ID + vague "看广告好不好" | Missing target object | Ask target type/object, or offer to pick one cost-active object |
| Has object ID but no type | Ambiguous entity grain | Ask whether it is Campaign, Ad Group, or Ad |
| Has object ID/type but no advertiser | Missing advertiser context | Ask for ADV ID or resolve via account picker if available |
| Asks "随便拿一个测一下" | Test mode | Pull same-grain list sorted by spend, pick one cost-active object, and state the selected ID |
| Asks for many campaigns/ad groups/ads | Multi-row mode | Compute one verdict per row, or ask which single row to inspect |

## Critical vs Defaultable Fields

Ask for these when missing:

- advertiser/account context
- target grain: Campaign, Ad Group, or Ad, unless the user asks for account overview; default
  account overview to Campaign grain
- target object ID/name, unless the user asks for account overview or explicitly allows automatic
  selection

Default these unless the user specifies otherwise:

- analysis window: last 7 complete account-local days
- benchmark window: same length as the analysis window; default to 7 complete days when the
  analysis window is the default 7 days
- cost-active rule: `spend > 0`
- metrics: CPC, CPA, CTR, CVR, CPM, conversions, spend
- statistics: median plus advertiser-facing relative position

## Clarifying Questions

Use at most three questions at a time. Prefer one concise bundle:

```text
可以，我会用账号内历史同粒度数据做 benchmark。还需要你补三点：
1. ADV ID 是多少？
2. 你要看 Campaign、Ad Group 还是 Ad？
3. 对象 ID 是多少？如果你想让我随机挑一个有消耗对象，也可以说“你来挑”。
```

If the user asks for account performance:

```text
可以。我会按 Campaign 粒度看这个账号近 7 个完整自然日，并在同一轮输出
基准范围、核心对比和 基准结论。
如果你没有指定 Campaign，我会默认选近 7 天主 objective bucket 里消耗最高的有消耗
Campaign 作为 benchmark 对象；账号总览和环比只作为补充，不会替代 benchmark。
```

If the user already gave an object ID but not type:

```text
这个 ID 我收到了。它是 Campaign、Ad Group 还是 Ad？TikTok 的数字 ID 不能只靠长度稳定判断类型。
```

If the user gave type/object but not advertiser:

```text
还需要 ADV ID 才能通过报表接口取数。你把 ADV ID 发我，我会默认看近 7 天，并用同样 7 天内同粒度有消耗对象做 benchmark。
```

If the user asks "今天好不好":

```text
可以看，但今天数据可能未完整回流。我建议默认分析昨天或近 7 个完整自然日；如果你坚持看今天，我会标注数据不完整风险。
```

## Inference Rules

- If the user says "campaign" / "计划" / "广告系列", use Campaign grain.
- If the user says "ad group" / "adg" / "广告组", use Ad Group grain.
- If the user says "ad" / "creative" / "素材" / "广告", use Ad grain only when the wording clearly refers to an individual ad or creative.
- Do not infer entity type from numeric ID length or prefix.
- Do not infer advertiser ID from a target object ID unless a verified MCP lookup can resolve it.

## Discovery Mode

If the user wants the assistant to choose a target:

1. Ask or resolve advertiser ID and target grain.
2. Pull a same-grain report for the analysis window sorted by `spend DESC`.
3. Pick the first cost-active entity unless the user gives another selection rule.
4. State the selected object ID/name before showing benchmark results.

Example:

```text
我先按 Ad Group 粒度从近 7 天有消耗对象里选消耗最高的一条作为测试对象：
Ad Group 123... / example_name。下面用同样 7 天内有消耗 Ad Groups 作为 benchmark。
```

## Account Overview Mode

Use this mode when the user asks how the account performed without naming one object.

1. Resolve advertiser ID.
2. Default to Campaign grain unless the user asks for Ad Group or Ad.
3. Pull the analysis-window same-grain list sorted by `spend DESC`.
4. Compute account totals, active object count, top spend objects, and objective buckets as
   supporting context only. Do not final-answer at this step.
5. Split mixed objectives into buckets. Do not compute one blended CPA/CVR/CPM verdict across
   incompatible objectives.
6. Select a primary benchmark target without asking first:
   - If the user named a target, use it.
   - Otherwise pick the highest-spend cost-active object in the dominant objective bucket.
7. State the selected Campaign / AdGroup as a linked object name before the benchmark result when
   link fields are available. For Ad grain, state the selected object as plain text by design.
   Otherwise use the object name or `Unknown name` with a partial-link disclosure only when a
   Campaign / AdGroup link field is missing.
8. Compute and render the literal sections `基准范围`,
   `核心对比`, and `基准结论` in the same response.

Do not compute one benchmark verdict for a merged account aggregate. The account overview is a
summary plus a mandatory single-object or objective-bucket benchmark. Benchmark verdicts remain
single-object and same-grain.

Do not finish account overview mode with only account totals, campaign drivers, key Campaigns, or
WoW trend. If the benchmark pool cannot be pulled or has no eligible rows, label the result as
`Benchmark blocked（Benchmark 受阻）` or `Partial benchmark（部分 Benchmark）` and explain the
blocker instead of implying a benchmark conclusion.

## Final Confirmation Pattern

Before pulling reports, briefly restate the resolved request:

```text
我会读取 ADV 725... 的 Ad Group 185...，分析窗口为 2026-06-01 到 2026-06-07，
benchmark 为同样 7 天内同账号有消耗 Ad Groups。这个流程只读，不会修改广告。
```

For account overview:

```text
我会读取 ADV 725... 近 7 个完整自然日的 Campaign 总览，并在同一轮自动选择主
objective bucket 里消耗最高的有消耗 Campaign 做 Account benchmark。这个流程只读，
不会修改广告。
```

For read-only report pulls, this restatement is enough; do not require a write-action confirmation.
