import { CheckCircleOutlined, LoadingOutlined } from "@ant-design/icons";
import {
  Alert,
  Button,
  Card,
  Divider,
  Form,
  InputNumber,
  Result,
  Segmented,
  Space,
  Steps,
  Switch,
  Typography,
} from "antd";
import type { SegmentedProps } from "antd/es/segmented";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { createDerivedJobRequest, getTaskRequest } from "../api/client";
import type { CreateDerivedTaskRequestBody, TaskKind, TaskResponseDto } from "../api/types";

type DeriveMode = "segment" | "classify";

type SegmentAlgorithm = "euclidean_cluster" | "region_growing";

type SegmentFormValues = {
  algorithm: SegmentAlgorithm;
  clusterTolerance?: number | null;
  minClusterPoints?: number | null;
  maxClusterPoints?: number | null;
  useXyOnly?: boolean;
  normalNeighborCount?: number | null;
  angleThresholdDeg?: number | null;
  distanceThreshold?: number | null;
  minRegionPoints?: number | null;
  maxSeeds?: number | null;
};

const segmentAlgorithmOptions: SegmentedProps<SegmentAlgorithm>["options"] = [
  { label: "欧式聚类", value: "euclidean_cluster" },
  { label: "区域生长", value: "region_growing" },
];

/** Fixed RF semantic classify body (PMF/CSF are not exposed in the UI). */
function buildRfSemanticClassifyBody(): CreateDerivedTaskRequestBody {
  return {
    taskKind: "CLASSIFY",
    algorithm: "ml_rf_semantic",
  };
}

function buildSegmentDerivedBody(values: SegmentFormValues): CreateDerivedTaskRequestBody {
  const body: CreateDerivedTaskRequestBody = {
    taskKind: "SEGMENT",
    algorithm: values.algorithm,
  };
  if (values.clusterTolerance != null) {
    body.clusterTolerance = values.clusterTolerance;
  }
  if (values.minClusterPoints != null) {
    body.minClusterPoints = values.minClusterPoints;
  }
  if (values.maxClusterPoints != null) {
    body.maxClusterPoints = values.maxClusterPoints;
  }
  if (values.useXyOnly === true) {
    body.useXyOnly = true;
  }
  if (values.normalNeighborCount != null) {
    body.normalNeighborCount = values.normalNeighborCount;
  }
  if (values.angleThresholdDeg != null) {
    body.angleThresholdDeg = values.angleThresholdDeg;
  }
  if (values.distanceThreshold != null) {
    body.distanceThreshold = values.distanceThreshold;
  }
  if (values.minRegionPoints != null) {
    body.minRegionPoints = values.minRegionPoints;
  }
  if (values.maxSeeds != null) {
    body.maxSeeds = values.maxSeeds;
  }
  return body;
}

export interface DeriveWizardPageProps {
  mode: DeriveMode;
}

/**
 * Child wizard: segment (configurable) or classify (auto RF semantic) from a succeeded parent filter task.
 */
export function DeriveWizardPage(props: DeriveWizardPageProps) {
  const { mode } = props;
  const isClassifyMode = mode === "classify";
  const { parentTaskId } = useParams<{ parentTaskId: string }>();
  const navigate = useNavigate();
  const [segmentForm] = Form.useForm<SegmentFormValues>();
  const [currentStep, setCurrentStep] = useState(0);
  const [parentTaskSnapshot, setParentTaskSnapshot] = useState<TaskResponseDto | null>(null);
  const [latestChildTask, setLatestChildTask] = useState<TaskResponseDto | null>(null);
  const [parentLoadError, setParentLoadError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [classifySubmitting, setClassifySubmitting] = useState(false);
  const pollingCancelRef = useRef(false);
  const classifyAutoSubmitAttemptedRef = useRef(false);
  const selectedSegmentAlgorithm = Form.useWatch("algorithm", segmentForm) ?? "euclidean_cluster";

  const taskKindForMode: TaskKind = mode === "segment" ? "SEGMENT" : "CLASSIFY";
  const titleText = mode === "segment" ? "新建分割任务" : "语义分类";

  useEffect(() => {
    return () => {
      pollingCancelRef.current = true;
    };
  }, []);

  useEffect(() => {
    if (!parentTaskId) {
      setParentLoadError("缺少父任务 ID");
      return;
    }
    const stableParentTaskId: string = parentTaskId;
    let cancelled = false;
    async function loadParent() {
      setParentLoadError(null);
      try {
        const parentSnapshot = await getTaskRequest(stableParentTaskId);
        if (cancelled) {
          return;
        }
        const parentKind = parentSnapshot.taskKind ?? "FILTER";
        if (parentKind !== "FILTER") {
          setParentLoadError("父任务必须是滤波任务（FILTER）。");
          setParentTaskSnapshot(null);
          return;
        }
        if (parentSnapshot.status !== "SUCCEEDED") {
          setParentLoadError("父任务需已成功完成，才能创建分割/语义分类子任务。");
          setParentTaskSnapshot(null);
          return;
        }
        setParentTaskSnapshot(parentSnapshot);
      } catch (errorUnknown) {
        if (!cancelled) {
          const message = errorUnknown instanceof Error ? errorUnknown.message : "加载父任务失败";
          setParentLoadError(message);
          setParentTaskSnapshot(null);
        }
      }
    }
    void loadParent();
    return () => {
      cancelled = true;
    };
  }, [parentTaskId]);

  async function pollUntilTerminal(taskId: string) {
    const pollIntervalMs = 2000;
    while (!pollingCancelRef.current) {
      const taskSnapshot = await getTaskRequest(taskId);
      setLatestChildTask(taskSnapshot);
      if (taskSnapshot.status === "SUCCEEDED" || taskSnapshot.status === "FAILED") {
        setCurrentStep(isClassifyMode ? 1 : 2);
        return;
      }
      await new Promise((resolve) => setTimeout(resolve, pollIntervalMs));
    }
  }

  async function handleSegmentSubmit() {
    if (!parentTaskId) {
      return;
    }
    const stableParentTaskId: string = parentTaskId;
    setSubmitError(null);
    try {
      const values = await segmentForm.validateFields();
      const createdChild = await createDerivedJobRequest(stableParentTaskId, buildSegmentDerivedBody(values));
      setLatestChildTask(createdChild);
      setCurrentStep(1);
      pollingCancelRef.current = false;
      await pollUntilTerminal(createdChild.id);
    } catch (errorUnknown) {
      const message = errorUnknown instanceof Error ? errorUnknown.message : "创建失败";
      setSubmitError(message);
    }
  }

  const handleRfSemanticClassifySubmit = useCallback(async () => {
    if (!parentTaskId) {
      return;
    }
    const stableParentTaskId: string = parentTaskId;
    setSubmitError(null);
    setClassifySubmitting(true);
    try {
      const createdChild = await createDerivedJobRequest(stableParentTaskId, buildRfSemanticClassifyBody());
      setLatestChildTask(createdChild);
      setCurrentStep(0);
      pollingCancelRef.current = false;
      await pollUntilTerminal(createdChild.id);
    } catch (errorUnknown) {
      const message = errorUnknown instanceof Error ? errorUnknown.message : "创建失败";
      setSubmitError(message);
      classifyAutoSubmitAttemptedRef.current = false;
    } finally {
      setClassifySubmitting(false);
    }
  }, [parentTaskId]);

  useEffect(() => {
    if (!isClassifyMode || !parentTaskSnapshot || parentLoadError) {
      return;
    }
    if (classifyAutoSubmitAttemptedRef.current) {
      return;
    }
    classifyAutoSubmitAttemptedRef.current = true;
    void handleRfSemanticClassifySubmit();
  }, [isClassifyMode, parentTaskSnapshot, parentLoadError, handleRfSemanticClassifySubmit]);

  const stepItems = isClassifyMode
    ? [
        { title: "处理中", description: "RF 四语义分类" },
        { title: "完成", description: "双窗预览" },
      ]
    : [
        { title: "配置", description: "分割算法" },
        { title: "处理中", description: "调度与 Python" },
        { title: "完成", description: "双窗预览" },
      ];

  return (
    <div style={{ maxWidth: 840, margin: "0 auto" }}>
      <Typography.Title level={3} style={{ marginTop: 0, marginBottom: 4, letterSpacing: "-0.02em" }}>
        {titleText}
      </Typography.Title>
      <Typography.Paragraph type="secondary" style={{ marginBottom: 20 }}>
        {isClassifyMode
          ? "基于父任务滤波结果（FILTERED_LAS）自动调用服务端预训练 RandomForest 模型，输出四语义 classification（1 地面 / 2 建筑 / 3 植被 / 4 其他）。"
          : "默认对父任务已成功产出的滤波结果（FILTERED_LAS）进行处理；参数留空则使用占位提示中的服务端默认值。"}
      </Typography.Paragraph>

      {parentLoadError ? <Alert type="error" message={parentLoadError} style={{ marginBottom: 16 }} /> : null}
      {parentTaskSnapshot ? (
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
          message={`父任务 ${parentTaskSnapshot.id}`}
          description={
            <div style={{ lineHeight: 1.65 }}>
              <div>状态：{parentTaskSnapshot.status}</div>
              <div>滤波：{parentTaskSnapshot.filterSummary ?? "—"}</div>
            </div>
          }
        />
      ) : null}

      <Steps style={{ marginBottom: 22 }} size="small" current={currentStep} items={stepItems} />

      {!isClassifyMode && currentStep === 0 && parentTaskSnapshot ? (
        <Card
          bordered={false}
          style={{
            boxShadow: "0 1px 2px rgba(0,0,0,0.06), 0 8px 24px rgba(0,0,0,0.06)",
          }}
          styles={{ body: { paddingTop: 20, paddingBottom: 12 } }}
        >
          <Form<SegmentFormValues>
            form={segmentForm}
            layout="vertical"
            requiredMark="optional"
            initialValues={{ algorithm: "euclidean_cluster", useXyOnly: false }}
            onFinish={() => void handleSegmentSubmit()}
          >
            <Form.Item name="algorithm" label="分割算法">
              <Segmented<SegmentAlgorithm> options={segmentAlgorithmOptions} block />
            </Form.Item>

            {selectedSegmentAlgorithm === "euclidean_cluster" ? (
              <Space direction="vertical" size="middle" style={{ width: "100%" }}>
                <Form.Item name="clusterTolerance" label="邻域半径（米）" extra="留空默认 0.5。">
                  <InputNumber style={{ width: "100%", maxWidth: 360 }} min={0.0001} step={0.05} placeholder="默认 0.5" />
                </Form.Item>
                <Form.Item name="minClusterPoints" label="成簇最少点数" extra="留空默认 50。">
                  <InputNumber style={{ width: "100%", maxWidth: 360 }} min={1} placeholder="默认 50" />
                </Form.Item>
                <Form.Item name="maxClusterPoints" label="单簇最大点数（可选）">
                  <InputNumber style={{ width: "100%", maxWidth: 360 }} min={1} />
                </Form.Item>
                <Form.Item name="useXyOnly" label="仅用 XY 距离" valuePropName="checked">
                  <Switch />
                </Form.Item>
              </Space>
            ) : (
              <Space direction="vertical" size="middle" style={{ width: "100%" }}>
                <Form.Item name="normalNeighborCount" label="法向邻点数 k" extra="留空默认 30。">
                  <InputNumber style={{ width: "100%", maxWidth: 360 }} min={3} placeholder="默认 30" />
                </Form.Item>
                <Form.Item name="angleThresholdDeg" label="法向夹角阈值（度）" extra="留空默认 30。">
                  <InputNumber style={{ width: "100%", maxWidth: 360 }} min={0.1} step={1} placeholder="默认 30" />
                </Form.Item>
                <Form.Item name="distanceThreshold" label="生长最大位移（米）" extra="留空默认 0.3。">
                  <InputNumber style={{ width: "100%", maxWidth: 360 }} min={0.0001} step={0.05} placeholder="默认 0.3" />
                </Form.Item>
                <Form.Item name="minRegionPoints" label="有效区域最少点数" extra="留空默认 100。">
                  <InputNumber style={{ width: "100%", maxWidth: 360 }} min={1} placeholder="默认 100" />
                </Form.Item>
                <Form.Item name="maxSeeds" label="自动种子上限" extra="留空默认 50。">
                  <InputNumber style={{ width: "100%", maxWidth: 360 }} min={1} placeholder="默认 50" />
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
      ) : null}

      {isClassifyMode && currentStep === 0 && parentTaskSnapshot ? (
        <Card bordered={false} style={{ boxShadow: "0 1px 2px rgba(0,0,0,0.06)" }}>
          <Space align="center" style={{ marginBottom: 16 }}>
            <LoadingOutlined style={{ fontSize: 22 }} />
            <Typography.Text>
              {classifySubmitting || !submitError
                ? "正在提交并执行 RF 语义分类，请稍候…"
                : "提交失败，请重试。"}
            </Typography.Text>
          </Space>
          {latestChildTask ? (
            <Alert
              type="info"
              message={`子任务 ${latestChildTask.id}`}
              description={
                <div style={{ lineHeight: 1.65 }}>
                  <div>状态：{latestChildTask.status}</div>
                  <div>类型：{latestChildTask.taskKind ?? taskKindForMode}</div>
                  <div>配置：{latestChildTask.derivedSummary ?? "—"}</div>
                </div>
              }
            />
          ) : null}
          {submitError ? (
            <>
              <Alert type="error" message={submitError} style={{ marginTop: 12 }} />
              <Divider plain style={{ margin: "12px 0 0" }} />
              <Space wrap style={{ marginTop: 12 }}>
                <Button type="primary" onClick={() => void handleRfSemanticClassifySubmit()} loading={classifySubmitting}>
                  重试语义分类
                </Button>
                <Link to="/jobs">返回列表</Link>
              </Space>
            </>
          ) : null}
        </Card>
      ) : null}

      {!isClassifyMode && currentStep === 1 ? (
        <Card bordered={false} style={{ boxShadow: "0 1px 2px rgba(0,0,0,0.06)" }}>
          <Space align="center" style={{ marginBottom: 16 }}>
            <LoadingOutlined style={{ fontSize: 22 }} />
            <Typography.Text>子任务处理中，请稍候…（自动刷新状态）</Typography.Text>
          </Space>
          {latestChildTask ? (
            <Alert
              type="info"
              message={`子任务 ${latestChildTask.id}`}
              description={
                <div style={{ lineHeight: 1.65 }}>
                  <div>状态：{latestChildTask.status}</div>
                  <div>类型：{latestChildTask.taskKind ?? taskKindForMode}</div>
                  <div>配置：{latestChildTask.derivedSummary ?? "—"}</div>
                </div>
              }
            />
          ) : null}
        </Card>
      ) : null}

      {((isClassifyMode && currentStep === 1) || (!isClassifyMode && currentStep === 2)) && latestChildTask ? (
        <Card bordered={false} style={{ boxShadow: "0 1px 2px rgba(0,0,0,0.06)" }}>
          {latestChildTask.status === "SUCCEEDED" ? (
            <Result
              icon={<CheckCircleOutlined />}
              status="success"
              title="子任务成功"
              subTitle={
                <>
                  <div style={{ marginBottom: 8 }}>{latestChildTask.derivedSummary ?? "—"}</div>
                  <div style={{ marginTop: 12, marginBottom: 6, fontWeight: 500 }}>输出目录</div>
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
                        latestChildTask.outputBasePath
                          ? { text: latestChildTask.outputBasePath, tooltips: ["复制路径", "已复制"] }
                          : false
                      }
                      style={{
                        fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
                        fontSize: 13,
                        color: "var(--ant-color-text, rgba(0,0,0,0.88))",
                      }}
                    >
                      {latestChildTask.outputBasePath?.trim() ? latestChildTask.outputBasePath : "（后端未返回输出路径）"}
                    </Typography.Text>
                  </div>
                </>
              }
              extra={
                <Space wrap>
                  <Button
                    type="primary"
                    onClick={() => void navigate(`/preview/dual?childTaskId=${latestChildTask.id}`)}
                  >
                    在大屏中查看（派生双窗）
                  </Button>
                  {isClassifyMode ? (
                    <Link to={`/jobs/${latestChildTask.id}/semantic-prune/new`}>语义裁剪</Link>
                  ) : null}
                  <Link to="/jobs">返回任务列表</Link>
                </Space>
              }
            />
          ) : (
            <Result
              status="error"
              title="子任务失败"
              subTitle={latestChildTask.errorMessage ?? latestChildTask.status}
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
