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

### 3.1 Python 环境与虚拟环境说明

- 为什么需要 venv：避免污染系统 Python，避免不同项目依赖冲突，发布构建过程也更可复现。
- 选择 Python 版本：建议优先使用稳定版本（3.11/3.12）。发布到 PyPI 时不要求本地版本与用户一致，但要求满足 `pyproject.toml` 的 `requires-python`。

检查当前解释器与 pip：

```bash
python -V
python -m pip --version
```

常见问题：系统/发行版会禁止对系统 Python 直接 pip 安装（PEP 668，报错 `externally-managed-environment`）。解决方式是使用 venv 或 pipx：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
```

退出虚拟环境：

```bash
deactivate
```

建议不要把 `.venv/` 提交到仓库，应该加入 `.gitignore`。

macOS 特殊情况：如果遇到 `pyexpat` / `libexpat` 相关的 ImportError，通常需要安装新版 expat 并让 Python 运行时优先使用它：

```bash
brew install expat
export DYLD_LIBRARY_PATH=/opt/homebrew/opt/expat/lib:$DYLD_LIBRARY_PATH
```

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
rm -rf dist build *.egg-info src/*.egg-info
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

官方 Python Packaging 指南推荐使用 `build` 生成发行包，并使用 `twine` 上传。发布前必须先运行 `twine check`。

```bash
python -m twine upload dist/*
```

出现提示时：
- username：`__token__`
- password：粘贴你的 PyPI API Token

### 6.1 使用本地 .env 保存上传凭据

可以在项目根目录创建本地 `.env`，避免每次发布都手动输入 token：

```bash
TWINE_USERNAME=__token__
TWINE_PASSWORD=pypi-your-token
```

`.env` 已被 `.gitignore` 忽略，不要提交。文档中只能说明 `.env` 的字段名和读取方式，不能写入真实 token。

发布前读取 `.env`：

```bash
set -a
source .env
set +a
python -m twine upload dist/*
```

发布前确认 token 没有被跟踪：

```bash
git status --short
git ls-files .env
```

`git ls-files .env` 应该没有任何输出。

### 6.2 发布 1.0.2 的完整命令

```bash
cd /Users/chongwen002/project/xiaokeer-gen-project-tree
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip build twine
python -m unittest discover tests -v
rm -rf dist build *.egg-info src/*.egg-info
python -m build
python -m twine check dist/*
set -a
source .env
set +a
python -m twine upload dist/*
```

## 7. 发布后验证（建议）

在一个干净的虚拟环境里验证安装与命令可用：

```bash
python3 -m venv /tmp/xgentree-verify
source /tmp/xgentree-verify/bin/activate
pip install -U pip
pip install xiaokeer.gen.project.tree
xgentree -h
xgentree --version
```

验证指定版本：

```bash
python3 -m venv /tmp/xgentree-verify-1.0.2
source /tmp/xgentree-verify-1.0.2/bin/activate
pip install -U pip
pip install xiaokeer.gen.project.tree==1.0.2
xgentree --help
xgentree --version
xgentree -c /path/to/config.json --output-format none
xgentree -c /path/to/config.json --output-format both
```

## 8. 常见问题

### 8.1 包名已被占用

如果上传时报错提示项目已存在且无权限：
- 说明包名已被其他账号占用，或你不是该项目的维护者
- 需要更换包名，或在 PyPI 上确认项目归属后再发布

### 8.2 Trusted Publishing 警告

twine 上传时可能会看到 “This environment is not supported for trusted publishing”，这不影响 token 方式上传成功。
Trusted Publishing 是另一种基于 OIDC 的自动化发布方式，通常配合 CI（如 GitHub Actions）使用。
