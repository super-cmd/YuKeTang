# 雨课堂数据获取与解析工具

## 项目简介

这是一个用于获取雨课堂平台课程数据并解析任务点的Python工具。该工具能够获取用户信息、课程列表、学习日志，并对任务点进行分类和统计。

## 功能特点

- ✅ 获取用户信息（用户名、用户ID等）
- ✅ 获取课程列表及教师信息
- ✅ 获取指定课程的学习日志
- ✅ 解析任务点并按类型分类（课件、公告、课堂等）
- ✅ 任务数据可视化和统计
- ✅ 支持保存任务数据到JSON文件
- ✅ 完整的日志记录系统
- ✅ 命令行参数支持，便于集成和自动化

## 项目结构

```
YuKeTang/
├── main.py              # 主程序入口
├── README.md            # 项目文档
├── requirements.txt     # 项目依赖
├── .gitignore           # Git忽略文件
├── api/                 # API模块
│   ├── __init__.py
│   ├── courses.py       # 课程相关API
│   └── userinfo.py      # 用户信息API
├── parser/              # 解析器模块
│   ├── __init__.py
│   └── task_parser.py   # 任务点解析器
└── utils/               # 工具模块
    ├── __init__.py
    ├── helpers.py       # 辅助函数
    ├── headers.py       # HTTP请求头处理
    ├── logger.py        # 日志系统
    └── time.py          # 时间处理工具
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

```bash
# 运行主程序，使用默认配置
python main.py

# 指定课程索引（从0开始）
python main.py -c 5

# 保存任务数据到文件
python main.py -s

# 指定输出文件路径
python main.py -s -o my_tasks.json
```

### 高级选项

```bash
# 设置日志级别为DEBUG
python main.py --log-level DEBUG

# 将日志保存到文件
python main.py --log-file app.log

# 综合使用多个选项
python main.py -c 3 -s -o output/tasks.json --log-level INFO --log-file logs/app.log
```

## 命令行参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--course` | `-c` | 指定要查询的课程索引 | `7` |
| `--save` | `-s` | 保存任务数据到文件 | `False` |
| `--output` | `-o` | 任务数据输出文件路径 | `tasks.json` |
| `--log-level` | - | 日志级别（DEBUG/INFO/WARNING/ERROR/CRITICAL） | `INFO` |
| `--log-file` | - | 日志文件路径 | `None` |

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

## 注意事项

1. 使用前请确保已在系统中配置好Cookie信息（保存在cookie.json文件中）
2. 默认情况下，程序将选择第8个课程（索引7）进行演示
3. 如需选择其他课程，请使用`-c`参数指定课程索引
4. 日志文件将自动创建在指定目录（如果不存在）
5. 建议定期更新Cookie以确保API访问正常

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