import json
from operator import add
from typing import Annotated, Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from .llm_client import build_llm, parse_json_object
from .schemas import AgentFinding, AuditResponse, SecuritiesCase


class AuditState(TypedDict):
    securities_case: dict[str, Any]
    agent_results: Annotated[list[dict[str, Any]], add]
    risk_score: int
    risk_level: str
    decision: str
    report: str


AGENT_PROMPTS = {
    "suitability_check": {
        "agent": "适当性审核 Agent",
        "title": "客户与产品匹配",
        "system": (
            "你是证券公司适当性审核 Agent。重点检查客户风险等级 C1-C5、产品风险等级 R1-R5、"
            "年龄、投资经验、资产规模与业务类型是否匹配，并识别需要人工复核的适当性风险。"
        ),
    },
    "marketing_compliance": {
        "agent": "营销合规 Agent",
        "title": "话术与材料合规",
        "system": (
            "你是证券公司营销合规 Agent。重点检查销售话术、产品宣传、投顾沟通中是否存在保本保收益、"
            "稳赚不赔、内部消息、确定上涨、夸大业绩、弱化风险等违规或不审慎表达。"
        ),
    },
    "research_advisory": {
        "agent": "投顾/研报合规 Agent",
        "title": "投顾与研报边界",
        "system": (
            "你是证券公司投顾与研报合规 Agent。重点检查是否缺少风险提示、是否把研究观点包装为确定性买卖指令、"
            "是否引用未经验证信息、是否越权提供投资建议。"
        ),
    },
    "trading_aml": {
        "agent": "异常交易与反洗钱 Agent",
        "title": "交易行为与 AML 线索",
        "system": (
            "你是证券公司异常交易和反洗钱 Agent。重点识别短期高频交易、大额集中交易、异常出入金、"
            "资产规模与交易金额不匹配、疑似账户出借或关联交易等风险。"
        ),
    },
}


def severity_from_score(score: int) -> str:
    if score >= 24:
        return "danger"
    if score >= 10:
        return "warn"
    return "ok"


def risk_level(score: int) -> str:
    if score >= 70:
        return "高风险"
    if score >= 40:
        return "中风险"
    return "低风险"


def decision_for(score: int) -> str:
    if score >= 70:
        return "禁止发布/销售，提交合规复核"
    if score >= 40:
        return "补充风险揭示后人工复核"
    return "可通过或抽检"


def call_agent(agent_key: str, state: AuditState) -> dict[str, Any]:
    prompt = AGENT_PROMPTS[agent_key]
    llm = build_llm()
    context = {
        "securities_case": state["securities_case"],
        "previous_agent_results": state.get("agent_results", []),
    }
    messages = [
        SystemMessage(content=prompt["system"]),
        HumanMessage(
            content=(
                "请基于以下证券业务材料进行合规与风险审核。只输出 JSON，不要 Markdown。\n"
                "JSON 格式："
                '{"score": 0-35, "findings": ["结论1"], "evidence": ["引用的字段或原文证据"]}。\n'
                "评分越高代表风险越高；findings 使用中文，具体、可解释、可给合规或业务人员阅读。\n"
                "如果材料不足，请把信息缺口作为风险点写入 findings。\n"
                f"当前 Agent：{prompt['agent']} / {prompt['title']}\n"
                f"输入上下文：{json.dumps(context, ensure_ascii=False)}"
            )
        ),
    ]
    raw = llm.invoke(messages).content
    parsed = parse_json_object(str(raw))
    score = max(0, min(35, int(parsed.get("score", 0))))
    result = AgentFinding(
        agent=prompt["agent"],
        title=prompt["title"],
        score=score,
        severity=severity_from_score(score),
        findings=[str(item) for item in parsed.get("findings", [])][:6],
        evidence=[str(item) for item in parsed.get("evidence", [])][:6],
    )
    return {"agent_results": [result.model_dump()]}


def suitability_check_node(state: AuditState) -> dict[str, Any]:
    return call_agent("suitability_check", state)


def marketing_compliance_node(state: AuditState) -> dict[str, Any]:
    return call_agent("marketing_compliance", state)


def research_advisory_node(state: AuditState) -> dict[str, Any]:
    return call_agent("research_advisory", state)


def trading_aml_node(state: AuditState) -> dict[str, Any]:
    return call_agent("trading_aml", state)


def approval_node(state: AuditState) -> dict[str, Any]:
    score = max(0, min(100, sum(item["score"] for item in state["agent_results"])))
    level = risk_level(score)
    decision = decision_for(score)
    result = AgentFinding(
        agent="合规结论 Agent",
        title="最终处置建议",
        score=0,
        severity="danger" if score >= 70 else "warn" if score >= 40 else "ok",
        findings=[
            f"综合风险分 {score}，风险等级为{level}。",
            f"建议动作：{decision}。",
            "该结论由前序 Agent 结果汇总形成，适合作为证券业务合规初筛意见。",
        ],
        evidence=[item["title"] for item in state["agent_results"]],
    )
    return {
        "risk_score": score,
        "risk_level": level,
        "decision": decision,
        "agent_results": [result.model_dump()],
    }


def report_node(state: AuditState) -> dict[str, Any]:
    case = state["securities_case"]
    finding_lines = []
    for item in state["agent_results"]:
        for finding in item["findings"]:
            finding_lines.append(f"- {item['agent']}：{finding}")

    report = "\n".join(
        [
            "证券业务合规与风险审核意见",
            "",
            f"客户：{case['customer_name']}",
            f"业务类型：{case['business_type']}",
            f"客户风险等级：{case['customer_risk_level']}，产品/服务风险等级：{case['product_risk_level']}",
            f"交易金额：{case['transaction_amount']} 元，近 30 日交易次数：{case['trades_30d']}",
            "",
            f"综合风险分：{state['risk_score']}",
            f"风险等级：{state['risk_level']}",
            f"处理建议：{state['decision']}",
            "",
            "Agent 审核依据：",
            *finding_lines,
        ]
    )
    return {"report": report}


def build_graph():
    graph = StateGraph(AuditState)
    graph.add_node("suitability_check", suitability_check_node)
    graph.add_node("marketing_compliance", marketing_compliance_node)
    graph.add_node("research_advisory", research_advisory_node)
    graph.add_node("trading_aml", trading_aml_node)
    graph.add_node("approval", approval_node)
    graph.add_node("report", report_node)

    graph.add_edge(START, "suitability_check")
    graph.add_edge("suitability_check", "marketing_compliance")
    graph.add_edge("marketing_compliance", "research_advisory")
    graph.add_edge("research_advisory", "trading_aml")
    graph.add_edge("trading_aml", "approval")
    graph.add_edge("approval", "report")
    graph.add_edge("report", END)
    return graph.compile()


audit_graph = build_graph()


def run_audit(securities_case: SecuritiesCase) -> AuditResponse:
    final_state = audit_graph.invoke(
        {
            "securities_case": securities_case.model_dump(),
            "agent_results": [],
            "risk_score": 0,
            "risk_level": "",
            "decision": "",
            "report": "",
        }
    )
    return AuditResponse(
        risk_score=final_state["risk_score"],
        risk_level=final_state["risk_level"],
        decision=final_state["decision"],
        agent_results=[AgentFinding.model_validate(item) for item in final_state["agent_results"]],
        report=final_state["report"],
    )
