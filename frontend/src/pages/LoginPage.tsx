import { CloudOutlined, LockOutlined, UserOutlined } from "@ant-design/icons";
import { Alert, Button, Card, Form, Input, Typography } from "antd";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginRequest } from "../api/client";
import { setStoredToken, setStoredUsername } from "../auth/tokenStorage";
import "./LoginPage.css";

const SYSTEM_NAME_EN = "PCFPS";
const SYSTEM_NAME_ZH = "点云滤波处理系统";
const SYSTEM_TAGLINE = "面向 LiDAR 点云的上传、滤波、分割、分类与 Web 可视化一体化平台";

export function LoginPage() {
  const navigate = useNavigate();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(values: { username: string; password: string }) {
    setErrorMessage(null);
    setSubmitting(true);
    try {
      const loginResponse = await loginRequest(values.username, values.password);
      setStoredToken(loginResponse.token);
      setStoredUsername(loginResponse.username);
      void navigate("/jobs", { replace: true });
    } catch (errorUnknown) {
      const message = errorUnknown instanceof Error ? errorUnknown.message : "登录失败";
      setErrorMessage(message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="login-page">
      <aside className="login-page__brand" aria-label="系统介绍">
        <div className="login-page__brand-grid" aria-hidden />
        <div className="login-page__brand-content">
          <div className="login-page__logo">
            <CloudOutlined />
          </div>
          <h1 className="login-page__system-name">{SYSTEM_NAME_EN}</h1>
          <p className="login-page__system-subtitle">{SYSTEM_NAME_ZH}</p>
          <p className="login-page__tagline">{SYSTEM_TAGLINE}</p>
          <ul className="login-page__features">
            <li>统计 / 半径离群点滤波（SOR / ROR）</li>
            <li>点云分割与地面分类派生处理</li>
            <li>双窗对比与抽稀三维预览</li>
          </ul>
        </div>
      </aside>

      <main className="login-page__panel">
        <Card className="login-page__card" bordered={false}>
          <Typography.Title level={4} className="login-page__card-title">
            欢迎登录
          </Typography.Title>
          <Typography.Text type="secondary" className="login-page__card-hint">
            使用账号进入 {SYSTEM_NAME_EN} 工作台
          </Typography.Text>
          <Form
            layout="vertical"
            size="large"
            onFinish={(values) => void handleSubmit(values)}
            initialValues={{ username: "", password: "" }}
          >
            <Form.Item label="用户名" name="username" rules={[{ required: true, message: "请输入用户名" }]}>
              <Input prefix={<UserOutlined style={{ color: "#94a3b8" }} />} placeholder="请输入用户名" autoComplete="username" />
            </Form.Item>
            <Form.Item label="密码" name="password" rules={[{ required: true, message: "请输入密码" }]}>
              <Input.Password
                prefix={<LockOutlined style={{ color: "#94a3b8" }} />}
                placeholder="请输入密码"
                autoComplete="current-password"
              />
            </Form.Item>
            {errorMessage && <Alert type="error" message={errorMessage} showIcon style={{ marginBottom: 16 }} />}
            <Form.Item style={{ marginBottom: 0 }}>
              <Button type="primary" htmlType="submit" block loading={submitting} className="login-page__submit">
                登录
              </Button>
            </Form.Item>
          </Form>
        </Card>
      </main>
    </div>
  );
}
