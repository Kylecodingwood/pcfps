import { Link } from "react-router-dom";
import { Alert, Space, Table, Typography } from "antd";
import type { ColumnsType } from "antd/es/table";
import { useCallback, useEffect, useState } from "react";
import { listTasksRequest } from "../api/client";
import type { TaskResponseDto } from "../api/types";

/**
 * Hub: pick a succeeded filter parent task to open the segment wizard.
 */
export function SegmentHubPage() {
  const [parentTaskList, setParentTaskList] = useState<TaskResponseDto[]>([]);
  const [loadErrorMessage, setLoadErrorMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshParentTaskList = useCallback(async () => {
    setLoadErrorMessage(null);
    try {
      const page = await listTasksRequest(0, 100);
      const eligibleParentList = page.content.filter((taskRow) => {
        const kindToken = taskRow.taskKind ?? "FILTER";
        return kindToken === "FILTER" && taskRow.status === "SUCCEEDED";
      });
      setParentTaskList(eligibleParentList);
    } catch (errorUnknown) {
      const message = errorUnknown instanceof Error ? errorUnknown.message : "加载失败";
      setLoadErrorMessage(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshParentTaskList();
  }, [refreshParentTaskList]);

  const columns: ColumnsType<TaskResponseDto> = [
    {
      title: "滤波摘要",
      dataIndex: "filterSummary",
      key: "filterSummary",
      ellipsis: true,
      width: 260,
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
      width: 140,
      render: (_value, taskRow) => (
        <Link to={`/jobs/${taskRow.id}/segment/new`}>去分割</Link>
      ),
    },
  ];

  return (
    <div>
      <Typography.Title level={3} style={{ marginTop: 0 }}>
        点云分割
      </Typography.Title>
      <Typography.Paragraph type="secondary" style={{ marginBottom: 16 }}>
        仅列出已成功完成的<strong>滤波任务</strong>；分割默认基于该任务的 FILTERED_LAS。也可从任务列表或滤波成功页进入。
      </Typography.Paragraph>
      {loadErrorMessage ? <Alert type="error" message={loadErrorMessage} style={{ marginBottom: 16 }} /> : null}
      <Table<TaskResponseDto>
        rowKey="id"
        loading={loading}
        columns={columns}
        dataSource={parentTaskList}
        pagination={false}
        locale={{ emptyText: "暂无已成功的滤波任务，请先完成滤波。" }}
      />
      <Space style={{ marginTop: 16 }}>
        <Link to="/jobs">返回任务列表</Link>
      </Space>
    </div>
  );
}
