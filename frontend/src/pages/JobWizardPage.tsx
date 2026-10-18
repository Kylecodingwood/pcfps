import { CheckCircleOutlined, LoadingOutlined } from "@ant-design/icons";
import {
  Alert,
  Button,
  Card,
  Divider,
  Form,
  Input,
  InputNumber,
  Result,
  Segmented,
  Space,
  Steps,
  Typography,
} from "antd";
import type { SegmentedProps } from "antd/es/segmented";
import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createTaskRequest, getTaskRequest } from "../api/client";
import type { CreateTaskRequestBody, FilterMethod, TaskResponseDto } from "../api/types";

type WizardFormValues = {
  inputLasPath: string;
  filterMethod: FilterMethod;
  sorNeighborCount?: number | null;
  sorStdRatio?: number | null;
  rorRadius?: number | null;
  rorMinNeighbors?: number | null;
};

const filterMethodSegmentedOptions: SegmentedProps<FilterMethod>["options"] = [
  { label: "SOR", value: "SOR" },
  { label: "ROR", value: "ROR" },
];

/**
 * Builds POST body: optional numbers omitted when empty so the server merges defaults.
 */
function buildCreateTaskBodyFromForm(values: WizardFormValues): CreateTaskRequestBody {
  const body: CreateTaskRequestBody = {
    inputLasPath: values.inputLasPath.trim(),
    filterMethod: values.filterMethod,
  };
  if (values.sorNeighborCount != null) {
    body.sorNeighborCount = values.sorNeighborCount;
  }
  if (values.sorStdRatio != null) {
    body.sorStdRatio = values.sorStdRatio;
  }
  if (values.rorRadius != null) {
    body.rorRadius = values.rorRadius;
  }
  if (values.rorMinNeighbors != null) {
    body.rorMinNeighbors = values.rorMinNeighbors;
  }
  return body;
}

/**
 * Wizard: LAS path, filter algorithm + optional params, create task, poll, link to dual preview.
 */
export function JobWizardPage() {
  const navigate = useNavigate();
  const [wizardForm] = Form.useForm<WizardFormValues>();
  const [currentStep, setCurrentStep] = useState(0);
  const [latestTask, setLatestTask] = useState<TaskResponseDto | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const pollingCancelRef = useRef(false);
  const selectedFilterMethod = Form.useWatch("filterMethod", wizardForm) ?? "SOR";

  useEffect(() => {
    return () => {
      pollingCancelRef.current = true;
    };
  }, []);

  async function pollUntilTerminal(taskId: string) {
    const pollIntervalMs = 2000;
    while (!pollingCancelRef.current) {
      const taskSnapshot = await getTaskRequest(taskId);
      setLatestTask(taskSnapshot);
      if (taskSnapshot.status === "SUCCEEDED" || taskSnapshot.status === "FAILED") {
        setCurrentStep(2);
        return;
      }
      await new Promise((resolve) => setTimeout(resolve, pollIntervalMs));
    }
  }

  async function handleWizardSubmit() {
    setSubmitError(null);
    try {
      const values = await wizardForm.validateFields();
      const createdTask = await createTaskRequest(buildCreateTaskBodyFromForm(values));
      setLatestTask(createdTask);
      setCurrentStep(1);
      pollingCancelRef.current = false;
      await pollUntilTerminal(createdTask.id);
    } catch (errorUnknown) {
      const message = errorUnknown instanceof Error ? errorUnknown.message : "创建失败";
      setSubmitError(message);
    }
  }

  return (
    <div style={{ maxWidth: 840, margin: "0 auto" }}>
      <Typography.Title level={3} style={{ marginTop: 0, marginBottom: 4, letterSpacing: "-0.02em" }}>
        新建处理任务
      </Typography.Title>
      <Typography.Paragraph type="secondary" style={{ marginBottom: 20 }}>
        选择滤波算法与参数（留空则使用灰色提示中的默认值），配置在创建后固定不变。
      </Typography.Paragraph>

      <Steps
        style={{ marginBottom: 22 }}
        size="small"
        current={currentStep}
        items={[
          { title: "配置", description: "路径与滤波" },
          { title: "处理中", description: "调度与 Python" },
          { title: "完成", description: "对比预览" },
        ]}
      />

      {currentStep === 0 && (
        <Card
          bordered={false}
          style={{
            boxShadow: "0 1px 2px rgba(0,0,0,0.06), 0 8px 24px rgba(0,0,0,0.06)",
          }}
          styles={{ body: { paddingTop: 20, paddingBottom: 12 } }}
        >
          <Form<WizardFormValues>
            form={wizardForm}
            layout="vertical"
            requiredMark="optional"
            initialValues={{ filterMethod: "SOR" }}
            onFinish={() => void handleWizardSubmit()}
          >
            <Form.Item
              name="inputLasPath"
              label="LAS / LAZ 绝对路径"
              rules={[{ required: true, message: "请填写服务器上的文件路径" }]}
            >
              <Input.TextArea rows={3} placeholder="/path/to/input.las" autoSize={{ minRows: 3, maxRows: 6 }} />
            </Form.Item>

            <Divider plain style={{ margin: "12px 0 16px", fontSize: 13, color: "#86868b" }}>
              滤波
            </Divider>

            <Form.Item name="filterMethod" label="算法">
              <Segmented<FilterMethod> options={filterMethodSegmentedOptions} block />
            </Form.Item>

            {selectedFilterMethod === "SOR" ? (
              <Space direction="vertical" size="middle" style={{ width: "100%" }}>
                <Form.Item
                  name="sorNeighborCount"
                  label="邻域点数 k"
                  extra="留空则使用默认 20（统计邻域大小）。"
                >
                  <InputNumber<number>
                    style={{ width: "100%", maxWidth: 360 }}
                    min={1}
                    placeholder="默认 20"
                    controls
                  />
                </Form.Item>
                <Form.Item
                  name="sorStdRatio"
                  label="标准差倍数"
                  extra="留空则使用默认 1.0；越大越保守（保留更多点）。"
                >
                  <InputNumber<number>
                    style={{ width: "100%", maxWidth: 360 }}
                    min={0.0001}
                    step={0.1}
                    placeholder="默认 1.0"
                  />
                </Form.Item>
              </Space>
            ) : (
              <Space direction="vertical" size="middle" style={{ width: "100%" }}>
                <Form.Item
                  name="rorRadius"
                  label="搜索半径"
                  extra="与 LAS 平面坐标（XY）同一单位；留空则使用默认 0.5。"
                >
                  <InputNumber<number>
                    style={{ width: "100%", maxWidth: 360 }}
                    min={0.0001}
                    step={0.1}
                    placeholder="默认 0.5"
                  />
                </Form.Item>
                <Form.Item
                  name="rorMinNeighbors"
                  label="半径内最少邻点数"
                  extra="留空则使用默认 5；低于该数的点视为离群。"
                >
                  <InputNumber<number>
                    style={{ width: "100%", maxWidth: 360 }}
                    min={0}
                    placeholder="默认 5"
                  />
                </Form.Item>
              </Space>
            )}

            {submitError ? <Alert type="error" message={submitError} style={{ marginTop: 8 }} /> : null}

            <Form.Item style={{ marginTop: 20, marginBottom: 0 }}>
              <Space wrap>
                <Button type="primary" htmlType="submit">
                  提交并开始处理
                </Button>
                <Link to="/jobs">返回列表</Link>
              </Space>
            </Form.Item>
          </Form>
        </Card>
      )}

      {currentStep === 1 && (
        <Card bordered={false} style={{ boxShadow: "0 1px 2px rgba(0,0,0,0.06)" }}>
          <Space align="center" style={{ marginBottom: 16 }}>
            <LoadingOutlined style={{ fontSize: 22 }} />
            <Typography.Text>任务处理中，请稍候…（自动刷新状态）</Typography.Text>
          </Space>
          {latestTask ? (
            <Alert
              type="info"
              message={`任务 ${latestTask.id}`}
              description={
                <div style={{ lineHeight: 1.65 }}>
                  <div>状态：{latestTask.status}</div>
                  <div>滤波：{latestTask.filterSummary ?? "—"}</div>
                  <div>输入：{latestTask.inputLasPath}</div>
                </div>
              }
            />
          ) : null}
        </Card>
      )}

      {currentStep === 2 && latestTask ? (
        <Card bordered={false} style={{ boxShadow: "0 1px 2px rgba(0,0,0,0.06)" }}>
          {latestTask.status === "SUCCEEDED" ? (
            <Result
              icon={<CheckCircleOutlined />}
              status="success"
              title="处理成功"
              subTitle={
                <>
                  <div style={{ marginBottom: 8 }}>滤波：{latestTask.filterSummary ?? "—"}</div>
                  <div style={{ marginTop: 12, marginBottom: 6, fontWeight: 500 }}>输出目录（含 filtered.las 等）</div>
                  <div
                    style={{
                      marginTop: 0,
                      padding: "10px 12px",
                      background: "var(--ant-color-fill-quaternary, #fafafa)",
                      border: "1px solid var(--ant-color-border-secondary, #f0f0f0)",
                      borderRadius: 8,
                      wordBreak: "break-all",
                    }}
                  >
                    <Typography.Text
                      copyable={
                        latestTask.outputBasePath
                          ? { text: latestTask.outputBasePath, tooltips: ["复制路径", "已复制"] }
                          : false
                      }
                      style={{
                        fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
                        fontSize: 13,
                        color: "var(--ant-color-text, rgba(0, 0, 0, 0.88))",
                      }}
                    >
                      {latestTask.outputBasePath?.trim()
                        ? latestTask.outputBasePath
                        : "（后端未返回输出路径）"}
                    </Typography.Text>
                  </div>
                </>
              }
              extra={
                <Space wrap>
                  <Button type="primary" onClick={() => void navigate(`/preview/dual?taskId=${latestTask.id}`)}>
                    在大屏中查看（滤波对比）
                  </Button>
                  <Link to={`/jobs/${latestTask.id}/segment/new`}>新建分割</Link>
                  <Link to={`/jobs/${latestTask.id}/classify/new`}>语义分类</Link>
                  <Link to="/jobs">返回任务列表</Link>
                </Space>
              }
            />
          ) : (
            <Result
              status="error"
              title="处理失败"
              subTitle={latestTask.errorMessage ?? latestTask.status}
              extra={
                <Link to="/jobs">
                  <Button>返回列表</Button>
                </Link>
              }
            />
          )}
        </Card>
      ) : null}
    </div>
  );
}
