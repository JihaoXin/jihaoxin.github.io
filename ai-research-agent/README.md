# AI Research Agent —— 面试题交付物

> 题目:设计并实现一个简单的 AI Research Agent。用户输入一个研究问题(如
> "强化学习是否能够提升代码大模型的推理能力?"),Agent 自动搜索相关资料,
> 输出一份包含主要结论、支持证据和引用来源的简短研究报告。
>
> 本方案复用 ARK 的成熟机制:**DeepResearch → 实验 → Writing** 三段式
> pipeline,引用侧采用 **Chain of Evidence(证据链)** 溯源,配合
> **高/中/低三档置信度路由** 与 **HITL 人工复核**。

## 六问导航

| # | 面试题要求 | 交付物 |
|---|-----------|--------|
| 1 | 任务拆解(≥5 个原子任务,含输入/输出) | [`DESIGN.md`](DESIGN.md) 第 1 节 |
| 2 | 决策边界(哪些步骤不能完全交给 AI) | [`DESIGN.md`](DESIGN.md) 第 2 节 |
| 3 | 置信度路由(高/中/低,写入/复核/拒绝) | [`DESIGN.md`](DESIGN.md) 第 3 节;代码实现见 `citation_checker.py` 的 `route()` |
| 4 | 核心实现:检查报告中的引用是否真实存在 | [`citation_checker.py`](citation_checker.py)(CrossRef + OpenAlex 溯源);[`pdf_citation_audit.py`](pdf_citation_audit.py)(PDF 端到端审计) |
| 5 | 代码审查(≥5 项,含风险说明) | [`CODE_REVIEW.md`](CODE_REVIEW.md) |
| 6 | 测试设计(3 个必测场景) | [`test_citation_checker.py`](test_citation_checker.py);策略说明见 [`DESIGN.md`](DESIGN.md) 第 4 节 |

## Chain of Evidence 四原则

1. **所有 bibtex 由溯源产生**:以 DeepResearch 证据库为 base,去
   OpenAlex / CrossRef 检索,模糊匹配后 pull 回官方 bibtex —— 严禁 LLM
   zero-shot 直接生成 bibtex。
2. **引用必须论证**:正文用某 citation 支持某结论时,做 claim–evidence
   支持性判断(生产环境用 LLM judge,本仓库内置可离线测试的启发式 fallback)。
3. **查无即禁用**:OpenAlex / CrossRef 均检索不到的引用,一律拒绝写入,
   不允许"改写后再用"。
4. **引用不为空**:`verify_report([])` 直接抛 `EmptyBibliographyError`,
   由测试保证。

## 快速开始

```bash
# 审计一份 Markdown 报告(或 .bib 文件)中的引用
python3 citation_checker.py report.md

# 审计一份 PDF 论文的参考文献(需要 pypdf)
python3 pdf_citation_audit.py paper.pdf

# 跑离线测试(全部 mock,不打真实网络)
python3 -m unittest test_citation_checker -v
```

退出码语义:`0` 全部 ACCEPT;`1` 存在需人工复核(HUMAN_REVIEW);
`2` 存在被拒绝的引用(REJECT)。

## 置信度路由速览

| 档位 | 判定 | 动作 |
|------|------|------|
| 高 | 溯源强命中(DOI/标题≥0.95 + 作者年份一致)且支持结论 | 直接写入报告 |
| 中 | 可溯源但有歧义(模糊匹配 0.80–0.95、支持性弱/未知、后端故障) | HITL 通知,人工复核 |
| 低 | 两个后端均查无 / 元数据矛盾 / 摘要与结论矛盾 | 拒绝使用,禁止写入 |

网络失败的 fail-safe 方向:**宁可进人工复核,绝不静默 ACCEPT**。
