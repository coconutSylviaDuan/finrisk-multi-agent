const fields = {
  customerName: document.querySelector("#customerName"),
  customerRiskLevel: document.querySelector("#customerRiskLevel"),
  productRiskLevel: document.querySelector("#productRiskLevel"),
  businessType: document.querySelector("#businessType"),
  investmentExperienceYears: document.querySelector("#investmentExperienceYears"),
  age: document.querySelector("#age"),
  assetsUnderManagement: document.querySelector("#assetsUnderManagement"),
  transactionAmount: document.querySelector("#transactionAmount"),
  trades30d: document.querySelector("#trades30d"),
  netInflow30d: document.querySelector("#netInflow30d"),
  materialText: document.querySelector("#materialText"),
};

const caseSelector = document.querySelector("#caseSelector");
const runAuditBtn = document.querySelector("#runAuditBtn");
const reportText = document.querySelector("#reportText");

const sampleCase = {
  customerName: "李强",
  customerRiskLevel: "C2",
  productRiskLevel: "R5",
  businessType: "产品销售",
  investmentExperienceYears: 0.5,
  age: 68,
  assetsUnderManagement: 180000,
  transactionAmount: 150000,
  trades30d: 42,
  netInflow30d: 120000,
  materialText:
    "该产品历史收益非常稳定，基本不用担心亏损，老师判断后面大概率上涨，建议今天直接满仓买入，错过就没有了。",
};

function collectFormData() {
  return {
    customer_name: fields.customerName.value.trim(),
    customer_risk_level: fields.customerRiskLevel.value,
    product_risk_level: fields.productRiskLevel.value,
    business_type: fields.businessType.value,
    investment_experience_years: Number(fields.investmentExperienceYears.value || 0),
    age: Number(fields.age.value || 0),
    assets_under_management: Number(fields.assetsUnderManagement.value || 0),
    transaction_amount: Number(fields.transactionAmount.value || 0),
    trades_30d: Number(fields.trades30d.value || 0),
    net_inflow_30d: Number(fields.netInflow30d.value || 0),
    material_text: fields.materialText.value.trim(),
  };
}

async function runAudit() {
  const validationError = validateForm();
  if (validationError) {
    showValidation(validationError);
    return;
  }

  setLoading(true);
  clearResults("LangGraph 正在调度证券合规 Agent，请稍候...");

  try {
    const response = await fetch("/api/audit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(collectFormData()),
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "后端审核失败");
    }
    renderAuditResult(payload);
  } catch (error) {
    showError(error);
  } finally {
    setLoading(false);
  }
}

function validateForm() {
  const required = [
    ["客户姓名", fields.customerName.value.trim()],
    ["客户风险等级", fields.customerRiskLevel.value],
    ["产品/服务风险等级", fields.productRiskLevel.value],
    ["业务类型", fields.businessType.value],
    ["投资经验", fields.investmentExperienceYears.value],
    ["年龄", fields.age.value],
    ["资产规模", fields.assetsUnderManagement.value],
    ["交易/认购金额", fields.transactionAmount.value],
    ["近 30 日交易次数", fields.trades30d.value],
    ["材料文本/话术内容", fields.materialText.value.trim()],
  ];
  const missing = required.filter(([, value]) => value === "").map(([label]) => label);
  if (missing.length) {
    return `请先导入 CSV 案例或填写必填字段：${missing.join("、")}。`;
  }
  return "";
}

function showValidation(message) {
  document.querySelector("#riskScore").textContent = "--";
  document.querySelector("#riskLevel").textContent = "待审核";
  document.querySelector("#decision").textContent = "--";
  document.querySelector("#auditFlow").innerHTML = "";
  reportText.textContent = message;
}

function renderAuditResult(payload) {
  document.querySelector("#riskScore").textContent = payload.risk_score;
  document.querySelector("#riskLevel").textContent = payload.risk_level;
  document.querySelector("#decision").textContent = payload.decision;
  document.querySelector("#auditFlow").innerHTML = payload.agent_results.map(renderAgentCard).join("");
  reportText.textContent = payload.report;
}

function renderAgentCard(agentResult, index) {
  const badgeText = {
    ok: "通过",
    warn: "关注",
    danger: "高危",
  }[agentResult.severity];

  const evidence = agentResult.evidence?.length
    ? `<li class="evidence">证据：${escapeHtml(agentResult.evidence.join("；"))}</li>`
    : "";

  return `
    <article class="agent-card">
      <header>
        <h3>${index + 1}. ${escapeHtml(agentResult.title)}</h3>
        <span class="badge ${agentResult.severity}">${badgeText}</span>
      </header>
      <p class="agent-name">${escapeHtml(agentResult.agent)}</p>
      <ul>
        ${agentResult.findings.map((finding) => `<li>${escapeHtml(finding)}</li>`).join("")}
        ${evidence}
      </ul>
    </article>
  `;
}

function clearResults(message) {
  document.querySelector("#riskScore").textContent = "--";
  document.querySelector("#riskLevel").textContent = "审核中";
  document.querySelector("#decision").textContent = "--";
  document.querySelector("#auditFlow").innerHTML = "";
  reportText.textContent = message;
}

function showError(error) {
  document.querySelector("#riskScore").textContent = "--";
  document.querySelector("#riskLevel").textContent = "失败";
  document.querySelector("#decision").textContent = "检查后端/API Key";
  reportText.textContent = [
    "审核失败",
    "",
    error.message,
    "",
    "请确认：",
    "1. 已执行 pip install -r requirements.txt。",
    "2. 已从 .env.example 复制 .env 并填写 OPENAI_API_KEY。",
    "3. 后端通过 uvicorn backend.main:app --port 8765 启动。",
  ].join("\n");
}

function setLoading(isLoading) {
  runAuditBtn.disabled = isLoading;
  runAuditBtn.textContent = isLoading ? "Agent 审核中..." : "启动多 Agent 审核";
}

function fillForm(caseData) {
  Object.entries(caseData).forEach(([key, value]) => {
    if (fields[key]) fields[key].value = value;
  });
}

function loadSample() {
  fillForm(sampleCase);
}

function parseCsv(text) {
  const rows = text
    .trim()
    .split(/\r?\n/)
    .map((line) => line.split(",").map((cell) => cell.trim()));
  const headers = rows.shift();

  return rows.map((row) => {
    return headers.reduce((record, header, index) => {
      record[header] = row[index] || "";
      return record;
    }, {});
  });
}

function normalizeImportedCase(row) {
  return {
    customerName: row.customer_name,
    customerRiskLevel: row.customer_risk_level,
    productRiskLevel: row.product_risk_level,
    businessType: row.business_type,
    investmentExperienceYears: Number(row.investment_experience_years || 0),
    age: Number(row.age || 0),
    assetsUnderManagement: Number(row.assets_under_management || 0),
    transactionAmount: Number(row.transaction_amount || 0),
    trades30d: Number(row.trades_30d || 0),
    netInflow30d: Number(row.net_inflow_30d || 0),
    materialText: row.material_text || "",
  };
}

function loadImportedCases(cases) {
  caseSelector.innerHTML = '<option value="">当前表单</option>';
  cases.forEach((caseData, index) => {
    const option = document.createElement("option");
    option.value = String(index);
    option.textContent = `${caseData.customerName || "未命名客户"} - ${caseData.businessType || "未分类"}`;
    caseSelector.appendChild(option);
  });
  caseSelector.importedCases = cases;
}

function fallbackCopy(text) {
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.left = "-9999px";
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand("copy");
  document.body.removeChild(textarea);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

document.querySelector("#runAuditBtn").addEventListener("click", runAudit);
document.querySelector("#loadSampleBtn").addEventListener("click", loadSample);
document.querySelector("#csvFile").addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  const text = await file.text();
  const cases = parseCsv(text).map(normalizeImportedCase);
  loadImportedCases(cases);

  if (cases[0]) {
    caseSelector.value = "0";
    fillForm(cases[0]);
  }
});
caseSelector.addEventListener("change", () => {
  const cases = caseSelector.importedCases || [];
  const selected = cases[Number(caseSelector.value)];
  if (selected) fillForm(selected);
});
document.querySelector("#copyReportBtn").addEventListener("click", async () => {
  const report = reportText.textContent;
  try {
    if (!navigator.clipboard) throw new Error("Clipboard API unavailable");
    await navigator.clipboard.writeText(report);
  } catch {
    fallbackCopy(report);
  }
});
