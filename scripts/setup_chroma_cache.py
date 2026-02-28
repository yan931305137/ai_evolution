#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChromaDB 模型缓存初始化脚本
确保模型已缓存到项目内部，避免每次运行时重新下载
"""
import os
import sys

def setup_chroma_cache():
    """设置 ChromaDB 缓存目录并预加载模型"""

    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cache_dir = os.path.join(project_root, '.cache', 'chroma')

    # 创建缓存目录
    os.makedirs(cache_dir, exist_ok=True)

    # 设置环境变量
    os.environ['CHROMA_CACHE_DIR'] = cache_dir
    os.environ['TRANSFORMERS_CACHE'] = os.path.join(project_root, '.cache', 'transformers')
    os.environ['HF_HOME'] = os.path.join(project_root, '.cache', 'huggingface')

    print("=" * 60)
    print("ChromaDB 模型缓存设置")
    print("=" * 60)
    print(f"缓存目录: {cache_dir}")
    print(f"环境变量已设置:")
    print(f"  CHROMA_CACHE_DIR={os.environ.get('CHROMA_CACHE_DIR')}")
    print(f"  TRANSFORMERS_CACHE={os.environ.get('TRANSFORMERS_CACHE')}")
    print(f"  HF_HOME={os.environ.get('HF_HOME')}")
    print()

    # 检查模型是否已缓存
    model_file = os.path.join(cache_dir, 'onnx_models', 'all-MiniLM-L6-v2', 'model.onnx')
    if os.path.exists(model_file):
        print("✅ 模型已缓存，无需重新下载")
        print(f"   模型路径: {model_file}")
        return True

    print("⚠️  模型未缓存，开始下载...")
    print("   注意: 首次下载需要几分钟，请耐心等待")
    print()

    try:
        # 导入 ChromaDB 并触发模型下载
        import chromadb
        from chromadb.utils import embedding_functions

        # 创建临时客户端
        client = chromadb.EphemeralClient()

        # 使用默认嵌入函数（会触发模型下载）
        ef = embedding_functions.DefaultEmbeddingFunction()

        # 调用一次确保模型加载
        result = ef(["test"])
        print(f"   模型加载成功，嵌入维度: {len(result[0])}")

        print()
        print("✅ 模型下载并缓存成功！")
        print(f"   模型文件: {model_file}")
        return True

    except Exception as e:
        print(f"❌ 模型下载失败: {e}")
        print()
        print("可能的原因:")
        print("  1. 网络连接问题")
        print("  2. 磁盘空间不足")
        print("  3. 权限问题")
        return False

if __name__ == '__main__':
    success = setup_chroma_cache()

    if success:
        print()
        print("=" * 60)
        print("✅ 设置完成！现在可以运行测试了")
        print("=" * 60)
        print()
        print("运行测试命令:")
        print(f"  cd {os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}")
        print("  python -m pytest tests/test_memory_system.py -v")
        print()
        sys.exit(0)
    else:
        print()
        print("=" * 60)
        print("❌ 设置失败，请检查错误信息")
        print("=" * 60)
        print()
        sys.exit(1)
