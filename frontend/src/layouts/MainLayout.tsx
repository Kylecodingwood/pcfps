import {
  CloudOutlined,
  ClusterOutlined,
  DeploymentUnitOutlined,
  LogoutOutlined,
  PlayCircleOutlined,
  TableOutlined,
  UserOutlined,
} from "@ant-design/icons";
import { Breadcrumb, Button, Layout, Menu, theme, Typography } from "antd";
import { useMemo, useState } from "react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import { clearStoredToken, getStoredUsername } from "../auth/tokenStorage";

const { Header, Sider, Content } = Layout;

/**
 * Ant Design shell: side navigation for jobs vs preview flows.
 */
export function MainLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const [displayUsername] = useState(() => getStoredUsername());
  const {
    token: { colorBgContainer, borderRadiusLG, colorTextSecondary },
  } = theme.useToken();

  const isPreviewRoute = location.pathname.startsWith("/preview");

  const selectedMenuKeyList = useMemo(() => {
    const pathname = location.pathname;
    if (pathname.startsWith("/jobs/new")) {
      return ["/jobs/new"];
    }
    if (/\/jobs\/[^/]+\/segment\/new/.test(pathname)) {
      return ["/process/segment"];
    }
    if (/\/jobs\/[^/]+\/classify\/new/.test(pathname)) {
      return ["/process/classify"];
    }
    if (pathname.startsWith("/process/segment")) {
      return ["/process/segment"];
    }
    if (pathname.startsWith("/process/classify")) {
      return ["/process/classify"];
    }
    if (pathname.startsWith("/jobs")) {
      return ["/jobs"];
    }
    if (pathname.startsWith("/preview/single")) {
      return ["/preview/single"];
    }
    if (pathname.startsWith("/preview/dual")) {
      return ["/preview/dual"];
    }
    return [pathname];
  }, [location.pathname]);

  const breadcrumbItems = useMemo(() => {
    const pathname = location.pathname;
    const homeCrumb = { title: <Link to="/jobs">首页</Link> };
    if (pathname.startsWith("/jobs/new")) {
      return [homeCrumb, { title: "新建处理" }];
    }
    if (/\/jobs\/[^/]+\/segment\/new/.test(pathname)) {
      return [homeCrumb, { title: "点云分割" }, { title: "新建分割" }];
    }
    if (/\/jobs\/[^/]+\/classify\/new/.test(pathname)) {
      return [homeCrumb, { title: "点云分类" }, { title: "新建分类" }];
    }
    if (pathname.startsWith("/process/segment")) {
      return [homeCrumb, { title: "点云分割" }];
    }
    if (pathname.startsWith("/process/classify")) {
      return [homeCrumb, { title: "点云分类" }];
    }
    if (pathname.startsWith("/jobs")) {
      return [homeCrumb, { title: "任务列表" }];
    }
    if (pathname.startsWith("/preview/single")) {
      return [homeCrumb, { title: "单文件抽稀预览" }];
    }
    if (pathname.startsWith("/preview/dual")) {
      return [homeCrumb, { title: "点云工作台（双窗）" }];
    }
    return [homeCrumb];
  }, [location.pathname]);

  return (
    <Layout style={{ minHeight: "100vh", height: "100%" }}>
      <Sider breakpoint="lg" collapsedWidth={0} width={220}>
        <div
          style={{
            height: 48,
            margin: 12,
            color: "#fff",
            fontWeight: 600,
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <CloudOutlined /> PCFPS
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={selectedMenuKeyList}
          items={[
            {
              key: "group-jobs",
              label: "处理任务",
              type: "group",
              children: [
                {
                  key: "/jobs",
                  icon: <TableOutlined />,
                  label: "任务列表",
                  onClick: () => void navigate("/jobs"),
                },
                {
                  key: "/jobs/new",
                  icon: <PlayCircleOutlined />,
                  label: "新建处理",
                  onClick: () => void navigate("/jobs/new"),
                },
              ],
            },
            {
              key: "group-process",
              label: "点云处理",
              type: "group",
              children: [
                {
                  key: "/process/segment",
                  icon: <ClusterOutlined />,
                  label: "点云分割",
                  onClick: () => void navigate("/process/segment"),
                },
                {
                  key: "/process/classify",
                  icon: <DeploymentUnitOutlined />,
                  label: "语义分类",
                  onClick: () => void navigate("/process/classify"),
                },
              ],
            },
            {
              key: "group-preview",
              label: "点云预览",
              type: "group",
              children: [
                {
                  key: "/preview/single",
                  label: "单文件抽稀",
                  onClick: () => void navigate("/preview/single"),
                },
                {
                  key: "/preview/dual",
                  label: "点云工作台（双窗）",
                  onClick: () => void navigate("/preview/dual"),
                },
              ],
            },
          ]}
        />
      </Sider>
      <Layout
        style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0, minWidth: 0, height: "100%" }}
      >
        <Header
          style={{
            padding: "0 16px",
            background: colorBgContainer,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: 16,
            flexShrink: 0,
          }}
        >
          <div style={{ minWidth: 0, flex: 1 }}>
            <Breadcrumb items={breadcrumbItems} style={{ minWidth: 0 }} />
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 12, flexShrink: 0 }}>
            {displayUsername ? (
              <span style={{ display: "inline-flex", alignItems: "center", gap: 6, maxWidth: 200 }}>
                <UserOutlined style={{ color: colorTextSecondary }} aria-hidden />
                <Typography.Text type="secondary" ellipsis style={{ maxWidth: 176 }}>
                  {displayUsername}
                </Typography.Text>
              </span>
            ) : null}
            <Button
              type="text"
              icon={<LogoutOutlined />}
              onClick={() => {
                clearStoredToken();
                void navigate("/login", { replace: true });
              }}
            >
              退出
            </Button>
          </div>
        </Header>
        <Content
          style={{
            flex: 1,
            margin: isPreviewRoute ? 8 : 12,
            display: "flex",
            flexDirection: "column",
            minHeight: 0,
            overflow: "hidden",
          }}
        >
          {isPreviewRoute ? (
            <div
              style={{
                flex: 1,
                minHeight: 0,
                display: "flex",
                flexDirection: "column",
                padding: 4,
                overflowX: "hidden",
                overflowY: "auto",
              }}
            >
              <Outlet />
            </div>
          ) : (
            <div
              style={{
                padding: 20,
                flex: 1,
                minHeight: 0,
                overflow: "auto",
                background: colorBgContainer,
                borderRadius: borderRadiusLG,
              }}
            >
              <Outlet />
            </div>
          )}
        </Content>
      </Layout>
    </Layout>
  );
}
