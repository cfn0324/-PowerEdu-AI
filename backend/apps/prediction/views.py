#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
预测应用视图 - AI 电力负荷预测 API
"""

from ninja import Router
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json
import sys
import os
import traceback
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# 导入认证模块
from apps.core import auth

# 添加AI预测模块路径
current_dir = os.path.dirname(os.path.abspath(__file__))
ai_prediction_path = os.path.join(current_dir, '../../ai_prediction')
sys.path.insert(0, ai_prediction_path)

def serialize_for_json(obj):
    """
    递归地将对象转换为JSON可序列化的格式
    """
    if isinstance(obj, dict):
        return {key: serialize_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    elif isinstance(obj, (pd.Timestamp, pd.Timedelta)):
        return obj.isoformat()
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif hasattr(obj, 'isoformat'):  # 其他日期时间对象
        return obj.isoformat()
    elif hasattr(obj, 'item'):  # numpy标量
        return obj.item()
    else:
        return obj

def get_authenticated_user(request):
    """从JWT token获取认证用户"""
    auth_header = request.headers.get('Authorization', '')
    print(f"🔐 认证头: {auth_header[:50]}..." if auth_header else "🔐 无认证头")
    
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        print(f"🔐 提取到token: {token[:30]}...")
        
        try:
            from apps.core import token_util
            from apps.user.models import User
            
            print(f"🔐 开始解析token...")
            user_id = token_util.parse(token)
            print(f"🔐 token解析成功，用户ID: {user_id}")
            
            user = User.objects.get(id=user_id)
            print(f"🔐 用户查询成功: {user.username} (ID: {user.id})")
            return user
        except User.DoesNotExist:
            print(f"🔐 用户不存在，ID: {user_id}")
            return None
        except Exception as e:
            print(f"� JWT认证失败: {str(e)}")
            return None
    else:
        print("🔐 无有效的Bearer token")
        return None

# 全局变量存储初始化的组件
_data_generator = None
_data_preprocessor = None
_model_manager = None
_predictor = None
_visualizer = None
_system_initialized = False

def check_system_ready():
    """检查系统是否准备就绪，并在必要时更新状态"""
    global _system_initialized, _model_manager
    
    # 如果模型管理器存在，有模型，且已训练，则认为系统就绪
    if _model_manager and hasattr(_model_manager, 'models') and _model_manager.models:
        if _model_manager.is_trained and not _system_initialized:
            _system_initialized = True
            print("🔄 检测到模型已训练，更新系统状态为已初始化")
        return _model_manager.is_trained
    
    return _system_initialized

def initialize_ai_system():
    """初始化AI预测系统"""
    global _data_generator, _data_preprocessor, _model_manager, _predictor, _visualizer, _system_initialized
    
    if _system_initialized:
        print("✅ AI系统已初始化")
        return True
    
    try:
        print("🚀 开始初始化AI预测系统...")
        
        # 确保AI预测模块路径正确添加
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        ai_prediction_path = os.path.join(current_dir, '../../ai_prediction')
        ai_prediction_path = os.path.abspath(ai_prediction_path)
        
        if ai_prediction_path not in sys.path:
            sys.path.insert(0, ai_prediction_path)
        
        # 导入AI模块
        from ai_prediction.data_generator import DataGenerator
        from ai_prediction.data_preprocessor import DataPreprocessor
        from ai_prediction.model_manager import ModelManager
        from ai_prediction.predictor import LoadPredictor
        from ai_prediction.visualizer import Visualizer
        
        # 1. 初始化数据生成器
        print("📊 初始化数据生成器...")
        _data_generator = DataGenerator()
        
        # 2. 生成训练数据 (使用较少的数据量以加快速度)
        print("📊 生成训练数据...")
        train_data = _data_generator.generate_training_data(days=14)  # 2周数据
        print(f"✅ 生成数据完成，数据量: {len(train_data)}")
        
        # 3. 初始化数据预处理器
        print("🔧 初始化数据预处理器...")
        _data_preprocessor = DataPreprocessor()
        X_train, X_test, y_train, y_test = _data_preprocessor.fit_transform(train_data)
        print(f"✅ 数据预处理完成，训练集: {X_train.shape}, 测试集: {X_test.shape}")
        
        # 4. 初始化模型管理器并训练
        print("🤖 初始化模型管理器...")
        _model_manager = ModelManager()
        
        print("📚 开始训练核心模型...")
        training_success = _model_manager.train_core_models(X_train, y_train, X_test, y_test)
        
        if not training_success:
            print("❌ 模型训练失败")
            return False
        
        print(f"✅ 模型训练完成，最佳模型: {_model_manager.best_model_name}")
        
        # 5. 初始化预测器
        print("🔮 初始化预测器...")
        _predictor = LoadPredictor(_model_manager, _data_preprocessor)
        
        # 6. 初始化可视化工具
        print("📊 初始化可视化工具...")
        _visualizer = Visualizer()
        
        _system_initialized = True
        print("🎉 AI预测系统初始化完成！")
        print(f"   最佳模型: {_model_manager.best_model_name}")
        print(f"   可用模型: {list(_model_manager.models.keys())}")
        return True
        
    except Exception as e:
        import traceback
        error_msg = f"❌ AI预测系统初始化失败: {str(e)}"
        print(error_msg)
        print(f"详细错误信息: {traceback.format_exc()}")
        
        # 重置初始化状态
        _system_initialized = False
        return False
        
    except Exception as e:
        import traceback
        error_msg = f"❌ AI预测系统初始化失败: {str(e)}"
        print(error_msg)
        print(f"详细错误信息: {traceback.format_exc()}")
        
        # 重置初始化状态
        _system_initialized = False
        return False

from .models import PredictionHistory, PredictionModel, ModelPerformance

router = Router()

@router.get("/")
def prediction_root(request):
    """AI预测系统根端点"""
    return {
        "success": True,
        "message": "欢迎使用AI电力负荷预测系统",
        "version": "1.0.0",
        "endpoints": {
            "system": {
                "status": "/api/prediction/system/status",
                "initialize": "/api/prediction/system/initialize"
            },
            "models": {
                "list": "/api/prediction/models",
                "performance": "/api/prediction/models/performance"
            },
            "prediction": {
                "single": "/api/prediction/predict/single",
                "batch": "/api/prediction/predict/batch",
                "day_ahead": "/api/prediction/predict/day-ahead",
                "uncertainty": "/api/prediction/predict/uncertainty"
            },
            "analysis": {
                "factors": "/api/prediction/analysis/factors",
                "error": "/api/prediction/analysis/error"
            },
            "data": {
                "history": "/api/prediction/history",
                "dashboard": "/api/prediction/dashboard",
                "generate": "/api/prediction/data/generate"
            }
        },
        "timestamp": datetime.now().isoformat()
    }

@router.get("/system/initialize")
def initialize_system(request):
    """初始化AI预测系统"""
    try:
        print("🔌 收到AI系统初始化请求...")
        success = initialize_ai_system()
        if success:
            return {
                "success": True,
                "message": "AI预测系统初始化成功",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "best_model": _model_manager.best_model_name if _model_manager else None,
                    "available_models": list(_model_manager.models.keys()) if _model_manager else [],
                    "training_status": _model_manager.is_trained if _model_manager else False
                }
            }
        else:
            return {
                "success": False,
                "message": "AI预测系统初始化失败，请检查服务器日志获取详细信息",
                "timestamp": datetime.now().isoformat(),
                "error": "模型训练或初始化过程中出现错误"
            }
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ 初始化API异常: {str(e)}")
        print(f"详细错误: {error_trace}")
        return {
            "success": False,
            "message": "AI预测系统初始化异常",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/system/status")
def get_system_status(request):
    """获取系统状态"""
    global _model_manager
    
    # 检查并更新系统状态
    system_ready = check_system_ready()
    
    status = {
        "initialized": system_ready,
        "timestamp": datetime.now().isoformat()
    }
    
    # 如果模型管理器存在，添加模型信息
    if _model_manager and hasattr(_model_manager, 'models'):
        status.update({
            "available_models": list(_model_manager.models.keys()),
            "best_model": _model_manager.best_model_name,
            "models_trained": _model_manager.is_trained
        })
    else:
        status.update({
            "available_models": [],
            "best_model": None,
            "models_trained": False
        })
    
    return {"success": True, "data": status}

@router.get("/debug/info")
def debug_info(request):
    """调试信息端点"""
    global _model_manager, _system_initialized, _data_generator, _data_preprocessor, _predictor, _visualizer
    
    debug_data = {
        "system_initialized": _system_initialized,
        "model_manager_exists": _model_manager is not None,
        "data_generator_exists": _data_generator is not None,
        "data_preprocessor_exists": _data_preprocessor is not None,
        "predictor_exists": _predictor is not None,
        "visualizer_exists": _visualizer is not None,
    }
    
    if _model_manager:
        debug_data.update({
            "models_count": len(_model_manager.models) if hasattr(_model_manager, 'models') else 0,
            "models_list": list(_model_manager.models.keys()) if hasattr(_model_manager, 'models') else [],
            "is_trained": _model_manager.is_trained if hasattr(_model_manager, 'is_trained') else False,
            "best_model": _model_manager.best_model_name if hasattr(_model_manager, 'best_model_name') else None,
            "performance_data": len(_model_manager.performance) if hasattr(_model_manager, 'performance') else 0
        })
    
    return {"success": True, "data": debug_data}

@router.get("/models")
def get_models(request):
    """获取可用模型列表"""
    global _model_manager
    
    # 强制性检查：只要模型管理器存在且有模型，就返回模型列表
    # 不再依赖初始化状态检查
    if _model_manager and hasattr(_model_manager, 'models'):
        if _model_manager.models:  # 如果有模型
            try:
                models_info = []
                for name, model in _model_manager.models.items():
                    performance = _model_manager.performance.get(name, {})
                    models_info.append({
                        "name": name,
                        "type": type(model).__name__,
                        "is_best": name == _model_manager.best_model_name,
                        "performance": performance
                    })
                
                return {"success": True, "data": models_info}
            except Exception as e:
                return {"success": False, "error": f"构建模型信息时出错: {str(e)}"}
        else:
            # 有模型管理器但没有训练的模型
            return {"success": False, "error": "模型未训练，请先调用系统初始化"}
    
    # 模型管理器不存在
    return {"success": False, "error": "系统未初始化，请先调用 /system/initialize"}

@router.get("/models/performance")
def get_model_performance(request):
    """获取模型性能对比"""
    if not check_system_ready():
        return {"success": False, "error": "系统未初始化"}
    
    try:
        # 获取模型对比数据
        comparison = _model_manager.get_model_comparison()
        
        # 生成可视化图表
        visualization = _visualizer.plot_model_comparison(_model_manager.performance)
        
        return {
            "success": True,
            "data": {
                "comparison": comparison,
                "visualization": visualization,
                "best_model": _model_manager.best_model_name,
                "summary": {
                    "total_models": len(comparison),
                    "trained_models": len([m for m in comparison if m['r2'] > 0]),
                    "best_r2": max([m['r2'] for m in comparison]) if comparison else 0
                }
            }
        }
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ 获取模型性能对比时出错: {str(e)}")
        print(f"详细错误: {error_trace}")
        return {
            "success": False, 
            "error": f"获取模型性能对比失败: {str(e)}",
            "debug_info": {
                "model_manager_exists": _model_manager is not None,
                "visualizer_exists": _visualizer is not None,
                "has_performance": bool(_model_manager.performance) if _model_manager else False
            }
        }

@router.post("/predict/single")
def predict_single(request):
    """单点预测"""
    if not check_system_ready():
        return {"success": False, "error": "系统未初始化"}
    
    try:
        data = json.loads(request.body)
        
        # 参数验证
        required_fields = ['timestamp', 'temperature', 'humidity']
        for field in required_fields:
            if field not in data:
                return {"success": False, "error": f"缺少必需参数: {field}"}
        
        # 执行预测
        result = _predictor.predict_single_point(
            timestamp=data['timestamp'],
            temperature=data['temperature'],
            humidity=data['humidity'],
            wind_speed=data.get('wind_speed', 5.0),
            rainfall=data.get('rainfall', 0.0),
            model_name=data.get('model_name')
        )
        
        # 生成可视化
        visualization = _visualizer.plot_single_prediction(result)
        
        # 保存预测历史 - 使用JWT认证
        user = get_authenticated_user(request)
        if user:
            try:
                print(f"💾 保存单点预测历史记录，用户: {user.username}")
                
                # 序列化输入数据和预测结果
                serialized_input = serialize_for_json(data)
                serialized_result = serialize_for_json(result)
                
                model_obj, created = PredictionModel.objects.get_or_create(
                    name=result['model_used'],
                    defaults={'model_type': 'ml', 'description': '机器学习模型'}
                )
                
                history_record = PredictionHistory.objects.create(
                    user=user,
                    model=model_obj,
                    input_data=serialized_input,
                    prediction_result=serialized_result,
                    prediction_type='single'
                )
                print(f"💾 单点预测历史记录保存成功，ID: {history_record.id}")
            except Exception as e:
                print(f"❌ 保存单点预测历史记录失败: {str(e)}")
        else:
            print("💾 用户未认证，跳过单点预测历史记录保存")
        
        return {
            "success": True,
            "data": {
                "prediction": result,
                "visualization": visualization
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/predict/batch")
def predict_batch(request):
    """批量预测"""
    if not _system_initialized:
        return {"success": False, "error": "系统未初始化"}
    
    try:
        data = json.loads(request.body)
        
        if 'data_points' not in data:
            return {"success": False, "error": "缺少参数: data_points"}
        
        # 执行批量预测
        results = _predictor.predict_batch(
            prediction_data=data['data_points'],
            model_name=data.get('model_name')
        )
        
        # 生成可视化
        visualization = _visualizer.plot_batch_predictions(results)
        
        # 保存预测历史 - 使用JWT认证
        user = get_authenticated_user(request)
        if user:
            try:
                print(f"💾 保存批量预测历史记录，用户: {user.username}")
                
                # 序列化输入数据和预测结果
                serialized_input = serialize_for_json(data)
                serialized_results = serialize_for_json({"results": results})
                
                model_obj, created = PredictionModel.objects.get_or_create(
                    name=results[0]['model_used'],
                    defaults={'model_type': 'ml', 'description': '机器学习模型'}
                )
                
                history_record = PredictionHistory.objects.create(
                    user=user,
                    model=model_obj,
                    input_data=serialized_input,
                    prediction_result=serialized_results,
                    prediction_type='batch'
                )
                print(f"💾 批量预测历史记录保存成功，ID: {history_record.id}")
            except Exception as e:
                print(f"❌ 保存批量预测历史记录失败: {str(e)}")
        else:
            print("💾 用户未认证，跳过批量预测历史记录保存")
        
        return {
            "success": True,
            "data": {
                "predictions": results,
                "visualization": visualization,
                "summary": {
                    "total_points": len(results),
                    "model_used": results[0]['model_used'] if results else None
                }
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/predict/day-ahead")
def predict_day_ahead(request):
    """日前预测（96个时间点）"""
    if not _system_initialized:
        return {"success": False, "error": "系统未初始化"}
    
    try:
        data = json.loads(request.body)
        
        if 'target_date' not in data:
            return {"success": False, "error": "缺少参数: target_date"}
        
        target_date_str = data['target_date']
        
        # 验证日期格式和有效性
        try:
            from datetime import datetime
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            
            # 检查日期是否为未来日期
            if target_date <= datetime.now().date():
                return {"success": False, "error": "只能预测未来的日期"}
                
        except ValueError as e:
            return {"success": False, "error": f"日期格式错误，请使用YYYY-MM-DD格式: {str(e)}"}
        
        print(f"🗓️  开始日前预测，目标日期: {target_date_str}")
        
        # 执行日前预测
        result = _predictor.predict_day_ahead(
            target_date=target_date_str,
            weather_forecast=data.get('weather_forecast'),
            model_name=data.get('model_name')
        )
        
        # 生成可视化
        visualization = _visualizer.plot_day_ahead_prediction(result)
        
        # 保存预测历史 - 使用JWT认证
        user = get_authenticated_user(request)
        
        if user:
            try:
                print(f"💾 保存日前预测历史记录，用户: {user.username}")
                
                # 序列化输入数据和预测结果
                serialized_input = serialize_for_json(data)
                serialized_result = serialize_for_json(result)
                
                model_obj, created = PredictionModel.objects.get_or_create(
                    name=result['model_used'],
                    defaults={'model_type': 'ml', 'description': '机器学习模型'}
                )
                if created:
                    print(f"💾 创建新模型记录: {model_obj.name}")
                
                history_record = PredictionHistory.objects.create(
                    user=user,
                    model=model_obj,
                    input_data=serialized_input,
                    prediction_result=serialized_result,
                    prediction_type='day_ahead'
                )
                print(f"💾 历史记录保存成功，ID: {history_record.id}")
            except Exception as e:
                print(f"❌ 保存历史记录失败: {str(e)}")
                # 不影响预测结果的返回
        else:
            print("💾 用户未认证，跳过历史记录保存")
        
        return {
            "success": True,
            "data": {
                "prediction": result,
                "visualization": visualization
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/predict/uncertainty")
def predict_with_uncertainty(request):
    """不确定性分析预测"""
    if not _system_initialized:
        return {"success": False, "error": "系统未初始化"}
    
    try:
        data = json.loads(request.body)
        
        # 执行不确定性预测
        result = _predictor.predict_with_uncertainty(
            input_data=data,
            n_samples=data.get('n_samples', 100)
        )
        
        return {"success": True, "data": result}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/analysis/factors")
def analyze_prediction_factors(request):
    """预测因素分析"""
    if not _system_initialized:
        return {"success": False, "error": "系统未初始化"}
    
    try:
        data = json.loads(request.body)
        
        # 分析预测因素
        analysis = _predictor.analyze_prediction_factors(
            prediction_result=data['prediction_result'],
            actual_load=data.get('actual_load')
        )
        
        return {"success": True, "data": analysis}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/analysis/error")
def analyze_prediction_error(request):
    """预测误差分析"""
    if not _system_initialized:
        return {"success": False, "error": "系统未初始化"}
    
    try:
        data = json.loads(request.body)
        
        if 'predictions' not in data or 'actual_values' not in data:
            return {"success": False, "error": "缺少参数: predictions 或 actual_values"}
        
        # 生成误差分析
        analysis = _visualizer.plot_prediction_error_analysis(
            predictions=data['predictions'],
            actual_values=data['actual_values']
        )
        
        return {"success": True, "data": analysis}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/history")
def get_prediction_history(request):
    """获取用户预测历史"""
    try:
        print(f"🔍 收到历史记录请求")
        
        # 使用JWT认证获取用户
        user = get_authenticated_user(request)
        
        if user:
            print(f"🔍 JWT认证成功，用户: {user.username} (ID: {user.id})")
            histories = PredictionHistory.objects.filter(user=user).order_by('-created_at')[:50]
            print(f"🔍 查询到 {len(histories)} 条历史记录")
        else:
            # 未登录用户返回空历史记录
            print("🔍 用户未认证，返回空历史记录")
            return {"success": True, "data": []}
        
        history_data = []
        for history in histories:
            print(f"🔍 处理历史记录 ID: {history.id}, 类型: {history.prediction_type}")
            
            # 根据预测类型处理不同的数据结构
            input_summary = {
                'timestamp': history.input_data.get('timestamp', 'N/A'),
                'temperature': history.input_data.get('temperature', 'N/A')
            }
            
            prediction_summary = {}
            
            if history.prediction_type == 'single':
                prediction_summary = {
                    'predicted_load': history.prediction_result.get('predicted_load', 'N/A')
                }
            elif history.prediction_type == 'batch':
                results = history.prediction_result.get('results', [])
                if results:
                    prediction_summary = {
                        'predicted_load': f"批量结果 ({len(results)} 个点)"
                    }
                else:
                    prediction_summary = {
                        'predicted_load': '批量结果'
                    }
            elif history.prediction_type == 'day_ahead':
                # 日前预测显示日期和总点数
                target_date = history.input_data.get('target_date', 'N/A')
                predictions = history.prediction_result.get('predictions', [])
                prediction_summary = {
                    'predicted_load': f"日前预测 ({len(predictions)} 个点)" if predictions else "日前预测"
                }
                input_summary['target_date'] = target_date
            
            history_data.append({
                'id': history.id,
                'model_name': history.model.name,
                'prediction_type': history.prediction_type,
                'created_at': history.created_at.isoformat(),
                'input_summary': input_summary,
                'prediction_summary': prediction_summary
            })
        
        print(f"🔍 返回 {len(history_data)} 条处理后的历史记录")
        return {"success": True, "data": history_data}
        
    except Exception as e:
        import traceback
        print(f"❌ 获取预测历史失败: {str(e)}")
        print(f"详细错误: {traceback.format_exc()}")
        return {"success": False, "error": str(e)}

@router.get("/dashboard")
def get_dashboard_data(request):
    """获取仪表板数据"""
    if not _system_initialized:
        return {"success": False, "error": "系统未初始化"}
    
    try:
        # 获取模型性能摘要
        performance_summary = _predictor.get_model_performance_summary()
        
        # 生成示例预测（最近24小时）
        tomorrow = datetime.now().date() + timedelta(days=1)
        sample_prediction = _predictor.predict_day_ahead(tomorrow)
        
        # 创建仪表板
        dashboard = _visualizer.create_dashboard_summary(
            prediction_results=sample_prediction,
            model_performance=_model_manager.performance
        )
        
        dashboard['system_info'] = {
            'initialized': _system_initialized,
            'total_models': len(_model_manager.models),
            'best_model': _model_manager.best_model_name,
            'last_updated': datetime.now().isoformat()
        }
        
        if request.user.is_authenticated:
            dashboard['user_stats'] = {
                'total_predictions': PredictionHistory.objects.filter(user=request.user).count(),
                'recent_predictions': PredictionHistory.objects.filter(
                    user=request.user,
                    created_at__gte=datetime.now() - timedelta(days=7)
                ).count()
            }
        
        return {"success": True, "data": dashboard}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/data/generate")
def generate_sample_data(request):
    """生成示例数据"""
    if not _system_initialized:
        return {"success": False, "error": "系统未初始化"}
    
    try:
        data = json.loads(request.body)
        days = data.get('days', 7)
        
        # 生成示例数据
        sample_data = _data_generator.generate_training_data(days=days)
        
        # 转换为JSON格式
        sample_data_json = sample_data.to_dict('records')
        
        return {
            "success": True,
            "data": {
                "sample_data": sample_data_json[:100],  # 限制返回前100条
                "total_records": len(sample_data_json),
                "columns": list(sample_data.columns)
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}
