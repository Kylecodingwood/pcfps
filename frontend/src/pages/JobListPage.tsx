import { Link } from "react-router-dom";
import { Alert, Button, Space, Table, Tooltip, Typography } from "antd";
import type { ColumnsType } from "antd/es/table";
import { useEffect, useState } from "react";
import { listTasksRequest } from "../api/client";
import type { TaskResponseDto } from "../api/types";

/**
 * Task list with Ant Design table; compare links to dual preview with taskId.
 */
export function JobListPage() {
  const [taskList, setTaskList] = useState<TaskResponseDto[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function refreshList() {
    setLoadError(null);
    try {
      const page = await listTasksRequest(0, 50);
      setTaskList(page.content);
    } catch (errorUnknown) {
      const message = errorUnknown instanceof Error ? errorUnknown.message : "加载失败";
      setLoadError(message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refreshList();
    const intervalId = window.setInterval(() => void refreshList(), 5000);
    return () => window.clearInterval(intervalId);
  }, []);

  const columns: ColumnsType<TaskResponseDto> = [
    { title: "状态", dataIndex: "status", key: "status", width: 120 },
    {
      title: "配置摘要",
      dataIndex: "filterSummary",
      key: "filterSummary",
      width: 240,
      ellipsis: true,
      render: (_value: string, taskRow) => {
        const taskKindToken = taskRow.taskKind ?? "FILTER";
        const isDerivedTask =
          taskKindToken === "SEGMENT" || taskKindToken === "CLASSIFY" || taskKindToken === "SEMANTIC_PRUNE";
        const summaryText = isDerivedTask ? (taskRow.derivedSummary ?? "—") : (taskRow.filterSummary ?? "—");
        const paramsJson = isDerivedTask ? taskRow.derivedParamsJson : taskRow.filterParamsJson;
        const tooltipTitle =
          paramsJson && Object.keys(paramsJson).length > 0 ? JSON.stringify(paramsJson, null, 2) : summaryText;
        return (
          <Tooltip title={tooltipTitle} placement="topLeft">
            <span style={{ cursor: "default" }}>{summaryText}</span>
          </Tooltip>
        );
      },
    },
    {
      title: "输入 LAS 路径",
      dataIndex: "inputLasPath",
      key: "inputLasPath",
      width: 360,
      ellipsis: true,
      render: (inputLasPath: string) => (
        <Tooltip title={inputLasPath} placement="topLeft">
          <span style={{ cursor: "default" }}>{inputLasPath}</span>
        </Tooltip>
      ),
    },
    {
      title: "创建时间",
      dataIndex: "createdAt",
      key: "createdAt",
      width: 200,
      render: (value: string) => new Date(value).toLocaleString(),
    },
    {
      title: "操作",
      key: "actions",
      width: 220,
      fixed: "right",
      render: (_value, taskRow) => {
        if (taskRow.status !== "SUCCEEDED") {
          return <span style={{ color: "#999" }}>—</span>;
        }
        const taskKindToken = taskRow.taskKind ?? "FILTER";
        if (taskKindToken === "SEGMENT" || taskKindToken === "CLASSIFY") {
          return (
            <Space size="small" wrap>
              <Link to={`/preview/dual?childTaskId=${taskRow.id}`}>派生双窗</Link>
              {taskKindToken === "CLASSIFY" ? (
                <Link to={`/jobs/${taskRow.id}/semantic-prune/new`}>语义精简</Link>
              ) : null}
            </Space>
          );
        }
        if (taskKindToken === "SEMANTIC_PRUNE") {
          return (
            <Space size="small" wrap>
              <Link to={`/preview/dual?pruneTaskId=${taskRow.id}`}>语义精简双窗</Link>
            </Space>
          );
        }
        return (
          <Space size="small" wrap>
            <Link to={`/preview/dual?taskId=${taskRow.id}`}>对比预览</Link>
            <Link to={`/jobs/${taskRow.id}/segment/new`}>分割</Link>
            <Link to={`/jobs/${taskRow.id}/classify/new`}>语义分类</Link>
          </Space>
        );
      },
    },
  ];

  return (
    <div>
      <Typography.Title level={3} style={{ marginTop: 0 }}>
        处理任务列表
      </Typography.Title>
      <Space style={{ marginBottom: 16 }}>
        <Link to="/jobs/new">
          <Button type="primary">新建处理</Button>
        </Link>
        <Button onClick={() => void refreshList()}>刷新</Button>
      </Space>
      {loadError && <Alert type="error" message={loadError} style={{ marginBottom: 16 }} />}
      <Table<TaskResponseDto>
        rowKey="id"
        loading={loading}
        columns={columns}
        dataSource={taskList}
        pagination={false}
        scroll={{ x: 1240 }}
      />
    </div>
  );
}
