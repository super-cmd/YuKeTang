# 雨课堂辅助工具

## 项目简介

这是一个功能强大的雨课堂平台辅助工具，旨在帮助用户高效完成在线学习任务。该工具可以自动处理各种学习任务，包括观看视频、阅读图文资料、完成作业等。

## 主要功能

- **用户信息获取**：自动获取并显示当前登录用户的基本信息
- **课程列表管理**：获取并展示用户所有课程列表，支持选择特定课程
- **学习任务解析**：自动解析选定课程的所有学习任务并分类显示
- **视频课程自动观看**：
  - 支持倍速播放（默认2倍速，可配置）
  - 自动发送心跳包模拟观看过程
  - 支持视频进度跟踪，避免重复观看
- **图文资料自动阅读**：自动标记图文资料为已读状态
- **作业自动完成**：
  - 集成题库功能，自动获取题目答案
  - 支持多种题型（单选、多选、判断、填空等）
  - 自动提交答案
- **缓存管理**：智能缓存已完成的任务，避免重复处理
- **日志系统**：完整的操作日志记录，方便追踪处理过程
- **灵活配置**：支持通过配置文件或环境变量进行个性化设置

## 系统架构

```
YuKeTang/
├── main.py              # 主程序入口
├── config.py            # 配置文件
├── config.yaml          # YAML配置文件（可选）
├── api/                 # API接口模块
│   ├── courses.py       # 课程相关API
│   ├── userinfo.py      # 用户信息API
│   ├── homework.py      # 作业相关API
│   └── WebSocket.py     # WebSocket连接处理
├── parser/              # 解析器模块
│   └── task_parser.py   # 任务点解析器
└── utils/               # 工具模块
    ├── cache.py         # 缓存管理
    ├── headers.py       # HTTP请求头处理
    ├── helpers.py       # 辅助函数
    ├── logger.py        # 日志系统
    ├── question_bank.py # 题库接口处理
    ├── request_helper.py # HTTP请求处理
    ├── select.py        # 选择处理工具
    └── time.py          # 时间处理工具
```

## 安装说明

### 环境要求

- Python 3.8 或更高版本
- pip 包管理器

### 安装步骤

```bash
# 1. 克隆项目到本地
git clone <repository-url>
cd YuKeTang

# 2. 安装依赖
pip install -r requirements.txt

# 3. 准备Cookie文件
# 从雨课堂网页版获取Cookie并保存为cookie.json文件

# 4. 运行程序
python main.py
```

## 使用方法

1. **准备Cookie**：从雨课堂网站获取有效的Cookie并保存到cookie.json文件
2. **配置参数**（可选）：
   - 方法一：修改config.yaml文件
   - 方法二：设置环境变量（前缀为YUKETANG_）
   - 方法三：直接修改config.py文件
3. **配置题库Token**（可选）：
   - 访问题库官网获取Token：https://frpclient04.xhyonline.com:9311
   - 在config.yaml中配置QUESTION_BANK_TOKEN，或通过环境变量YUKETANG_QUESTION_BANK_TOKEN设置
4. **运行程序**：执行`python main.py`启动程序
5. **选择课程**：根据提示选择需要处理的课程（支持选择多个课程）
6. **自动处理**：程序会自动处理所选课程的各种学习任务

## 配置说明

项目支持多种配置方式，优先级从高到低依次为：
1. 环境变量
2. YAML配置文件(config.yaml)
3. Python配置文件(config.py)

### 可配置参数

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| APP_NAME | YuKeTang App | 应用程序名称 |
| APP_VERSION | 1.0.0 | 应用程序版本 |
| API_BASE_URL | https://www.yuketang.cn | 雨课堂API基础URL |
| API_TIMEOUT | 30 | API请求超时时间（秒） |
| API_RETRY_COUNT | 3 | API重试次数 |
| API_RETRY_DELAY | 1.0 | API重试延迟（秒） |
| COOKIE_FILE_PATH | cookie.json | Cookie文件路径 |
| DEFAULT_LOG_DIR | logs | 默认日志目录 |
| DEFAULT_LOG_FILE | logs/app.log | 默认日志文件路径 |
| DEFAULT_LOG_LEVEL | INFO | 默认日志级别 |
| DEFAULT_COURSE_INDEX | 7 | 默认选择的课程索引 |
| AUTO_SAVE_TASKS | false | 是否自动保存任务文件 |
| HEARTBEAT_INTERVAL | 30.0 | 心跳包发送间隔（秒） |
| VIDEO_SPEED | 2.0 | 视频播放倍速 |
| QUESTION_BANK_TOKEN | 无（需用户自行购买获取） | 题库接口认证Token |

### 配置示例

#### YAML配置文件(config.yaml)
```yaml
# 刷课配置
VIDEO_SPEED: 3.0
HEARTBEAT_INTERVAL: 20.0

# 日志配置
DEFAULT_LOG_LEVEL: DEBUG

# 题库配置 (需要自行购买获取)
# QUESTION_BANK_TOKEN: "your_token_here"
```

#### 环境变量配置
```bash
# Windows
set YUKETANG_VIDEO_SPEED=3.0
set YUKETANG_HEARTBEAT_INTERVAL=20.0

# Linux/Mac
export YUKETANG_VIDEO_SPEED=3.0
export YUKETANG_HEARTBEAT_INTERVAL=20.0
```

## 注意事项

1. 请确保使用的Cookie有效且未过期
2. 使用过程中请遵守雨课堂平台的相关规定
3. 本工具仅供学习交流使用，请勿用于其他用途
4. 如遇到问题可查看日志文件进行排查

## 许可证

本项目采用MIT许可证。