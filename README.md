# 🔌 PowerEdu-AI 电力知识库与AI预测平台

> **PowerEdu-AI** - 集成电力知识库在线学习与AI负荷预测功能的企业级智能平台

[![Python](https://img.shields.io/badge/Python-3.8+-3776ab.svg?logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-4.2.7-092e20.svg?logo=django&logoColor=white)](https://djangoproject.com)
[![React](https://img.shields.io/badge/React-18.2.0-61dafb.svg?logo=react&logoColor=black)](https://reactjs.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

## 📋 项目概述

PowerEdu-AI是一个面向电力行业的综合性智能教育平台，集成了知识库管理、在线学习和AI负荷预测等核心功能。

### 🎯 核心功能

- **📚 教育平台**: 用户管理、课程系统、互动学习
- **🤖 AI预测引擎**: 多模型负荷预测、实时分析  
- **📊 数据可视化**: 交互式图表、性能监控

## 🚀 快速启动

### 系统要求
- **Python**: 3.8+
- **Node.js**: 18.15+
- **内存**: 4GB+
- **存储**: 2GB+

### 一键启动

**Windows**:
```powershell
.\start.ps1
```

**Linux/Mac**:
```bash
chmod +x start.sh && ./start.sh
```

### 手动启动

1. **安装依赖**
```bash
# Python依赖
pip install -r requirements.txt

# 前端依赖
cd frontend && npm install
```

2. **启动后端**
```bash
cd backend
python manage.py migrate
python manage.py runserver
```

3. **启动前端**
```bash
cd frontend
npm run dev
```

4. **AI系统初始化**

访问 `http://localhost:5173/prediction` 并点击"初始化AI系统"按钮完成机器学习模型的训练和配置。

## 🌐 访问地址

- **前端界面**: http://localhost:5173
- **AI预测**: http://localhost:5173/prediction  
- **后端API**: http://localhost:8000/api
- **管理后台**: http://localhost:8000/admin

## 🤖 AI预测系统

### 预测功能
- **单点预测**: 实时预测特定时间点负荷
- **批量预测**: 批处理多时间点预测  
- **日前预测**: 96点15分钟间隔预测

### 机器学习算法
- **线性回归**: 基线模型，快速训练
- **随机森林**: 集成学习，特征重要性分析
- **梯度提升**: 高精度预测
- **XGBoost**: 工业级梯度提升
- **支持向量回归**: 非线性映射

### 特征工程
- **时间特征**: 小时、日、周、月、季节
- **气象特征**: 温度、湿度、风速、降雨量
- **历史特征**: 滞后项、滑动窗口统计

## 🏗️ 项目结构

```
PowerEdu-AI/
├── backend/                     # Django后端服务
│   ├── manage.py               # 项目管理脚本
│   ├── edu/                    # 核心配置模块
│   ├── apps/                   # 业务应用模块
│   │   ├── user/              # 用户管理
│   │   ├── course/            # 课程管理
│   │   └── prediction/        # AI预测服务
│   └── ai_prediction/         # AI引擎核心
│       ├── data_generator.py  # 数据生成器
│       ├── data_preprocessor.py # 数据预处理
│       ├── model_manager.py   # 模型管理器
│       ├── predictor.py       # 预测引擎
│       └── visualizer.py      # 可视化模块
├── frontend/                   # React前端应用
│   ├── package.json           # 依赖配置
│   ├── vite.config.js         # 构建配置
│   └── src/                   # 源代码目录
│       ├── components/        # 通用组件
│       ├── pages/            # 页面组件
│       ├── router/           # 路由管理
│       ├── service/          # API服务
│       └── stores/           # 状态管理
├── requirements.txt           # Python依赖
├── LICENSE                    # 开源协议
└── start.ps1 / start.sh      # 启动脚本
```

## 🔧 技术栈

### 后端技术
- **Django 4.2.7** - Web框架
- **Python 3.8+** - 编程语言  
- **SQLite** - 数据库
- **scikit-learn** - 机器学习
- **XGBoost** - 梯度提升
- **pandas** - 数据处理
- **plotly** - 数据可视化

### 前端技术
- **React 18.2.0** - UI框架
- **Ant Design 5.x** - 组件库
- **Vite 3.2.3** - 构建工具
- **React Router** - 路由管理
- **Axios** - HTTP客户端

## 📄 开源协议

本项目采用 [MIT License](./LICENSE) 开源协议。

---

**🚀 立即开始：执行 `.\start.ps1` (Windows) 或 `./start.sh` (Linux/Mac) 启动平台！**
