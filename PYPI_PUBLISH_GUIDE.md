# PyPI 发布指南（注册 / 2FA / 打包 / 上传）

本文档用于记录如何将本项目发布到 PyPI，并确保任何人都可以通过 pip 安装使用。

PyPI 官网：https://pypi.org/

## 1. 注册与登录

1. 打开注册页面：https://pypi.org/account/register/
2. 按页面提示填写用户名、邮箱、密码并完成邮箱验证。
3. 登录：https://pypi.org/account/login/

## 2. 配置双重认证（2FA，TOTP）

PyPI 支持基于 TOTP 标准的认证应用（如 Google Authenticator、Microsoft Authenticator、1Password 等）。

1. 进入账号安全设置（登录后）：https://pypi.org/manage/account/#two-factor-authentication
2. 选择使用认证应用（TOTP）
3. 用认证应用扫描二维码或手动输入密钥
4. 输入认证应用生成的 6 位动态验证码，完成启用
5. 保存 Recovery codes（恢复码），建议离线保存

安全提示：TOTP 密钥等同于账户的 2FA “钥匙”，不要在聊天、截图或任何不安全渠道传播。

## 3. 本地环境准备（推荐 Python 3.11/3.12 + venv）

建议使用虚拟环境进行构建与上传。

```bash
cd /Users/chongwen002/project/xiaokeer-gen-project-tree
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
```

如果你的系统 Python/pip 因动态库导致安装失败，优先改用一个干净可用的 Python 版本（例如通过 Homebrew 安装 python@3.12）后再创建 venv。

## 4. 创建 PyPI API Token（用于上传）

建议使用 API Token 上传，而不是账户密码。

1. 打开 Token 页面：https://pypi.org/manage/account/#api-tokens
2. Create token
3. Scope 建议首次选择 Entire account（后续可以改为只绑定到某个项目）
4. 复制并妥善保存 Token（通常只显示一次）

上传时的用户名固定为：

`__token__`

密码为你创建的 Token。

## 5. 打包构建（生成 dist/）

安装构建与上传工具：

```bash
python -m pip install -U build twine
```

构建发布产物：

```bash
rm -rf dist build
python -m build
```

生成文件通常位于 dist/：
- *.whl
- *.tar.gz

构建产物自检：

```bash
python -m twine check dist/*
```

## 6. 上传到 PyPI（正式发布）

```bash
python -m twine upload dist/*
```

出现提示时：
- username：`__token__`
- password：粘贴你的 PyPI API Token

## 7. 发布后验证（建议）

在一个干净的虚拟环境里验证安装与命令可用：

```bash
python3 -m venv /tmp/xgentree-verify
source /tmp/xgentree-verify/bin/activate
pip install -U pip
pip install xiaokeer.gen.project.tree
xgentree -h
```

## 8. 常见问题

### 8.1 包名已被占用

如果上传时报错提示项目已存在且无权限：
- 说明包名已被其他账号占用，或你不是该项目的维护者
- 需要更换包名，或在 PyPI 上确认项目归属后再发布

### 8.2 Trusted Publishing 警告

twine 上传时可能会看到 “This environment is not supported for trusted publishing”，这不影响 token 方式上传成功。
Trusted Publishing 是另一种基于 OIDC 的自动化发布方式，通常配合 CI（如 GitHub Actions）使用。

