# 📁 PowerEdu-AI 项目结构

## 根目录
```
PowerEdu-AI/
├── backend/          # Django后端服务
├── frontend/         # React前端应用
├── .env.example      # 环境变量模板
├── .gitignore        # Git忽略文件
├── LICENSE           # 开源协议
├── README.md         # 项目说明文档
├── requirements.txt  # Python依赖
├── start.ps1         # Windows启动脚本
└── start.sh          # Linux/Mac启动脚本
```

## 后端结构 (backend/)
```
backend/
├── manage.py             # Django管理脚本
├── admin_manager.py      # 管理员管理工具
├── db.sqlite3           # SQLite数据库
├── media/               # 媒体文件存储
├── edu/                 # Django项目配置
│   ├── __init__.py
│   ├── settings.py      # 项目设置
│   ├── urls.py          # URL配置
│   ├── wsgi.py          # WSGI配置
│   └── asgi.py          # ASGI配置
├── apps/                # 业务应用
│   ├── core.py          # 核心功能
│   ├── urls.py          # 应用URL配置
│   ├── user/            # 用户管理
│   ├── course/          # 课程管理
│   ├── prediction/      # AI预测
│   └── knowledge/       # 知识库系统
└── ai_prediction/       # AI预测引擎
    ├── data_generator.py    # 数据生成器
    ├── data_preprocessor.py # 数据预处理
    ├── model_manager.py     # 模型管理
    ├── predictor.py         # 预测引擎
    └── visualizer.py        # 可视化
```

## 前端结构 (frontend/)
```
frontend/
├── public/              # 静态资源
├── src/                 # 源代码
│   ├── assets/          # 静态资源
│   ├── components/      # 组件
│   │   ├── common/      # 通用组件
│   │   ├── course/      # 课程组件
│   │   ├── login/       # 登录组件
│   │   └── message/     # 消息组件
│   ├── hooks/           # 自定义Hooks
│   ├── pages/           # 页面组件
│   │   ├── home/        # 首页
│   │   ├── courses/     # 课程页面
│   │   ├── prediction/  # 预测页面
│   │   ├── knowledge/   # 知识库页面
│   │   ├── profile/     # 个人中心
│   │   └── layout/      # 布局组件
│   ├── router/          # 路由配置
│   ├── service/         # API服务
│   ├── stores/          # 状态管理
│   ├── index.css        # 全局样式
│   ├── main.jsx         # 入口文件
│   └── tools.js         # 工具函数
├── package.json         # 项目依赖
├── package-lock.json    # 依赖锁定
├── vite.config.js       # Vite配置
└── index.html           # HTML模板
```

## 核心功能模块

### 1. 用户管理 (apps/user/)
- 用户注册、登录、认证
- 用户资料管理
- 权限控制

### 2. 课程管理 (apps/course/)
- 课程创建、编辑、删除
- 章节管理
- 视频播放
- 评论系统

### 3. AI预测 (apps/prediction/)
- 负荷预测算法
- 多种机器学习模型
- 预测结果可视化
- 历史记录管理

### 4. 知识库系统 (apps/knowledge/)
- 基于RAG的智能问答
- 文档管理
- 向量化存储
- 多模型配置

### 5. AI预测引擎 (ai_prediction/)
- 数据生成和预处理
- 模型训练和管理
- 预测执行
- 结果可视化

## 数据存储
- SQLite数据库：用户数据、课程信息、预测记录
- 文件系统：上传的文档、媒体文件
- 向量数据库：知识库文档的向量化存储

## 技术栈
- **后端**: Django 4.2.7, Python 3.8+
- **前端**: React 18.2.0, Ant Design, Vite
- **数据库**: SQLite
- **AI/ML**: scikit-learn, XGBoost, pandas
- **大模型**: OpenAI GPT, Google Gemini, 智谱AI等
