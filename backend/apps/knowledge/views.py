#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
知识库应用视图 - 大模型知识库问答系统 API
"""

from ninja import Router, UploadedFile, File
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from apps.user.models import User
from django.core.paginator import Paginator
from typing import List, Dict, Optional
import json
import os
import sys
import traceback
import asyncio
import logging

logger = logging.getLogger(__name__)
import uuid
from datetime import datetime

from apps.core import auth, R
from .models import (
    KnowledgeBase, Document, QASession, QARecord, 
    ModelConfig, EmbeddingConfig
)
from .schemas import (
    KnowledgeBaseSchema, DocumentSchema, QASessionSchema, 
    QARecordSchema, ModelConfigSchema, ModelConfigCreateSchema, QARequestSchema,
    DocumentUploadSchema, KnowledgeBaseCreateSchema
)

# 导入RAG系统
from .rag_system_simple import RAGSystem

# 创建路由器
router = Router()

# 全局RAG系统实例
_rag_system = None

def get_rag_system():
    """获取RAG系统实例"""
    global _rag_system
    if _rag_system is None:
        _rag_system = RAGSystem()
    return _rag_system


def get_user_from_request(request):
    """从请求中获取用户，如果用户不存在则抛出异常"""
    try:
        return User.objects.get(id=request.auth)
    except User.DoesNotExist:
        raise ValueError("用户不存在，请重新登录")


@router.get("/", summary="知识库系统概览")
def knowledge_root(request):
    """知识库系统根端点"""
    return {
        "success": True,
        "message": "欢迎使用PowerEdu-AI大模型知识库系统",
        "version": "1.0.0",
        "features": [
            "基于RAG技术的智能问答",
            "支持多种文档格式处理",
            "多模型配置支持",
            "向量化存储与检索",
            "会话式交互体验"
        ],
        "endpoints": {
            "knowledge_bases": "/api/knowledge/knowledge-bases",
            "documents": "/api/knowledge/documents", 
            "qa": "/api/knowledge/qa",
            "models": "/api/knowledge/models",
            "upload": "/api/knowledge/upload"
        },
        "timestamp": datetime.now().isoformat()
    }


# ==================== 知识库管理 ====================

@router.get("/knowledge-bases", summary="获取知识库列表")
def get_knowledge_bases(request, page: int = 1, size: int = 10):
    """获取知识库列表"""
    try:
        knowledge_bases = KnowledgeBase.objects.filter(is_active=True).order_by('-created_at')
        paginator = Paginator(knowledge_bases, size)
        page_obj = paginator.get_page(page)
        
        # 手动序列化知识库对象
        items = []
        for kb in page_obj:
            items.append({
                "id": kb.id,
                "name": kb.name,
                "description": kb.description,
                "is_active": kb.is_active,
                "document_count": kb.documents.count(),
                "created_at": kb.created_at.isoformat() if kb.created_at else None,
                "updated_at": kb.updated_at.isoformat() if kb.updated_at else None,
                "created_by": kb.created_by.username if kb.created_by else None,
            })
        
        return {
            "success": True,
            "data": {
                "items": items,
                "total": paginator.count,
                "page": page,
                "size": size,
                "pages": paginator.num_pages
            }
        }
    except Exception as e:
        logger.error(f"获取知识库列表失败: {e}")
        return {"success": False, "error": str(e)}


@router.post("/knowledge-bases", summary="创建知识库", **auth)
def create_knowledge_base(request, data: KnowledgeBaseCreateSchema):
    """创建新的知识库"""
    try:
        # 获取用户
        user = get_user_from_request(request)
        
        # 创建数据库记录
        kb = KnowledgeBase.objects.create(
            name=data.name,
            description=data.description,
            created_by=user
        )
        
        # 简单返回成功，不需要特殊的RAG系统初始化
        return {"success": True, "data": {"id": kb.id, "name": kb.name}}
            
    except ValueError as e:
        # 用户不存在的错误
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/knowledge-bases/{kb_id}", summary="获取知识库详情")
def get_knowledge_base(request, kb_id: int):
    """获取知识库详情"""
    try:
        kb = KnowledgeBase.objects.get(id=kb_id, is_active=True)
        
        # 获取统计信息
        rag_system = get_rag_system()
        stats = rag_system.get_knowledge_base_stats(kb_id)
        
        return {
            "success": True,
            "data": {
                "knowledge_base": {
                    "id": kb.id,
                    "name": kb.name,
                    "description": kb.description,
                    "is_active": kb.is_active,
                    "created_at": kb.created_at.isoformat() if kb.created_at else None,
                    "updated_at": kb.updated_at.isoformat() if kb.updated_at else None,
                    "created_by": kb.created_by.username if kb.created_by else None,
                },
                "stats": stats,
                "document_count": kb.documents.count(),
                "qa_session_count": kb.qa_sessions.count()
            }
        }
    except KnowledgeBase.DoesNotExist:
        return {"success": False, "error": "知识库不存在"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.delete("/knowledge-bases/{kb_id}", summary="删除知识库", **auth)
def delete_knowledge_base(request, kb_id: int):
    """删除知识库"""
    try:
        kb = KnowledgeBase.objects.get(id=kb_id, is_active=True)
        user = get_user_from_request(request)
        
        # 检查权限（只有创建者可以删除）
        if kb.created_by != user:
            return {"success": False, "error": "没有权限删除此知识库"}
        
        # 软删除（设置为不活跃）
        kb.is_active = False
        kb.save()
        
        return {"success": True, "message": "知识库已删除"}
        
    except KnowledgeBase.DoesNotExist:
        return {"success": False, "error": "知识库不存在"}
    except ValueError as e:
        # 用户不存在的错误
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== 文档管理 ====================

@router.get("/documents", summary="获取文档列表")
def get_documents(request, kb_id: int, page: int = 1, size: int = 10):
    """获取文档列表"""
    try:
        documents = Document.objects.filter(
            knowledge_base_id=kb_id
        ).order_by('-uploaded_at')
        
        paginator = Paginator(documents, size)
        page_obj = paginator.get_page(page)
        
        # 手动序列化文档对象
        items = []
        for doc in page_obj:
            items.append({
                "id": doc.id,
                "title": doc.title,
                "file_name": doc.file_name,
                "file_type": doc.file_type,
                "file_size": doc.file_size,
                "status": doc.status,
                "chunk_count": doc.chunk_count,
                "processed_at": doc.processed_at.isoformat() if doc.processed_at else None,
                "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
            })
        
        return {
            "success": True,
            "data": {
                "items": items,
                "total": paginator.count,
                "page": page,
                "size": size,
                "pages": paginator.num_pages
            }
        }
    except Exception as e:
        logger.error(f"获取文档列表失败: {e}")
        return {"success": False, "error": str(e)}


@router.get("/documents/{doc_id}", summary="获取文档详情")
def get_document_detail(request, doc_id: int):
    """获取文档详情"""
    try:
        document = Document.objects.get(id=doc_id)
        
        # 序列化文档对象
        doc_data = {
            "id": document.id,
            "title": document.title,
            "file_name": document.file_name,
            "file_path": document.file_path,
            "file_type": document.file_type,
            "file_size": document.file_size,
            "status": document.status,
            "chunk_count": document.chunk_count,
            "metadata": document.metadata,
            "uploaded_by": document.uploaded_by.username if document.uploaded_by else None,
            "uploaded_at": document.uploaded_at.isoformat() if document.uploaded_at else None,
            "processed_at": document.processed_at.isoformat() if document.processed_at else None,
            "knowledge_base": {
                "id": document.knowledge_base.id,
                "name": document.knowledge_base.name,
                "description": document.knowledge_base.description,
            }
        }
        
        return {
            "success": True,
            "data": doc_data
        }
        
    except Document.DoesNotExist:
        return {"success": False, "error": "文档不存在"}
    except Exception as e:
        logger.error(f"获取文档详情失败: {e}")
        return {"success": False, "error": str(e)}

@router.delete("/documents/{doc_id}", summary="删除文档", **auth)
def delete_document(request, doc_id: int):
    """删除文档"""
    try:
        document = Document.objects.get(id=doc_id)
        user = get_user_from_request(request)
        
        # 检查权限（只有上传者或知识库创建者可以删除）
        if document.uploaded_by != user and document.knowledge_base.created_by != user:
            return {"success": False, "error": "没有权限删除此文档"}
        
        # 删除文件
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # 删除数据库记录
        document.delete()
        
        return {"success": True, "message": "文档已删除"}
        
    except Document.DoesNotExist:
        return {"success": False, "error": "文档不存在"}
    except ValueError as e:
        # 用户不存在的错误
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/documents/upload", summary="上传文档", **auth)
def upload_document(request, kb_id: int, file: UploadedFile = File(...)):
    """上传文档到知识库"""
    try:
        # 检查知识库是否存在
        kb = KnowledgeBase.objects.get(id=kb_id, is_active=True)
        user = get_user_from_request(request)
        
        # 检查文件大小 (限制为500MB)
        max_file_size = 500 * 1024 * 1024  # 500MB
        if file.size > max_file_size:
            return {"success": False, "error": f"文件大小超过限制({max_file_size // (1024*1024)}MB)"}
        
        # 检查文件类型
        allowed_extensions = ['.md', '.pdf', '.txt', '.docx', '.html']
        file_extension = os.path.splitext(file.name)[1].lower()
        
        if file_extension not in allowed_extensions:
            return {"success": False, "error": f"不支持的文件类型: {file_extension}"}
        
        # 创建上传目录
        upload_dir = f"media/knowledge_bases/{kb_id}/documents"
        os.makedirs(upload_dir, exist_ok=True)
        
        # 生成唯一文件名避免冲突
        import uuid
        unique_filename = f"{uuid.uuid4().hex[:8]}_{file.name}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # 保存文件 - 优化大文件处理
        logger.info(f"开始保存文件: {file.name}, 大小: {file.size} bytes")
        try:
            with open(file_path, 'wb') as f:
                # 分块写入，减少内存使用
                for chunk in file.chunks(chunk_size=8192):  # 8KB chunks
                    f.write(chunk)
        except Exception as e:
            logger.error(f"文件保存失败: {e}")
            return {"success": False, "error": f"文件保存失败: {str(e)}"}
        
        logger.info(f"文件保存成功: {file_path}")
        
        # 创建文档记录
        document = Document.objects.create(
            knowledge_base=kb,
            title=os.path.splitext(file.name)[0],
            file_path=file_path,
            file_name=file.name,
            file_type=file_extension[1:],  # 去掉点号
            file_size=file.size,
            uploaded_by=user,
            status='pending'
        )
        
        # 异步处理文档
        try:
            rag_system = get_rag_system()
            logger.info(f"开始处理文档: {file.name}, 文件大小: {file.size}")
            result = rag_system.process_document(kb_id, file_path, document.id)
            logger.info(f"文档处理结果: {result}")
            
            if result.get('success', False):
                # 更新文档状态
                document.status = 'completed'
                document.chunk_count = result.get('chunk_count', 0)
                document.processed_at = datetime.now()
                document.save()
                
                return {
                    "success": True,
                    "data": {
                        "document_id": document.id,
                        "chunk_count": result.get('chunk_count', 0),
                        "status": "completed",
                        "file_size": file.size,
                        "file_name": file.name
                    }
                }
            else:
                document.status = 'failed'
                document.save()
                logger.error(f"文档处理失败: {result.get('error', '未知错误')}")
                return {"success": False, "error": f"文档处理失败: {result.get('error', '未知错误')}"}
            
        except Exception as e:
            document.status = 'failed'
            document.save()
            logger.error(f"文档处理异常: {str(e)}", exc_info=True)
            return {"success": False, "error": f"文档处理失败: {str(e)}"}
            
    except KnowledgeBase.DoesNotExist:
        return {"success": False, "error": "知识库不存在"}
    except ValueError as e:
        # 用户不存在的错误
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"上传文档异常: {str(e)}", exc_info=True)
        return {"success": False, "error": f"上传失败: {str(e)}"}


@router.post("/documents/{kb_id}/batch-upload", summary="批量上传文档", **auth)
def batch_upload_documents(request, kb_id: int):
    """批量上传文档到知识库"""
    try:
        # 检查知识库是否存在
        kb = KnowledgeBase.objects.get(id=kb_id, is_active=True)
        user = get_user_from_request(request)
        
        # 从request.FILES中获取所有上传的文件
        files = request.FILES.getlist('files')
        if not files:
            return {"success": False, "error": "没有选择文件"}
        
        results = []
        allowed_extensions = ['.md', '.pdf', '.txt', '.docx', '.html']
        max_file_size = 500 * 1024 * 1024  # 500MB
        
        for file in files:
            try:
                # 检查文件大小
                if file.size > max_file_size:
                    results.append({
                        "file_name": file.name,
                        "success": False,
                        "error": f"文件大小超过限制({max_file_size // (1024*1024)}MB)"
                    })
                    continue
                
                # 检查文件类型
                file_extension = os.path.splitext(file.name)[1].lower()
                
                if file_extension not in allowed_extensions:
                    results.append({
                        "file_name": file.name,
                        "success": False,
                        "error": f"不支持的文件类型: {file_extension}"
                    })
                    continue
                
                # 创建上传目录
                upload_dir = f"media/knowledge_bases/{kb_id}/documents"
                os.makedirs(upload_dir, exist_ok=True)
                
                # 生成唯一文件名避免冲突
                import uuid
                unique_filename = f"{uuid.uuid4().hex[:8]}_{file.name}"
                file_path = os.path.join(upload_dir, unique_filename)
                
                # 保存文件 - 优化大文件处理
                logger.info(f"开始批量保存文件: {file.name}, 大小: {file.size} bytes")
                try:
                    with open(file_path, 'wb') as f:
                        # 分块写入，减少内存使用
                        for chunk in file.chunks(chunk_size=8192):  # 8KB chunks
                            f.write(chunk)
                except Exception as e:
                    logger.error(f"批量文件保存失败: {e}")
                    results.append({
                        "file_name": file.name,
                        "success": False,
                        "error": f"文件保存失败: {str(e)}"
                    })
                    continue
                
                logger.info(f"批量文件保存成功: {file_path}")
                
                # 创建文档记录
                document = Document.objects.create(
                    knowledge_base=kb,
                    title=os.path.splitext(file.name)[0],
                    file_path=file_path,
                    file_name=file.name,
                    file_type=file_extension[1:],  # 去掉点号
                    file_size=file.size,
                    uploaded_by=user,
                    status='pending'
                )
                
                # 处理文档
                rag_system = get_rag_system()
                logger.info(f"开始批量处理文档: {file.name}, 文件大小: {file.size}")
                result = rag_system.process_document(kb_id, file_path, document.id)
                logger.info(f"批量文档处理结果: {result}")
                
                if result.get('success', False):
                    # 更新文档状态
                    document.status = 'completed'
                    document.chunk_count = result.get('chunk_count', 0)
                    document.processed_at = datetime.now()
                    document.save()
                    
                    results.append({
                        "file_name": file.name,
                        "success": True,
                        "document_id": document.id,
                        "chunk_count": result.get('chunk_count', 0),
                        "file_size": file.size
                    })
                else:
                    document.status = 'failed'
                    document.save()
                    logger.error(f"批量文档处理失败: {result.get('error', '未知错误')}")
                    results.append({
                        "file_name": file.name,
                        "success": False,
                        "error": f"文档处理失败: {result.get('error', '未知错误')}"
                    })
                
            except Exception as e:
                logger.error(f"批量文档处理异常 {file.name}: {str(e)}", exc_info=True)
                results.append({
                    "file_name": file.name if hasattr(file, 'name') else 'unknown',
                    "success": False,
                    "error": str(e)
                })
        
        # 统计结果
        success_count = sum(1 for r in results if r['success'])
        total_count = len(results)
        
        return {
            "success": True,
            "data": {
                "results": results,
                "summary": {
                    "total": total_count,
                    "success": success_count,
                    "failed": total_count - success_count
                }
            }
        }
            
    except KnowledgeBase.DoesNotExist:
        return {"success": False, "error": "知识库不存在"}
    except ValueError as e:
        # 用户不存在的错误
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"批量上传文档异常: {str(e)}", exc_info=True)
        return {"success": False, "error": f"批量上传失败: {str(e)}"}


# ==================== 问答功能 ====================

@router.post("/qa/ask", summary="智能问答", **auth)
def ask_question(request, data: QARequestSchema):
    """智能问答接口"""
    try:
        # 检查知识库
        kb = KnowledgeBase.objects.get(id=data.kb_id, is_active=True)
        user = get_user_from_request(request)
        
        # 获取或创建会话
        if data.session_id:
            try:
                session = QASession.objects.get(session_id=data.session_id, user=user)
            except QASession.DoesNotExist:
                session = QASession.objects.create(
                    knowledge_base=kb,
                    user=user,
                    session_id=data.session_id,
                    title=data.question[:50] + "..." if len(data.question) > 50 else data.question
                )
        else:
            # 创建新会话
            session_id = str(uuid.uuid4())
            session = QASession.objects.create(
                knowledge_base=kb,
                user=user,
                session_id=session_id,
                title=data.question[:50] + "..." if len(data.question) > 50 else data.question
            )
        
        # 调用RAG系统进行问答
        rag_system = get_rag_system()
        
        # 配置LLM - 优先使用指定的配置，否则使用默认的Gemini配置
        config_id_to_use = data.model_config_id
        
        if config_id_to_use:
            try:
                model_config = ModelConfig.objects.get(id=config_id_to_use, is_active=True)
                llm_config = {
                    'model_type': model_config.model_type,
                    'model_name': model_config.model_name,
                    'api_key': model_config.api_key,
                    'api_base_url': model_config.api_base_url,
                    'max_tokens': model_config.max_tokens,
                    'temperature': model_config.temperature
                }
                rag_system.configure_llm(config_id_to_use, llm_config)
            except ModelConfig.DoesNotExist:
                config_id_to_use = None
        
        # 如果没有指定配置ID或指定的配置不存在，使用默认的Gemini配置
        if not config_id_to_use:
            try:
                # 查找激活的Gemini配置
                gemini_config = ModelConfig.objects.filter(
                    model_name__icontains='gemini',
                    is_active=True
                ).first()
                
                if gemini_config:
                    config_id_to_use = gemini_config.id
                    llm_config = {
                        'model_type': gemini_config.model_type,
                        'model_name': gemini_config.model_name,
                        'api_key': gemini_config.api_key,
                        'api_base_url': gemini_config.api_base_url,
                        'max_tokens': gemini_config.max_tokens,
                        'temperature': gemini_config.temperature
                    }
                    rag_system.configure_llm(config_id_to_use, llm_config)
                    logger.info(f"使用默认Gemini配置: {gemini_config.model_name}")
                else:
                    logger.warning("未找到激活的Gemini配置")
            except Exception as e:
                logger.warning(f"无法配置默认Gemini配置: {e}")
        
        # 添加调试日志
        logger.info(f"最终使用的配置ID: {config_id_to_use}")
        logger.info(f"RAG系统中的LLM配置: {list(rag_system.llm_configs.keys())}")
        
        # 执行问答
        async def run_qa():
            from asgiref.sync import sync_to_async
            
            @sync_to_async
            def get_doc_count():
                return Document.objects.filter(
                    knowledge_base_id=data.kb_id,
                    status='completed'
                ).count()
            
            try:
                # 获取知识库的文档数量
                doc_count = await get_doc_count()
                
                # 检查RAG系统中是否已有文档
                vector_store = rag_system.get_or_create_vector_store(data.kb_id)
                
                # 如果向量存储为空但数据库中有文档，则手动加载
                if len(vector_store.chunks) == 0 and doc_count > 0:
                    logger.info(f"知识库 {data.kb_id} 的向量存储为空，开始手动加载文档数据")
                    loaded_count = rag_system.manually_load_documents(data.kb_id)
                    logger.info(f"成功加载 {loaded_count} 个文档块")
                else:
                    logger.info(f"知识库 {data.kb_id} 中已有 {len(vector_store.chunks)} 个文档块")
                    
            except Exception as e:
                logger.error(f"加载文档时出错: {e}")
                # 继续执行，即使加载失败也允许问答（可能返回通用回答）
            
            return await rag_system.ask_question(
                kb_id=data.kb_id,
                question=data.question,
                config_id=config_id_to_use,
                top_k=data.top_k or 5,
                threshold=data.threshold or 0.1  # 降低默认阈值，确保能检索到文档
            )
        
        # 在同步环境中运行异步函数
        try:
            # 尝试获取当前事件循环
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环正在运行，使用asyncio.run_coroutine_threadsafe
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, run_qa())
                    result = future.result()
            else:
                # 如果事件循环没有运行，直接运行
                result = loop.run_until_complete(run_qa())
        except RuntimeError:
            # 如果没有事件循环，创建新的
            result = asyncio.run(run_qa())
        
        # 验证返回的结果包含所有必要字段
        required_fields = ['answer', 'sources', 'model_used', 'response_time']
        missing_fields = [field for field in required_fields if field not in result]
        
        if missing_fields:
            logger.error(f"RAG系统返回的结果缺少字段: {missing_fields}")
            logger.error(f"实际返回的结果: {result}")
            return {"success": False, "error": f"系统内部错误: 缺少必要字段 {missing_fields}"}
        
        # 保存问答记录
        qa_record = QARecord.objects.create(
            session=session,
            question=data.question,
            answer=result['answer'],
            retrieved_chunks=result.get('retrieved_chunks', []),
            model_used=result['model_used'],
            response_time=result['response_time'],
            tokens_used=result.get('tokens_used', 0)
        )
        
        return {
            "success": True,
            "data": {
                "session_id": session.session_id,
                "answer": result['answer'],
                "sources": result['sources'],
                "model_used": result['model_used'],
                "response_time": result['response_time'],
                "qa_record_id": qa_record.id
            }
        }
        
    except KnowledgeBase.DoesNotExist:
        return {"success": False, "error": "知识库不存在"}
    except ValueError as e:
        # 用户不存在的错误
        return {"success": False, "error": str(e)}
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"问答异常: {error_trace}")
        return {"success": False, "error": str(e)}


@router.get("/qa/sessions", summary="获取问答会话列表", **auth)
def get_qa_sessions(request, kb_id: int = None, page: int = 1, size: int = 10):
    """获取用户的问答会话列表"""
    try:
        user = get_user_from_request(request)
        
        sessions = QASession.objects.filter(user=user)
        if kb_id:
            sessions = sessions.filter(knowledge_base_id=kb_id)
        
        sessions = sessions.order_by('-updated_at')
        
        paginator = Paginator(sessions, size)
        page_obj = paginator.get_page(page)
        
        # 手动序列化会话对象
        items = []
        for session in page_obj:
            items.append({
                "id": session.id,
                "session_id": session.session_id,
                "title": session.title,
                "knowledge_base_name": session.knowledge_base.name if session.knowledge_base else None,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "updated_at": session.updated_at.isoformat() if session.updated_at else None,
            })
        
        return {
            "success": True,
            "data": {
                "items": items,
                "total": paginator.count,
                "page": page,
                "size": size,
                "pages": paginator.num_pages
            }
        }
    except ValueError as e:
        # 用户不存在的错误
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/qa/sessions/{session_id}/records", summary="获取会话问答记录")
def get_qa_records(request, session_id: str, page: int = 1, size: int = 20):
    """获取指定会话的问答记录"""
    try:
        session = QASession.objects.get(session_id=session_id)
        records = QARecord.objects.filter(session=session).order_by('created_at')
        
        paginator = Paginator(records, size)
        page_obj = paginator.get_page(page)
        
        # 手动序列化QA记录对象
        record_items = []
        for record in page_obj:
            record_items.append({
                "id": record.id,
                "question": record.question,
                "answer": record.answer,
                "confidence": float(record.confidence) if record.confidence else 0.0,
                "feedback_score": record.feedback_score,
                "feedback_comment": record.feedback_comment,
                "created_at": record.created_at.isoformat() if record.created_at else None,
            })
        
        return {
            "success": True,
            "data": {
                "session": {
                    "id": session.id,
                    "session_id": session.session_id,
                    "title": session.title,
                    "created_at": session.created_at.isoformat() if session.created_at else None,
                },
                "records": record_items,
                "total": paginator.count,
                "page": page,
                "size": size,
                "pages": paginator.num_pages
            }
        }
    except QASession.DoesNotExist:
        return {"success": False, "error": "会话不存在"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/qa/feedback", summary="问答反馈", **auth)
def submit_feedback(request, qa_record_id: int, score: int, comment: str = ""):
    """提交问答反馈"""
    try:
        qa_record = QARecord.objects.get(id=qa_record_id)
        
        # 验证评分范围
        if not (1 <= score <= 5):
            return {"success": False, "error": "评分必须在1-5之间"}
        
        qa_record.feedback_score = score
        qa_record.feedback_comment = comment
        qa_record.save()
        
        return {"success": True, "message": "反馈提交成功"}
        
    except QARecord.DoesNotExist:
        return {"success": False, "error": "问答记录不存在"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ==================== 模型配置管理 ====================

@router.get("/models/configs", summary="获取模型配置列表", **auth)
def get_model_configs(request):
    """获取模型配置列表"""
    try:
        configs = ModelConfig.objects.filter(is_active=True).order_by('-created_at')
        
        # 手动序列化模型配置对象
        items = []
        for config in configs:
            items.append({
                "id": config.id,
                "name": config.name,
                "description": config.description,
                "model_type": config.model_type,
                "model_name": config.model_name,
                "api_base_url": config.api_base_url,
                "is_default": config.is_default,
                "is_active": config.is_active,
                "created_at": config.created_at.isoformat() if config.created_at else None,
            })
        
        return {"success": True, "data": items}
    except Exception as e:
        logger.error(f"获取模型配置列表失败: {e}")
        return {"success": False, "error": str(e)}


@router.post("/models/configs", summary="创建模型配置", **auth)
def create_model_config(request, data: ModelConfigCreateSchema):
    """创建模型配置"""
    try:
        # 如果设置为默认，先取消其他默认配置
        if data.is_default:
            ModelConfig.objects.filter(is_default=True).update(is_default=False)
        
        config = ModelConfig.objects.create(**data.dict())
        return {"success": True, "data": {"id": config.id, "name": config.name}}
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.put("/models/configs/{config_id}", summary="更新模型配置", **auth)
def update_model_config(request, config_id: int, data: ModelConfigCreateSchema):
    """更新模型配置"""
    try:
        config = ModelConfig.objects.get(id=config_id)
        
        # 如果设置为默认，先取消其他默认配置
        if data.is_default:
            ModelConfig.objects.filter(is_default=True).exclude(id=config_id).update(is_default=False)
        
        # 更新配置
        for field, value in data.dict().items():
            setattr(config, field, value)
        config.save()
        
        return {"success": True, "data": {"id": config.id, "name": config.name}}
        
    except ModelConfig.DoesNotExist:
        return {"success": False, "error": "模型配置不存在"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.delete("/models/configs/{config_id}", summary="删除模型配置", **auth)
def delete_model_config(request, config_id: int):
    """删除模型配置"""
    try:
        config = ModelConfig.objects.get(id=config_id)
        
        # 检查是否是默认配置
        if config.is_default:
            return {"success": False, "error": "不能删除默认配置，请先设置其他配置为默认"}
        
        config.delete()
        return {"success": True, "message": "模型配置删除成功"}
        
    except ModelConfig.DoesNotExist:
        return {"success": False, "error": "模型配置不存在"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/models/test", summary="测试模型配置", **auth)
def test_model_config(request, config_id: int):
    """测试模型配置"""
    try:
        config = ModelConfig.objects.get(id=config_id, is_active=True)
        
        # 创建测试用的RAG系统实例
        rag_system = get_rag_system()
        
        # 配置LLM
        llm_config = {
            'model_type': config.model_type,
            'model_name': config.model_name,
            'api_key': config.api_key,
            'api_base_url': config.api_base_url,
            'max_tokens': config.max_tokens,
            'temperature': config.temperature
        }
        
        rag_system.configure_llm(config_id, llm_config)
        
        # 发送测试问题
        async def test_llm():
            return await rag_system.llm_configs[config_id].generate_response(
                "你好，请简单介绍一下你自己。", ""
            )
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(test_llm())
        
        return {
            "success": True,
            "data": {
                "test_result": "连接成功",
                "response": result['answer'][:100] + "..." if len(result['answer']) > 100 else result['answer'],
                "response_time": result['response_time']
            }
        }
        
    except ModelConfig.DoesNotExist:
        return {"success": False, "error": "模型配置不存在"}
    except Exception as e:
        return {"success": False, "error": f"测试失败: {str(e)}"}


# ==================== 系统状态和统计 ====================

@router.get("/stats", summary="获取系统统计信息")
def get_system_stats(request):
    """获取系统统计信息"""
    try:
        stats = {
            "knowledge_bases": KnowledgeBase.objects.filter(is_active=True).count(),
            "documents": Document.objects.filter(status='completed').count(),
            "qa_sessions": QASession.objects.count(),
            "qa_records": QARecord.objects.count(),
            "model_configs": ModelConfig.objects.filter(is_active=True).count(),
        }
        
        # 获取最近的问答记录
        recent_qa = QARecord.objects.order_by('-created_at')[:5]
        
        return {
            "success": True,
            "data": {
                "stats": stats,
                "recent_qa": [
                    {
                        "question": qa.question[:50] + "..." if len(qa.question) > 50 else qa.question,
                        "model_used": qa.model_used,
                        "response_time": qa.response_time,
                        "created_at": qa.created_at
                    } for qa in recent_qa
                ]
            }
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/health", summary="系统健康检查")
def health_check(request):
    """系统健康检查"""
    try:
        # 检查RAG系统
        rag_system = get_rag_system()
        
        # 检查数据库连接
        db_status = "ok"
        try:
            KnowledgeBase.objects.first()
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        # 检查模型配置
        active_models = ModelConfig.objects.filter(is_active=True).count()
        
        # 测试问答系统基本功能
        qa_test_status = "ok"
        try:
            import asyncio
            async def test_qa():
                return await rag_system.ask_question(
                    kb_id=1,
                    question="健康检查测试",
                    config_id=None,
                    top_k=1,
                    threshold=0.5
                )
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            test_result = loop.run_until_complete(test_qa())
            loop.close()
            
            # 检查返回结果是否包含必要字段
            required_fields = ['answer', 'sources', 'model_used', 'response_time']
            missing_fields = [field for field in required_fields if field not in test_result]
            
            if missing_fields:
                qa_test_status = f"error: 缺少字段 {missing_fields}"
            
        except Exception as e:
            qa_test_status = f"error: {str(e)}"
        
        return {
            "success": True,
            "data": {
                "status": "healthy" if all([
                    db_status == "ok",
                    qa_test_status == "ok",
                    active_models > 0
                ]) else "unhealthy",
                "database": db_status,
                "rag_system": "initialized" if rag_system else "not_initialized",
                "qa_system": qa_test_status,
                "active_models": active_models,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status": "unhealthy"
        }
