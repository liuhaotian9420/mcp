# ❓ 常见问题解答（FAQ）

本节收录了使用 MCP-CLI 及相关工具时的常见问题与解决方法。

---

## 1. 工具函数未被发现/未暴露？
- 请确保函数有**类型注解**和**docstring**。
- 检查 `--source-path` 路径是否正确，且文件已保存。
- 若指定了 `--target-functions`，请确保函数名拼写无误。

## 2. 端口冲突或服务无法启动？
- 检查端口是否被占用，可更换 `--port` 参数。
- Windows 下有时需以管理员权限运行。

## 3. 打包后服务无法运行？
- 检查 `start.sh` 是否有执行权限（Linux/macOS）。
- 确认依赖已正确安装，可参考生成的 `requirements.txt`。

## 4. 如何调试工具函数？
- 可直接用 Python 运行工具文件进行单元测试。
- 启动服务时加 `--log-level DEBUG` 查看详细日志。

## 5. 如何自定义路由或多文件组合？
- 传入目录路径，自动发现所有 Python 文件并挂载。
- 详见 `docs/architecture-modes.md`。

## 6. 依赖安装失败/版本冲突？
- 建议使用虚拟环境（如 venv、conda、poetry）。
- 检查 `requirements.txt`，逐项排查冲突。

## 7. 传输协议相关问题

### 7.1 服务在云环境中无法正常工作？
**问题**: 服务在 Knative、Istio 或其他云原生环境中出现连接问题。

**解决方案**:
- 检查是否使用了 `--legacy-sse` 参数
- Legacy SSE 模式在云环境中存在已知兼容性问题
- 移除 `--legacy-sse` 参数，使用默认的 Streamable HTTP 传输协议：
```bash
# ❌ 有问题的命令
mcpy-cli run --source-path tools/ --legacy-sse

# ✅ 正确的命令
mcpy-cli run --source-path tools/
```

### 7.2 什么时候应该使用 `--legacy-sse`？
**回答**: 
- `--legacy-sse` 是已弃用的传输模式，仅用于向后兼容
- 只在以下情况下使用：
  - 现有系统严重依赖 SSE 传输模式
  - 正在从旧版本进行渐进式迁移
- **新项目绝不应使用** `--legacy-sse`

### 7.3 如何从 Legacy SSE 迁移到默认传输协议？
**迁移步骤**:
1. 在测试环境中移除 `--legacy-sse` 参数
2. 验证所有功能正常工作
3. 更新部署脚本和文档
4. 在生产环境中应用更改

```bash
# 迁移前
mcpy-cli run --source-path tools/ --legacy-sse --port 8080

# 迁移后
mcpy-cli run --source-path tools/ --port 8080
```

### 7.4 Legacy SSE 和默认传输协议有什么区别？
**主要差异**:
- **默认 Streamable HTTP**: 单端点，云兼容，现代化
- **Legacy SSE**: 双端点，云环境问题，已弃用

详见文档：`docs/architecture.md` 中的"传输协议架构"部分。

## 8. 还有其他问题？
- 可查阅主文档、最佳实践或在 issue 区提问。

---

如需补充更多问题，欢迎 PR！
