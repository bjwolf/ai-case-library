const { Layout, Menu, Form, Input, Select, Slider, Button, Table, Tag, Modal,
  message, Card, Space, Typography, Tabs, Popconfirm, Tooltip, Row, Col, Badge } = antd;
const { Header, Content, Footer } = Layout;
const { Title, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;

const API_BASE = "http://127.0.0.1:8000";

// ---- API helpers ----
async function fetchOptions() {
  const res = await fetch(`${API_BASE}/cases/options`);
  return res.json();
}
async function fetchCases(params = {}) {
  const qs = new URLSearchParams(params).toString();
  const res = await fetch(`${API_BASE}/cases?${qs}`);
  return res.json();
}
async function createCase(data) {
  const res = await fetch(`${API_BASE}/cases`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error((await res.json()).detail || "Create failed");
  return res.json();
}
async function updateCase(id, data) {
  const res = await fetch(`${API_BASE}/cases/${id}`, {
    method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error((await res.json()).detail || "Update failed");
  return res.json();
}
async function submitCase(id) {
  const res = await fetch(`${API_BASE}/cases/${id}/submit`, { method: "PUT" });
  if (!res.ok) throw new Error((await res.json()).detail || "Submit failed");
  return res.json();
}
async function deleteCase(id) {
  const res = await fetch(`${API_BASE}/cases/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error((await res.json()).detail || "Delete failed");
  return res.json();
}

// ---- Submission Form Component ----
function CaseForm({ options, onSuccess, editingCase, onCancelEdit }) {
  const [form] = Form.useForm();
  const [loading, setLoading] = React.useState(false);
  const isEditing = !!editingCase;

  React.useEffect(() => {
    if (editingCase) {
      form.setFieldsValue(editingCase);
    } else {
      form.resetFields();
    }
  }, [editingCase]);

  const handleSaveDraft = async () => {
    try {
      const values = await form.validateFields(["owner_login", "program_team", "use_case_title", "problem_statement", "ai_technique"]);
      const allValues = form.getFieldsValue(true);
      setLoading(true);
      if (isEditing) {
        await updateCase(editingCase.id, { ...allValues, status: "draft" });
        message.success("Draft updated");
      } else {
        await createCase({ ...allValues, status: "draft" });
        message.success("Draft saved");
      }
      form.resetFields();
      onSuccess();
    } catch (e) {
      if (e.errorFields) message.error("Please fill required fields");
      else message.error(e.message);
    } finally { setLoading(false); }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);
      if (isEditing) {
        await updateCase(editingCase.id, { ...values, status: "submitted" });
      } else {
        await createCase({ ...values, status: "submitted" });
      }
      message.success("Initiative submitted");
      form.resetFields();
      onSuccess();
    } catch (e) {
      if (e.errorFields) message.error("Please fill all required fields");
      else message.error(e.message);
    } finally { setLoading(false); }
  };

  return (
    <Card title={isEditing ? "Edit Initiative" : "Submit New AI Initiative"} className="form-card"
      extra={isEditing && <Button onClick={() => { form.resetFields(); onCancelEdit(); }}>Cancel Edit</Button>}>
      <Form form={form} layout="vertical" initialValues={{ scalability_score: 5, innovation_score: 5 }}>
        <Row gutter={16}>
          <Col span={8}>
            <Form.Item name="owner_login" label="Owner Login" rules={[{ required: true, message: "Required" }]}>
              <Input placeholder="e.g. jsmith" />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item name="job_level" label="Job Level">
              <Select placeholder="Select level" allowClear>
                {(options.job_levels || []).map(l => <Option key={l} value={l}>{l}</Option>)}
              </Select>
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item name="program_team" label="Program / Team" rules={[{ required: true, message: "Required" }]}>
              <Select placeholder="Select program" showSearch>
                {(options.programs_teams || []).map(p => <Option key={p} value={p}>{p}</Option>)}
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="use_case_title" label="Use Case Title" rules={[{ required: true, message: "Required" }]}>
              <Input placeholder="Short descriptive title" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="ai_technique" label="AI Technique" rules={[{ required: true, message: "Required" }]}>
              <Select placeholder="Select technique" showSearch>
                {(options.ai_techniques || []).map(t => <Option key={t} value={t}>{t}</Option>)}
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Form.Item name="problem_statement" label="Problem Statement" rules={[{ required: true, message: "Required" }]}>
          <TextArea rows={3} placeholder="Describe the problem this initiative solves" />
        </Form.Item>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="tools_services" label="Tools / Services">
              <Input placeholder="e.g. Amazon SageMaker, Bedrock" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="input_data" label="Input Data">
              <Input placeholder="e.g. 3 years of sales data" />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item name="key_prompts" label="Key Prompts">
          <TextArea rows={2} placeholder="Key prompts or queries used" />
        </Form.Item>

        <Form.Item name="output_outcome" label="Output / Outcome">
          <TextArea rows={2} placeholder="Describe the results achieved" />
        </Form.Item>

        <Row gutter={16}>
          <Col span={8}>
            <Form.Item name="time_saved" label="Time Saved (%)">
              <Input type="number" min={0} max={100} placeholder="e.g. 40" />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item name="accuracy" label="Accuracy (%)">
              <Input type="number" min={0} max={100} placeholder="e.g. 92" />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item name="cost_reduction" label="Cost Reduction (%)">
              <Input type="number" min={0} max={100} placeholder="e.g. 15" />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item name="scalability_score" label="Scalability Score (1-10)">
              <Slider min={1} max={10} marks={{ 1: "1", 5: "5", 10: "10" }} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item name="innovation_score" label="Innovation Score (1-10)">
              <Slider min={1} max={10} marks={{ 1: "1", 5: "5", 10: "10" }} />
            </Form.Item>
          </Col>
        </Row>

        <Space>
          <Button onClick={handleSaveDraft} loading={loading}>Save as Draft</Button>
          <Button type="primary" onClick={handleSubmit} loading={loading}>Submit Initiative</Button>
        </Space>
      </Form>
    </Card>
  );
}

// ---- Case List Component ----
function CaseList({ cases, loading, options, onEdit, onRefresh }) {
  const statusColors = { draft: "default", submitted: "processing", approved: "success" };

  const columns = [
    { title: "Title", dataIndex: "use_case_title", key: "title", width: 200,
      render: (text, record) => <Tooltip title={record.problem_statement}><a onClick={() => onEdit(record)}>{text}</a></Tooltip> },
    { title: "Owner", dataIndex: "owner_login", key: "owner", width: 90 },
    { title: "Program", dataIndex: "program_team", key: "program", width: 150,
      filters: (options.programs_teams || []).map(p => ({ text: p, value: p })),
      onFilter: (value, record) => record.program_team === value },
    { title: "AI Technique", dataIndex: "ai_technique", key: "technique", width: 150,
      filters: (options.ai_techniques || []).map(t => ({ text: t, value: t })),
      onFilter: (value, record) => record.ai_technique === value },
    { title: "Status", dataIndex: "status", key: "status", width: 100,
      filters: (options.statuses || []).map(s => ({ text: s, value: s })),
      onFilter: (value, record) => record.status === value,
      render: s => <Tag color={statusColors[s]}>{s.toUpperCase()}</Tag> },
    { title: "Time Saved", dataIndex: "time_saved", key: "time", width: 100,
      sorter: (a, b) => (a.time_saved || 0) - (b.time_saved || 0),
      render: v => v != null ? `${v}%` : "-" },
    { title: "Accuracy", dataIndex: "accuracy", key: "acc", width: 90,
      sorter: (a, b) => (a.accuracy || 0) - (b.accuracy || 0),
      render: v => v != null ? `${v}%` : "-" },
    { title: "Cost Red.", dataIndex: "cost_reduction", key: "cost", width: 90,
      sorter: (a, b) => (a.cost_reduction || 0) - (b.cost_reduction || 0),
      render: v => v != null ? `${v}%` : "-" },
    { title: "Actions", key: "actions", width: 180, render: (_, record) => (
      <Space>
        <Button size="small" onClick={() => onEdit(record)}>Edit</Button>
        {record.status === "draft" && (
          <Popconfirm title="Submit this initiative?" onConfirm={async () => { await submitCase(record.id); message.success("Submitted"); onRefresh(); }}>
            <Button size="small" type="primary">Submit</Button>
          </Popconfirm>
        )}
        <Popconfirm title="Delete this case?" onConfirm={async () => { await deleteCase(record.id); message.success("Deleted"); onRefresh(); }}>
          <Button size="small" danger>Delete</Button>
        </Popconfirm>
      </Space>
    )},
  ];

  return (
    <Card title={<span>All Initiatives <Badge count={cases.length} style={{ backgroundColor: "#1677ff", marginLeft: 8 }} /></span>}>
      <Table columns={columns} dataSource={cases} rowKey="id" loading={loading}
        size="middle" scroll={{ x: 1100 }} pagination={{ pageSize: 10, showSizeChanger: true, showTotal: t => `${t} cases` }} />
    </Card>
  );
}

// ---- Main App ----
function App() {
  const [options, setOptions] = React.useState({});
  const [cases, setCases] = React.useState([]);
  const [loading, setLoading] = React.useState(false);
  const [editingCase, setEditingCase] = React.useState(null);
  const [activeTab, setActiveTab] = React.useState("form");

  const loadData = async () => {
    setLoading(true);
    try {
      const [opts, data] = await Promise.all([fetchOptions(), fetchCases()]);
      setOptions(opts);
      setCases(data);
    } catch (e) {
      message.error("Failed to load data. Is the backend running?");
    } finally { setLoading(false); }
  };

  React.useEffect(() => { loadData(); }, []);

  const handleEdit = (record) => {
    setEditingCase(record);
    setActiveTab("form");
  };

  const tabItems = [
    { key: "form", label: "Submit Initiative",
      children: <CaseForm options={options} editingCase={editingCase}
        onSuccess={() => { setEditingCase(null); loadData(); }}
        onCancelEdit={() => setEditingCase(null)} /> },
    { key: "list", label: `Browse Initiatives (${cases.length})`,
      children: <CaseList cases={cases} loading={loading} options={options}
        onEdit={handleEdit} onRefresh={loadData} /> },
  ];

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Header style={{ display: "flex", alignItems: "center" }}>
        <Title level={3} style={{ color: "white", margin: 0 }}>AI Case Library</Title>
      </Header>
      <Content className="site-layout">
        <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} size="large" />
      </Content>
      <Footer style={{ textAlign: "center" }}>AI Ascent Hackathon 2026</Footer>
    </Layout>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
