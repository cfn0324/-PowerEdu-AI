# 🔌 电力知识库与AI预测平台

集成电力知识库在线学习与AI负荷预测功能的综合性平台。

## 📋 项目概述

本项目整合了两个核心功能：
- **电力知识库与在线学习平台**：基于Django + React的教育平台
- **电力负荷AI预测系统**：基于机器学习的负荷预测功能

## 🏗️ 项目结构

```
电力知识库与AI预测平台/
├── README.md                    # 项目说明文档
├── requirements.txt             # Python依赖文件
├── backend/                     # Django后端
│   ├── manage.py               # Django管理脚本
│   ├── requirements.txt        # 后端依赖
│   ├── db.sqlite3             # SQLite数据库
│   ├── edu/                   # Django项目配置
│   ├── apps/                  # 应用模块
│   │   ├── course/           # 课程管理
│   │   ├── user/             # 用户管理
│   │   └── prediction/       # AI预测模块（新增）
│   ├── static/               # 静态文件
│   └── ai_prediction/        # AI预测核心代码
│       ├── data_generator.py
│       ├── data_preprocessor.py
│       ├── model_manager.py
│       ├── predictor.py
│       └── visualizer.py
├── frontend/                   # React前端
│   ├── package.json           # 前端依赖
│   ├── vite.config.js         # Vite配置
│   ├── index.html
│   ├── src/                   # 源代码
│   │   ├── main.jsx
│   │   ├── components/        # 组件
│   │   ├── pages/            # 页面
│   │   │   └── prediction/   # AI预测页面（新增）
│   │   ├── router/           # 路由
│   │   └── service/          # API服务
│   └── public/               # 公共资源
├── standalone_ai/             # 独立AI预测系统（保留原功能）
│   ├── app.py                # Gradio应用
│   └── requirements.txt      # 独立系统依赖
└── docs/                     # 文档目录
    ├── 项目立项/
    ├── 需求分析/
    ├── 原型设计/
    ├── 系统设计/
    ├── 系统测试/
    └── 项目答辩/
```

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Node.js 18.15+
- pip
- npm

### 1. 安装Python依赖
```bash
pip install -r requirements.txt
```

### 2. 启动Django后端
```bash
cd backend
python manage.py migrate          # 初始化数据库
python manage.py createsuperuser  # 创建管理员账户
python manage.py runserver        # 启动后端服务
```

### 3. 启动React前端
```bash
cd frontend
npm install      # 安装依赖
npm run dev      # 启动前端开发服务器
```

### 4. 启动独立AI预测系统（可选）
```bash
cd standalone_ai
python app.py    # 启动Gradio界面
```

## 🌐 访问地址

- **主平台**: http://localhost:5173 (React前端)
- **后端API**: http://localhost:8000 (Django后端)
- **管理后台**: http://localhost:8000/admin
- **独立AI系统**: http://localhost:7860 (Gradio界面)

## 🎯 主要功能

### 教育平台功能
- 用户注册与登录
- 课程管理与学习
- 知识库检索
- 在线考试与测评

### AI预测功能
- 电力负荷单点预测
- 批量时间段预测
- 多模型性能对比
- 可视化图表展示
- 模型训练与管理

## 🔧 技术栈

**后端**
- Django 4.x
- Python 3.8+
- SQLite/MySQL
- scikit-learn
- pandas, numpy
- matplotlib, seaborn

**前端**
- React 18
- Antd 5.x
- Vite
- Axios
- React Router

**AI预测**
- Gradio
- 机器学习模型：Linear Regression, Random Forest, Gradient Boosting, XGBoost, SVR

## 👥 开发团队

第2组 - 电力知识库与在线学习平台开发团队

## 📄 许可证

本项目仅供学习和研究使用。
