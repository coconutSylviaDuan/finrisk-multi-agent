# SecuGuard Multi-Agent

证券业务合规与风险审核助手，一个基于 LangGraph + 外部 LLM API 的可运行多 Agent 项目。

## 项目亮点

- 适当性审核 Agent：检查客户风险等级、产品/服务风险等级、年龄、投资经验和资产规模是否匹配。
- 营销合规 Agent：识别保本保收益、稳赚不赔、内部消息、确定上涨、夸大业绩等违规表达。
- 投顾/研报合规 Agent：检查投顾话术、研报摘要、风险提示和投资建议边界。
- 异常交易与反洗钱 Agent：识别高频交易、大额集中交易、异常出入金、资产交易不匹配等线索。
- 合规结论 Agent：汇总输出通过、补充风险揭示后复核、禁止发布/销售等处置建议。
- FastAPI 后端：提供 `/api/audit` 和 `/api/health`。
- LangGraph 编排：每个 Agent 是一个图节点，按证券合规审核链路顺序执行。
- 外部 API 依赖：支持 OpenAI 兼容协议，可接 OpenAI、公司网关或国产模型代理。

## 快速运行

1. 安装依赖：

```powershell
cd D:\dxy\finrisk-multi-agent
C:\Users\95853\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pip install -r requirements.txt
```

2. 配置外部 API：

```powershell
copy .env.example .env
```

然后编辑 `.env`：

```text
OPENAI_API_KEY=你的 API Key
OPENAI_MODEL=gpt-4o-mini
# 如果使用公司网关或兼容 OpenAI 的模型服务，填写：
# OPENAI_BASE_URL=https://your-gateway.example.com/v1
```

3. 启动服务：

```powershell
C:\Users\95853\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8765
```

然后打开：

```text
http://127.0.0.1:8765/
```

## 演示流程

1. 打开页面后表单默认是空的。
2. 可以手动填写证券业务材料，也可以通过 `data/sample-applications.csv` 导入案例。
3. 点击“载入高风险样例”，展示高风险营销话术和适当性不匹配场景。
4. 点击“启动多 Agent 审核”，后端会通过 LangGraph 调度多个证券合规 Agent。
5. 复制“证券业务合规审核意见”给领导展示完整审核链路。

## 项目结构

```text
finrisk-multi-agent
├─ backend
│  ├─ main.py          # FastAPI 入口
│  ├─ graph.py         # LangGraph 多 Agent 编排
│  ├─ llm_client.py    # 外部 OpenAI 兼容 API 客户端
│  └─ schemas.py       # 请求和响应模型
├─ data
│  └─ sample-applications.csv
├─ index.html
├─ app.js
├─ styles.css
├─ requirements.txt
└─ .env.example
```

## LangGraph 链路

```text
START
 -> 适当性审核 Agent
 -> 营销合规 Agent
 -> 投顾/研报合规 Agent
 -> 异常交易与反洗钱 Agent
 -> 合规结论 Agent
 -> 报告生成
 -> END
```

## 后续可扩展

- 增加监管规则库 RAG，例如适当性管理办法、投顾业务规则、营销材料管理制度。
- 增加 LangGraph streaming，把每个 Agent 的执行过程实时推到前端。
- 接入内部客户画像、产品风险评级、交易流水和员工展业记录。
- 接入 LangSmith 做链路追踪、评估和审计。
