import { Alert, Button, Card, Form, InputNumber, Result, Space, Typography } from "antd";
import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { createSemanticPruneJobRequest, getTaskRequest } from "../api/client";
import type { TaskResponseDto } from "../api/types";

type SemanticPruneFormValues = {
  groundVoxelSizeM: number;
};

/**
 * Creates a semantic-prune child task from a succeeded classify task (drop 3/4, voxel-thin ground).
 *
 * @author PCFPS
 * @date 2026-05-15
 */
export function SemanticPruneWizardPage() {
  const navigate = useNavigate();
  const { classifyTaskId } = useParams<{ classifyTaskId: string }>();
  const [parentTaskSnapshot, setParentTaskSnapshot] = useState<TaskResponseDto | null>(null);
  const [parentLoadError, setParentLoadError] = useState<string | null>(null);
  const [createdTask, setCreatedTask] = useState<TaskResponseDto | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!classifyTaskId || classifyTaskId.trim() === "") {
      setParentLoadError("缺少分类任务 ID");
      return;
    }
    let cancelled = false;
    void (async () => {
      setParentLoadError(null);
      try {
        const snapshot = await getTaskRequest(classifyTaskId.trim());
        if (!cancelled) {
          setParentTaskSnapshot(snapshot);
        }
      } catch (errorUnknown) {
        if (!cancelled) {
          const message = errorUnknown instanceof Error ? errorUnknown.message : "加载父任务失败";
          setParentLoadError(message);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [classifyTaskId]);

  const parentReady =
    parentTaskSnapshot != null &&
    parentTaskSnapshot.status === "SUCCEEDED" &&
    parentTaskSnapshot.taskKind === "CLASSIFY";

  return (
    <div>
      <Typography.Title level={3} style={{ marginTop: 0 }}>
        语义精简（删 3/4 + 地面体素）
      </Typography.Title>
      <Space direction="vertical" size="middle" style={{ width: "100%" }}>
        <Link to="/jobs">返回任务列表</Link>
        {parentLoadError ? <Alert type="error" message={parentLoadError} /> : null}
        {parentTaskSnapshot && !parentReady ? (
          <Alert
            type="warning"
            message="父任务须为已成功完成的「分类」子任务"
            description={`当前状态：${parentTaskSnapshot.status}，类型：${parentTaskSnapshot.taskKind ?? "—"}`}
          />
        ) : null}
        {parentTaskSnapshot && parentReady ? (
          <Card size="small" title="父分类任务">
            <Typography.Paragraph style={{ marginBottom: 8 }}>
              <strong>ID</strong>：{parentTaskSnapshot.id}
            </Typography.Paragraph>
            <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
              {parentTaskSnapshot.derivedSummary ?? "—"}
            </Typography.Paragraph>
          </Card>
        ) : null}
        {createdTask ? (
          <Result
            status="success"
            title="已创建语义精简任务"
            subTitle={`子任务 ID：${createdTask.id}`}
            extra={[
              <Button type="primary" key="dual" onClick={() => void navigate(`/preview/dual?pruneTaskId=${createdTask.id}`)}>
                打开语义精简双窗
              </Button>,
              <Button key="jobs" onClick={() => void navigate("/jobs")}>
                返回列表
              </Button>,
            ]}
          />
        ) : (
          <Card title="参数" style={{ maxWidth: 520 }}>
            <Form<SemanticPruneFormValues>
              layout="vertical"
              initialValues={{ groundVoxelSizeM: 0.5 }}
              onFinish={async (values) => {
                if (!classifyTaskId || classifyTaskId.trim() === "") {
                  return;
                }
                setSubmitError(null);
                setSubmitting(true);
                try {
                  const created = await createSemanticPruneJobRequest(classifyTaskId.trim(), {
                    groundVoxelSizeM: values.groundVoxelSizeM,
                  });
                  setCreatedTask(created);
                } catch (errorUnknown) {
                  const message = errorUnknown instanceof Error ? errorUnknown.message : "提交失败";
                  setSubmitError(message);
                } finally {
                  setSubmitting(false);
                }
              }}
            >
              <Form.Item
                label="地面 XY 体素边长（米）"
                name="groundVoxelSizeM"
                rules={[{ required: true, message: "请输入体素边长" }]}
                extra="默认 0.5：同一水平格内地面只保留一点（Z 最低）；建筑（2）全保留；删除植被（3）与其它（4）。"
              >
                <InputNumber min={0.05} max={50} step={0.05} style={{ width: "100%" }} />
              </Form.Item>
              {submitError ? <Alert type="error" message={submitError} style={{ marginBottom: 12 }} /> : null}
              <Button type="primary" htmlType="submit" loading={submitting} disabled={!parentReady}>
                创建语义精简任务
              </Button>
            </Form>
          </Card>
        )}
      </Space>
    </div>
  );
}
