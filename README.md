# 雨课堂辅助工具

## 项目简介

这是一个功能强大的雨课堂平台辅助工具，不仅能够获取用户信息、课程列表和学习日志，还能够自动处理各种任务点，如观看视频课程、阅读图文资料等，帮助用户高效完成在线学习任务。

同时集成了题库功能，可以通过题库官网 `frpclient04.xhyonline.com:9311` 查询题目答案。

## 功能特点

- ✅ 获取用户信息（用户名、用户ID等）
- ✅ 获取课程列表及教师信息
- ✅ 获取指定课程的学习日志
- ✅ 解析任务点并按类型分类（课件、公告、课堂等）
- ✅ 自动观看视频课程（支持倍速播放）
- ✅ 自动阅读图文资料
- ✅ 自动处理课件任务
- ✅ 题库功能支持（通过官网 frpclient04.xhyonline.com:9311）
- ✅ 任务数据可视化和统计
- ✅ 进度跟踪和缓存，避免重复处理
- ✅ 完整的日志记录系统
- ✅ 灵活的配置选项，支持环境变量覆盖
- ✅ Cookie文件选择功能，支持多账户

## 项目结构

```
YuKeTang/
├── main.py              # 主程序入口
├── README.md            # 项目文档
├── requirements.txt     # 项目依赖
├── config.py            # 配置文件
├── .gitignore           # Git忽略文件
├── cache/               # 缓存目录
├── api/                 # API模块
│   ├── __init__.py
│   ├── courses.py       # 课程相关API
│   ├── userinfo.py      # 用户信息API
│   └── WebSocket.py     # WebSocket连接处理
├── parser/              # 解析器模块
│   ├── __init__.py
│   └── task_parser.py   # 任务点解析器
├── utils/               # 工具模块
│   ├── __init__.py
│   ├── helpers.py       # 辅助函数
│   ├── headers.py       # HTTP请求头处理
│   ├── logger.py        # 日志系统
│   ├── time.py          # 时间处理工具
│   ├── cache.py         # 缓存管理
│   ├── request_helper.py # HTTP请求处理
│   ├── question_bank.py # 题库接口处理
│   └── select.py        # 选择处理工具
```

## 安装说明

### 前提条件

- Python 3.8 或更高版本
- pip 包管理器

### 安装依赖

```bash
# 克隆仓库后进入项目目录
cd YuKeTang

# 安装依赖
pip install -r requirements.txt
```

## 使用方法

### 基本使用

1. 运行主程序：
   ```bash
   python main.py
   ```

2. 程序启动后，会提示选择 Cookie 文件

3. 选择要处理的课程（可使用逗号分隔多个课程，或使用短横线表示范围）

4. 程序会自动开始处理选中课程的任务

### 配置选项

项目支持通过 `config.py` 文件或环境变量进行配置：

| 配置项 | 类型 | 默认值 | 环境变量 | 描述 |
|--------|------|--------|----------|------|
| APP_NAME | str | "YuKeTang App" | YUKETANG_APP_NAME | 应用程序名称 |
| APP_VERSION | str | "1.0.0" | YUKETANG_APP_VERSION | 应用程序版本 |
| API_BASE_URL | str | "https://www.yuketang.cn" | YUKETANG_API_BASE_URL | API 基础 URL |
| API_TIMEOUT | int | 30 | YUKETANG_API_TIMEOUT | API 请求超时时间（秒） |
| DEFAULT_LOG_LEVEL | str | "INFO" | YUKETANG_DEFAULT_LOG_LEVEL | 默认日志级别 |
| DEFAULT_COURSE_INDEX | int | 7 | YUKETANG_DEFAULT_COURSE_INDEX | 默认选择的课程索引 |
| AUTO_SAVE_TASKS | bool | False | YUKETANG_AUTO_SAVE_TASKS | 是否自动保存任务文件 |
| HEARTBEAT_INTERVAL | float | 30.0 | YUKETANG_HEARTBEAT_INTERVAL | 心跳包发送间隔（秒） |
| VIDEO_SPEED | float | 2.0 | YUKETANG_VIDEO_SPEED | 视频播放倍速 |
| QUESTION_BANK_TOKEN | str | "3d749979-90d1-4751-a10a-8c4e755aed1a" | YUKETANG_QUESTION_BANK_TOKEN | 题库接口认证Token |

示例：通过环境变量设置题库Token：
```bash
# Windows
set YUKETANG_QUESTION_BANK_TOKEN=your_token_here

# Linux/Mac
YUKETANG_QUESTION_BANK_TOKEN=your_token_here python main.py
```

## 模块说明

### 1. API模块

负责与雨课堂API进行交互，获取各种数据。

- `CourseAPI`: 课程相关API，包括获取课程列表、学习日志等
- `UserAPI`: 用户信息API，获取当前用户的基本信息

### 2. 解析器模块

负责解析API返回的数据，特别是对任务点进行分类和结构化处理。

- `TaskParser`: 任务点解析器，将原始学习日志数据转换为结构化的任务数据

### 3. 工具模块

提供各种通用功能支持。

- `helpers`: 辅助函数，如文件操作、数据解压等
- `headers`: HTTP请求头管理
- `logger`: 日志系统，支持控制台和文件日志
- `time`: 时间处理工具
- `question_bank`: 题库接口处理模块，用于查询题目答案

## 题库功能

本项目集成了题库查询功能，可以通过访问题库官网 `frpclient04.xhyonline.com:9311` 获取题目答案。题库支持多种题型，包括但不限于：

- 单选题
- 多选题
- 判断题
- 填空题
- 简答题

题库功能通过 [utils/question_bank.py](utils/question_bank.py) 模块实现，主要包括以下功能：

1. 题目数据预处理 ([prepare_question_data](utils/question_bank.py#L119-L149))
2. 向题库服务器查询答案 ([query_question_bank](utils/question_bank.py#L49-L73))
3. 格式化答案以适配不同题型 ([get_submit_answer](utils/question_bank.py#L9-L46))

题库接口需要使用授权Token进行身份验证，默认Token已在 [config.py](config.py) 中配置，用户可以根据需要进行修改。

## 注意事项

1. **Cookie准备**：使用前请确保已准备好有效的Cookie文件（从雨课堂网页版获取）
2. **Cookie有效期**：Cookie有一定的有效期，过期后需要重新获取
3. **课程选择**：默认情况下，程序将选择第8个课程（索引7），但会提示用户确认或选择其他课程
4. **任务处理**：
   - 视频任务会自动发送心跳包模拟观看
   - 图文任务会自动标记为已读
   - 作业和考试任务仅显示信息，需要手动完成
5. **网络环境**：使用本工具需要稳定的网络连接
6. **使用风险**：本工具仅用于学习和研究目的，使用本工具可能违反雨课堂的用户协议，请谨慎使用

## 开发指南

### 添加新功能

1. 在相应模块中添加新的类或函数
2. 确保添加适当的类型注解和文档字符串
3. 在main.py中集成新功能
4. 更新README.md文档

### 代码风格

- 遵循PEP 8编码规范
- 使用类型注解提高代码可读性
- 为所有公共函数和类添加文档字符串
- 使用日志替代print语句

## 许可证

本项目采用MIT许可证。

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 联系方式

如有问题或建议，请在项目仓库中提交Issue。