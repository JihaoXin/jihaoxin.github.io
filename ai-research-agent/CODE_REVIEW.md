# 代码审查报告(Code Review)— Chain-of-Evidence 引用校验模块

- **审查对象**:`citation_checker.py`(1005 行)、`pdf_citation_audit.py`(170 行)
- **审查日期**:2026-08-25
- **审查性质**:对"AI 生成代码"的正式人工审查(面试题第 5 问交付物)
- **审查方式**:逐行通读 + 手工数据流推演(未运行网络请求,未修改任何代码)
- **说明**:文中行号以本次审查时的文件快照为准;代码正在由他人并行修改,行号可能漂移,函数名为准。

---

## 1. 外部 API 错误处理、超时与重试

**【检查项】** 对 CrossRef / OpenAlex 的所有 HTTP 调用是否设置超时、是否有重试与退避、是否区分"确定性否定(404)"与"基础设施故障(超时/5xx)"。

**【在本代码中的检查结果】**
- `CitationChecker._http_get`(约 L396-426)对每个请求设置 `timeout=_HTTP_TIMEOUT_SECONDS`(10 秒),最多重试 `_HTTP_MAX_RETRIES=2` 次,指数退避 `time.sleep(2**attempt)`(1s、2s)。
- 异常契约清晰:HTTP 404 立即抛 `NotFoundError` 且**不重试**(确定性否定,如无效 DOI);其余 `HTTPError`/`URLError`/`TimeoutError`/`OSError` 重试耗尽后抛 `LookupBackendError`。`NotFoundError` 刻意**不是** `LookupBackendError` 的子类(见两个异常类的 docstring),二者在 `verify_one` 中走完全不同的分支:前者记录原因继续降级查询,后者置 `backend_failed=True`。
- `_get_json`(约 L428-435)把非 JSON 响应(`json.JSONDecodeError`)也归为 `LookupBackendError`,避免脏响应被当成"查无此文"。
- 遗留问题:(a) 重试不区分状态码,HTTP 400(请求本身非法)也会白白重试两轮;(b) 收到 429 时不读取 `Retry-After` 响应头,只按固定 1s/2s 退避,退避可能不足;(c) 若 CDN/代理在故障期间对**搜索端点**返回 404(而非 5xx),`verify_one` 步骤 (b) 中 CrossRef 搜索 404 → `need_openalex=True`,OpenAlex 搜索 404 → 仅 `note("OpenAlex search returned 404")`、`backend_failed` 保持 False,最终 `exists=False` 走 LOW/REJECT——一次非常规的基础设施 404 会被误读为"确定不存在"。

**【可能带来的风险】** 网络抖动被误判为"引用不存在",错杀真实引用,报告可信度受损;429 退避不足会加剧被限流。本实现已把绝大多数网络故障隔离到 `LookupBackendError` → HUMAN_REVIEW,主风险面收敛得不错,残余风险集中在"搜索端点异常 404"这一小缝隙。

**【建议/结论】** 基本合格。建议:重试仅针对 429/5xx/超时;429 时优先遵循 `Retry-After`;对**搜索类端点**的 404 按 `LookupBackendError`(而非确定性否定)处理——404 语义上只应属于"按 DOI 取单条记录"这类点查。

---

## 2. 模糊匹配阈值与文本归一化

**【检查项】** 标题模糊匹配的阈值设定、相似度算法选型、归一化流程,是否可能把"另一篇论文"当成"被引论文"(张冠李戴)。

**【在本代码中的检查结果】**
- 双阈值:`title_strong=0.95`(强匹配才可 ACCEPT)、`title_weak=0.80`(低于即视为该候选不存在)。构造函数校验 `0 <= title_weak <= title_strong <= 1`,非法配置直接 `ValueError`,这点做得对。
- `_similarity` 用 `difflib.SequenceMatcher` 对 `_normalize` 后的字符串(NFKD 去变音符、小写、标点转空格、空白折叠)做**字符级** ratio。区间 [0.80, 0.95) 只判 `exists=True` 但路由 HUMAN_REVIEW(`verify_one` 步骤 (c) 的 `note("fuzzy title match only ...")`),不会直接采纳,方向正确。
- **发现一处高风险行为**:`route_verification` 与 `verify_one` 中的强匹配条件是 `year_consistent is not False and author_consistent is not False`——即年份/作者**缺失(None)时视同"未矛盾"**。而 `route_verification` 的 docstring 写的是 "(title/year/author agree)",实现是"不 disagree",文档与实现不一致。后果:一条只解析出标题(`parse_reference_entry` 对非常规格式经常解析不出作者/年份)的引用,只要与**任何**候选的标题字符相似度 ≥0.95,就自动 HIGH/ACCEPT,并拉取该候选的 BibTeX。同名或几乎同名的不同论文(综述类短标题、会议版 vs arXiv 预印本)会被张冠李戴。
- 次要问题:`best_candidate()` 仅按 `max(candidates, key=lambda c: c["similarity"])` 取最大值,多个候选同分(同名论文、同文多版本)时取列表序中第一个,选择是任意的,且不参考年份/作者做 tie-break。

**【可能带来的风险】** 阈值本身不算松,但"缺失元数据 = 不矛盾"这一放行逻辑让强匹配退化为"仅标题匹配",幻觉引用或错误版本可能混入正文并携带看似正规的官方 BibTeX——这是学术不端级别的风险,且比"引用不存在"更隐蔽(存在、格式正确、内容错张)。

**【建议/结论】** **需要修改(高优先级)**。当 `citation.year` 与 `citation.authors` 均缺失时,即使相似度 ≥0.95 也应降级为 MEDIUM/HUMAN_REVIEW(至少要求年份、作者之一佐证才可 ACCEPT);`best_candidate` 同分时用年份/首作者做次级排序;并把 docstring 与实现对齐。

---

## 3. URL 参数编码与注入

**【检查项】** 拼 URL 时用户可控内容(标题、DOI 均来自被审报告,应视为不可信输入)是否正确转义,能否借构造输入改变请求路径或打到非预期端点。

**【在本代码中的检查结果】**
- 标题查询:`verify_one` 步骤 (b) 用 `urllib.parse.quote(citation.title)` 后拼入 `?query.bibliographic={query}&rows=5` 与 OpenAlex `?search={query}`。`quote` 默认 `safe="/"`,`&`、`=`、`#`、`?` 都会被转义,标题里的 `&rows=1000` 或 `#fragment` 无法注入额外参数;主机名写死在模块常量 `CROSSREF_WORKS_API` / `OPENALEX_WORKS_API`,无法改写目标主机。这部分是安全的。
- **DOI 路径存在缝隙**:`urllib.parse.quote(citation.doi, safe="/")` 保留 `/` 是 CrossRef 路径式 DOI 的标准做法,但代码从未校验 DOI 形状。`_DOI_IN_TEXT_RE` 只要求 `10.` 开头加非空白(`10\.\S+`),因此报告里一条恶意构造的 "DOI" 如 `10.1/../../members/123` 会被原样拼进 `f"{CROSSREF_WORKS_API}/{doi_path}"`,`urllib` 不做客户端路径规范化,服务端解析 `../` 后请求会落到 `api.crossref.org` 上**非 works 的其他端点**。同样的 DOI 还会被用于 BibTeX transform 请求(步骤 (e))。
- `parse_bibtex` 提取的 `doi` 字段同样未做形状校验即入库。

**【可能带来的风险】** 目标 API 是只读公共服务,当前危害上限是"打到同主机非预期端点、返回被误当作元数据解析";但这是典型的注入面,一旦未来把常量换成带鉴权的内网聚合服务,`../` 遍历就会变成实打实的越权访问。恶意标题破坏请求的风险已被 `quote` 挡住。

**【建议/结论】** 查询参数编码合格;**DOI 必须先做形状校验**(如 `^10\.\d{4,9}/[^\s]+$`,并显式拒绝含 `..` 分段的输入)再拼 URL;查询串建议改用 `urllib.parse.urlencode` 统一构造,消除手拼。

---

## 4. Fail-safe 方向性(网络失败绝不放行)

**【检查项】** 任何网络/后端失败路径下,引用是否绝无可能被 ACCEPT;失败时是走 HUMAN_REVIEW 还是被静默放过或误杀。

**【在本代码中的检查结果】**
- `route_verification` 的规则 1 把 `backend_failed` 放在**最高优先级**:只要任何一次溯源查询抛过 `LookupBackendError`,即便随后 OpenAlex 找到了 ≥0.95 的强匹配,也强制 MEDIUM/HUMAN_REVIEW("backend unavailable, needs retry/human"),既不 ACCEPT 也不 REJECT。逐路径核对:`verify_one` 中 DOI 解析(步骤 a)、CrossRef 标题搜索、OpenAlex 搜索(步骤 b)三处 `except LookupBackendError` 都置 `v.backend_failed = True`。**确认不存在任何从网络失败通往 ACCEPT 的路径**。
- `Verification` 的字段默认值即 `Confidence.MEDIUM` / `Action.HUMAN_REVIEW`——即使未来有人加了提前 return 忘记路由,默认态也是安全侧。这是一个好的防御性设计。
- REJECT 仅发生在 `exists=False and not backend_failed`,即所有后端都给出确定性回答之后,故障不会导致误杀(第 1 节所述"搜索端点 404"缝隙除外)。
- **一处偏离**:步骤 (e) 的 BibTeX transform 请求失败(`except (NotFoundError, LookupBackendError)`)被注释标为 non-fatal,仅 `note("bibtex retrieval failed (non-fatal); regenerate before final build")`,不置 `backend_failed`,该引用仍以 HIGH/ACCEPT、`bibtex=None` 通过。`route_verification` 不检查 `bibtex` 字段,`ReportAudit.ok` 也不检查。若下游只认 `action == ACCEPT` 就写入报告,会产出一条**没有官方 BibTeX 的已接受引用**,与模块第一原则"Provenance-only BibTeX"相抵触(下游若为补齐而让 LLM 生成 bibtex,恰好踩中被严禁的行为)。

**【可能带来的风险】** 主链路的 fail-safe 方向性正确,静默放行未验证引用的核心风险已被挡住;残余风险是"ACCEPT 但无 bibtex"这一中间态可能被下游误用。

**【建议/结论】** 主体通过。建议:BibTeX 拉取失败时要么降级 HUMAN_REVIEW,要么在 `ReportAudit.ok` 中增加"所有 ACCEPT 均携带非空 `bibtex`"的断言,把第一原则闭环到出口。

---

## 5. 速率限制与 API 礼貌性(mailto / User-Agent)

**【检查项】** 是否按 CrossRef/OpenAlex 的 etiquette 提供可联系的 UA 与 mailto、是否控制请求速率,避免被列入慢速池或封禁。

**【在本代码中的检查结果】**
- `_http_get` 发送了规范的 UA:`ai-research-agent-citation-checker/1.0 (https://github.com/jihaoxin; mailto:{self.mailto})`,两家服务都认 UA 中的 mailto,能进 polite pool;`mailto` 通过构造参数注入且 docstring 明确提醒公开部署不要放个人数据——设计意识到位。
- **但默认值是 `research-agent@example.com`**(`__init__` 参数默认),而 CLI 入口 `main` 直接 `CitationChecker()` 使用默认值,没有任何命令行开关可覆盖。`example.com` 是保留占位域,等于向 CrossRef 提供了一个不可达联系方式,礼貌池资格存疑,极端情况下会被视为不良客户端。
- 无任何主动限速:`verify_report` 顺序循环,每条引用最多约 4 个请求(DOI 点查 + CrossRef 搜索 + OpenAlex 搜索 + BibTeX transform),请求间零间隔;收到 429 只按固定 1s/2s 重试(见第 1 节),不读 `Retry-After`。也没有跨引用/跨运行的缓存,同一篇被多处引用会重复打 API。

**【可能带来的风险】** 大型参考文献列表(如 100+ 条)一次审计即数百请求,可能触发 CrossRef/OpenAlex 限流甚至封禁,导致溯源全线不可用——届时所有引用统统落入 HUMAN_REVIEW(方向安全,但流水线实质瘫痪)。

**【建议/结论】** 需改进。上线前:把 mailto 默认值改为真实角色邮箱或强制显式传入(为空则拒绝启动);加最小请求间隔(如 100ms)与 `Retry-After` 遵循;对 (title, doi) 键加进程内 memo 及可选磁盘缓存。

---

## 6. 空输入与边界条件

**【检查项】** 空引用列表、空/缺失标题、缺 DOI、缺 abstract、空 PDF 书目等边界是否会静默通过或崩溃。

**【在本代码中的检查结果】**
- 空引用列表:`verify_report` 开头即 `raise EmptyBibliographyError`,`main` 捕获后 stderr 报错并退出码 2;PDF 侧 `audit_pdf` 复用同一守卫,`find_references_section` 找不到书目标题返回空串 → `split_numbered_entries` 返回 [] → 同样触发。**"引用列表不为空"的硬性要求在两条 CLI 链路上都闭环了**,不会静默通过。
- 无标题无 DOI:`verify_one` 记录 "citation has neither DOI nor title; provenance impossible",跳过全部查询,`exists=False` → LOW/REJECT,不崩溃。
- `_similarity` 对 `None`/空串直接返回 0.0;缺 abstract 时 `supports_claim` 保持 `None`,路由为 MEDIUM("claim support unknown (abstract unavailable)"),不会因缺摘要放行——方向正确。
- `format_audit_table` 对零行输入有 `if rows else len(headers[i])` 守卫,不会在 `max()` 上崩。
- 边界缝隙:(a) `split_numbered_entries` 要求 `[n]` 序列**严格从 [1] 开始连续递增**,双栏 PDF 抽取乱序或书目从 [2] 起编号时会得到空/截断列表——好在结果是 EmptyBibliographyError 阻断发布而非放行,安全方向;(b) `pypdf.PdfReader` 对损坏 PDF 抛出的库异常在 `pdf_citation_audit.main` 中未捕获(只捕获了 `FileNotFoundError` 和 `EmptyBibliographyError`),会以 traceback 崩溃退出(见第 11 节退出码问题);(c) `_rebuild_openalex_abstract` 中 `int(pos)` 遇到畸形数据(非数值 position)会抛未捕获的 `ValueError` 直接击穿 `verify_one`。

**【可能带来的风险】** 核心边界(空列表、空字段、缺摘要)处理扎实;残余风险是畸形外部数据/损坏 PDF 造成进程崩溃而非优雅降级,批量流水线中一条坏数据会中断整批审计。

**【建议/结论】** 基本通过。建议在 `verify_one` 外围对"解析外部响应"的代码路径加窄化的 try/except → `LookupBackendError`(畸形响应 = 后端不可信 = HUMAN_REVIEW),PDF CLI 捕获 `pypdf` 异常并给出明确退出码。

---

## 7. 启发式 support_judge 的能力边界

**【检查项】** 默认 claim-support 判定器的原理性局限是否被认识、是否可能把"词面重叠"误判为"语义支持",以及该误判能否直达 ACCEPT。

**【在本代码中的检查结果】**
- `default_support_judge` 是长度加权的词面包含度(claim 去停用词后的 token 集与 abstract 的交集,按字符长度加权),外加一个"单侧含否定词则减半"的粗糙矛盾信号(`_NEGATION_TOKENS`)。docstring 明确自我标注:这是 dependency-free 的离线 FALLBACK,"A production deployment should inject an LLM-based judge via `CitationChecker(support_judge=...)`"——能力边界的**声明**是到位的。
- **但默认配置下误判可直达 HIGH/ACCEPT,且能通过矛盾样例**。推演:claim = "Method X improves accuracy on ImageNet",abstract = "We show that method X does not improve accuracy on ImageNet"。词面重叠(method/x/accuracy/imagenet,"improves"≠"improve" 无词干归并)加权分约 0.74,否定减半后约 0.37,仍高于 `support_threshold=0.2` → `supports_claim=True` → 强匹配下 HIGH/ACCEPT。**摘要与结论相反的引用被判为支持**,直接违反本项目置信度路由规范中"摘要与结论矛盾 => 拒绝使用"的要求。0.2 的阈值对"包含度"型分数来说过低,几个实词撞上就能过线。
- 另一侧:中文 claim 对英文 abstract 词面零重叠,恒为 0 分 → 全部涌入 HUMAN_REVIEW(方向安全,但中文报告会把 HITL 队列打爆)。双侧同含否定词时不减半,即便否定对象完全不同。

**【可能带来的风险】** 词重叠误判语义支持,矛盾文献被引为正面证据——报告结论与其引用互相打脸,是最伤可信度的一类错误;该判定器在生产中**必须**只作降级手段。

**【建议/结论】** **需要修改(高优先级)**。短期:将 `support_threshold` 提高(如 ≥0.5),且启发式判定为"支持"时最多给 MEDIUM/HUMAN_REVIEW,HIGH/ACCEPT 仅允许来自注入的 LLM judge;长期:生产环境注入 LLM entailment judge,并保留 HITL 人工复核兜底(接口 `support_judge=` 已就绪,改动成本低)。在输出表中标注当前使用的是哪种 judge,避免下游误信启发式结果。

---

## 8. 可测试性与依赖注入

**【检查项】** 外部效应(HTTP、判定器、HITL 通知、PDF 库)是否可注入,核心逻辑是否可离线、确定性地测试;测试是否真的存在。

**【在本代码中的检查结果】**
- 注入面设计良好:`CitationChecker.__init__` 接受 `fetch_json` / `fetch_text` / `support_judge` / `on_human_review` 四个可注入依赖,类 docstring 写清了异常契约(注入的 fetcher 也须遵守 404→`NotFoundError`、其余→`LookupBackendError`);`route_verification` 被刻意保持为无 I/O 纯函数("kept standalone so it is trivially unit-testable");`audit_pdf(path, checker=...)` 允许注入 mock 过的 checker;`pypdf` 懒加载使模块在无依赖环境下仍可 import。这套结构可以做到测试不打真网。
- **但目录中没有任何测试文件**(本次审查时 `ai-research-agent/` 下仅有 README.md、DESIGN.md 与两份源码)。`EmptyBibliographyError` 的 docstring 声称 "tests assert on this exception",模块头也承诺 "Non-empty bibliography is enforced ... (and its tests)",而面试题要求"必须有测试保证引用列表不为空"——**该承诺目前没有兑现物**。
- 细节:`_http_get` 内的 `time.sleep` 不可注入,若有测试想覆盖默认 HTTP 层的重试路径会真实等待 3 秒;CLI `main` 硬编码 `CitationChecker()`,CLI 层只能靠子进程级测试。

**【可能带来的风险】** 没有测试,"严禁空引用列表""fail-safe 不放行"等硬性规则没有回归保障,并行修改(当前正有人在改)极易无声破坏这些不变量;若日后补测试时不用注入点,则测试打真网,不可复现且泄露流量。

**【建议/结论】** 结构通过,交付不完整。**必须补一份离线测试**(全部走注入 fetcher),至少覆盖:空列表抛 `EmptyBibliographyError`;`LookupBackendError` → HUMAN_REVIEW 而非 ACCEPT/REJECT;404 DOI → 降级标题搜索;强匹配 + 矛盾 claim 的路由;`route_verification` 的全部分支。顺带把 `time.sleep` 换成可注入的 sleeper。

---

## 9. Unicode 与变音符处理

**【检查项】** 非 ASCII 作者名/标题(变音符、连字、CJK)在归一化与比对中是否等价化,是否引发误杀或误放。

**【在本代码中的检查结果】**
- `_normalize` 做 NFKD 分解并剔除 combining 字符,`Müller`→`muller`、`café`→`cafe`,再统一小写、去标点,能覆盖最常见的欧洲变音符;`re.sub(r"[^\w\s]", " ", ...)` 中 `\w` 在 Python3 默认 Unicode 语义下保留 CJK,中文标题不会被清空。整体思路正确。
- 盲点:NFKD 对**无分解形式**的字母无效——`ø`(Søgaard)、`ß`(Weiß vs Weiss)、`đ`、`ł` 等不会折叠到 ASCII;`lower()` 也不做 casefold(`ß`→`ss` 需要 `str.casefold()`)。当报告写 "Sogaard" 而 CrossRef 返回 "Søgaard" 时,`_first_author_family` 比对(`_normalize(cited_family) == _normalize(best["first_family"])` 的全等判断)判 `author_consistent=False`,强匹配被拉低到 HUMAN_REVIEW。
- 注意该失败方向是**安全侧**(多报人工复核,不会放行),与第 2 节"元数据缺失反而放行"形成对照:有数据但字符集不合会误报,没数据反而通过——两个方向的不对称值得一并修。

**【可能带来的风险】** 北欧/东欧/德语系作者的真实引用被批量推入 HITL 队列,人工复核疲劳后形成"看到作者不一致就点通过"的惯性,反噬整个 HITL 机制的有效性。

**【建议/结论】** 低危,建议改进:`lower()` 换 `casefold()`,并为 `ø→o`、`đ→d`、`ł→l`、`æ→ae` 等无分解字符加一张小型映射表;作者姓氏比对从全等放宽为高阈值相似度。

---

## 10. CrossRef JATS 摘要剥离与 OpenAlex 摘要重建

**【检查项】** CrossRef 返回的 JATS/XML 摘要与 OpenAlex 倒排索引摘要在喂给 support_judge 前是否被正确还原为纯文本。

**【在本代码中的检查结果】**
- `_strip_jats` 用 `<[^>]+>` 去除标签并折叠空白,`_candidate_from_crossref` 仅在 `raw_abstract` 非空时调用,空摘要保持 `None` 从而正确触发"abstract unavailable"路由。常规 `<jats:p>` 摘要处理正确。
- 盲点一:**不解码 XML 实体**,`&amp;`、`&lt;`、`&#x03B1;` 会以字面形式留在文本里,成为无意义 token 参与 `default_support_judge` 的加权重叠(好在多为低权重噪声)。
- 盲点二:数学公式的 MathML 标签被剥掉后留下符号残渣,可能干扰词面匹配;`<` 出现在正文(如 "p<0.05")时 `<[^>]+>` 可能把到下一个 `>` 为止的正文误当标签吞掉。
- `_rebuild_openalex_abstract` 按位置排序重建,对 `None`/空 dict 返回 `None`,重复位置后写覆盖前写;位置有空洞时静默跳过(`" ".join(slots[i] for i in sorted(slots))` 用的是 sorted keys 而非 range,不会 KeyError——实现是对的)。唯 `int(pos)` 对畸形数据会抛异常击穿(已在第 6 节记录)。

**【可能带来的风险】** 摘要文本噪声轻微抬高/压低 support 分数;在 `support_threshold=0.2` 这么低的阈值下(第 7 节),噪声抬分与误放行会叠加。

**【建议/结论】** 低危。建议 `_strip_jats` 后追加 `html.unescape`(标准库,零成本);其余作为已知启发式局限记录即可。

---

## 11. 退出码语义

**【检查项】** CLI 退出码是否语义清晰、互不冲突,能否被 CI/流水线可靠消费。

**【在本代码中的检查结果】**
- `audit_exit_code` 定义了清晰的三档:REJECT→2、HUMAN_REVIEW→1、全 ACCEPT→0;`pdf_citation_audit` 另加 3=缺 pypdf 依赖,且模块 docstring 把全部退出码写明——设计意图良好。
- 冲突一:**用法错误/文件不可读/空书目也返回 2**(两个 `main` 均如此),与"存在 REJECT(发现幻觉引用)"共享同一个码。CI 无法区分"审计器没跑起来"和"审计跑完且发现了必须删除的引用",而这两者的处置完全不同(修流水线 vs 修报告)。
- 冲突二:未捕获异常(损坏 PDF、畸形 JSON 结构,见第 6 节)导致解释器以退出码 **1** 崩溃,与"存在 HUMAN_REVIEW"同码。一个崩溃的审计会被 CI 误读成"审计完成,有待人工复核项"。所幸两者都非 0,不会误放行,但会误导后续处置。

**【可能带来的风险】** 流水线基于退出码做分支(如 1→发 HITL 通知、2→自动删引用重写)时,崩溃与用法错误会触发错误的自动化动作。

**【建议/结论】** 低-中危。建议:用法/IO 错误改用独立码(如 64,循 sysexits 惯例);两个 `main` 最外层兜底 `except Exception` 打印错误并返回专用码(如 70),保证 1/2 只表达审计结论。

---

## 12. 并发、缓存与性能

**【检查项】** 大规模书目下的吞吐与延迟,重复查询是否有缓存,顺序执行是否成为瓶颈。

**【在本代码中的检查结果】**
- `verify_report` 严格串行,每条引用最多 4 个 HTTP 请求;最坏情况下单个请求耗时约 10s×3 次尝试 + 3s 退避 ≈ 33s,单条引用理论上可达 2 分钟以上。50 条引用的报告在后端劣化时会跑到小时级。
- 无任何缓存:同一 DOI/标题在同一次审计或多次审计间重复查询(报告修订后重跑是常态),既慢又加重第 5 节的限流风险。
- 公平地说,串行 + 无并发在"礼貌性"上是保守安全的,当前规模(面试交付物)可接受;这是可扩展性债务而非缺陷。

**【可能带来的风险】** 审计时长不可控导致流水线超时;重复请求放大被限流概率。

**【建议/结论】** 低危,记录为技术债。建议引入按 (doi, title) 键的进程内 memoization(`functools.lru_cache` 级别即可),并发采用带上限(如 2-4)的有界并发以兼顾礼貌性;两者都不影响现有注入式测试结构。

---

## 汇总表

| # | 检查项 | 严重度 | 状态 |
|---|--------|--------|------|
| 1 | 外部 API 错误处理/超时/重试 | 中 | 基本通过,改进 429/搜索端点 404 处理 |
| 2 | 模糊匹配阈值与归一化(元数据缺失即放行) | **高** | **需修改** |
| 3 | URL 编码/注入(DOI 未做形状校验) | 中 | 需修改 |
| 4 | Fail-safe 方向性 | 中(主链路通过) | 通过;补 ACCEPT-无-bibtex 闭环 |
| 5 | 速率限制与 API 礼貌性(mailto 占位符、无限速) | 中 | 需改进 |
| 6 | 空输入与边界 | 低 | 基本通过;补畸形数据兜底 |
| 7 | 启发式 support_judge 能力边界(矛盾可过检) | **高** | **需修改** |
| 8 | 可测试性与依赖注入(测试缺失) | 中 | 结构通过;**测试必须补齐** |
| 9 | Unicode/变音符 | 低 | 建议改进 |
| 10 | JATS 剥离与摘要重建 | 低 | 建议改进 |
| 11 | 退出码语义 | 低-中 | 建议改进 |
| 12 | 并发与缓存 | 低 | 技术债,记录 |

## 总体结论

这份代码的**架构判断是对的**:404 与基础设施故障的异常分型、`backend_failed` 最高优先级的 fail-safe 路由、`Verification` 默认落在 HUMAN_REVIEW 的防御性默认值、四个外部效应全部可注入、`route_verification` 保持纯函数——这些决定了"网络失败绝不静默放行"这条底线是守住的,Chain-of-Evidence 的四条原则中第 1、3、4 条在代码结构上有实质落实。

**但目前不建议按现状进入生产**,两处高危问题都发生在"通往 ACCEPT 的最后一步":其一,年份/作者缺失被当作"未矛盾",仅凭标题相似度 ≥0.95 即自动接受并拉取 BibTeX,同名异文会被张冠李戴;其二,启发式 support_judge 配 0.2 的低阈值,摘要与 claim 相矛盾的文献仍可能被判"支持"并 HIGH/ACCEPT,直接违反本项目"摘要与结论矛盾 => 拒绝"的路由规范。两者的共性是:**启发式信号被允许单独兑换成最高置信度**。修复方向一致——把"仅标题匹配"与"启发式判支持"的天花板都压到 MEDIUM/HUMAN_REVIEW,HIGH/ACCEPT 只留给"元数据多重佐证 + LLM judge(或人工)确认支持"的组合。加上补齐承诺中的离线测试、校验 DOI 形状、替换 mailto 占位符,这套模块即可达到可部署标准。

---

## 复审与修复记录(审查后落实)

本节记录审查意见的处置结果。三项拦截性问题已全部修复,每项修复均配有专门的回归测试;测试文件已由并行开发补齐(审查快照时尚不存在)。

| 审查项 | 处置 | 修复方式 | 回归测试 |
|--------|------|----------|----------|
| #2 元数据缺失即放行(高危) | **已修复** | 新增纯函数 `is_strong_match()`,强匹配在"高标题相似度 + 无矛盾"之外,还必须有**至少一项正向佐证**(年份一致 / 首作者一致 / 所引 DOI 与命中记录一致);仅标题命中降级 MEDIUM/HUMAN_REVIEW,并记录 "no corroborating metadata" 原因。`route_verification` 与 `verify_one` 共用该判定,消除了文档与实现不一致 | `test_title_only_match_requires_corroboration`;`test_route_is_pure` 新增边界用例 |
| #7 矛盾摘要可判"支持"(高危) | **已修复** | `default_support_judge` 升级为返回 `(score, contradicted)`:词面重叠 ≥0.6 且单侧含否定词即判**矛盾**;`route_verification` 对强匹配 + 矛盾走 **LOW/REJECT**(呼应"摘要与结论矛盾 => 拒绝使用"),且矛盾引用不再拉取 BibTeX;`support_threshold` 默认从 0.2 提至 0.45。注入的 LLM judge 可返回同款元组或裸 float(向后兼容) | `test_contradicting_abstract_rejected`;`test_route_is_pure` 新增矛盾用例 |
| #4 ACCEPT-无-bibtex 中间态 | **已修复** | `route_verification` 的 ACCEPT 分支强制要求 `bibtex` 非空;transform 端点失败时降级 MEDIUM/HUMAN_REVIEW,reason 明确写出 "never LLM-generate it",把 Provenance-only 原则闭环到出口 | `test_accept_requires_provenance_bibtex`;`test_route_is_pure` 新增缺-bibtex 用例 |
| #8 测试缺失 | **已解决** | `test_citation_checker.py` 已交付:15 个测试全绿,覆盖三个必测场景、空书目守卫、模糊区间、后端故障 fail-safe、DOI 404 降级、解析器、纯路由边界、OpenAlex 摘要重建、PDF 端到端冒烟;全部走注入 fetcher 且 patch 了 `urllib.request.urlopen` 防真网 | — |
| #1/#3/#5/#6/#9/#10/#11/#12 | 记录在案 | 中低危改进项(429 退避、DOI 形状校验、mailto 占位符、畸形数据兜底、casefold、XML 实体、退出码细分、缓存/限速),作为上线前 checklist 保留 | — |

修复后的路由不变量:**HIGH/ACCEPT 的充要条件 = 强匹配(含正向佐证)∧ 支持性确认(或无 claim)∧ 无矛盾 ∧ 官方 BibTeX 已溯源拉取**;任何单一启发式信号都不再能独立兑换最高置信度。
