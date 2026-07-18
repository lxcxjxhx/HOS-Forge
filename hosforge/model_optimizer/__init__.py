"""
HOS-Forge Model Optimizer — 本地模型微调与 RAG 打标强化引擎。

基于 HOS-Model-Optimizer，集成到 HOS-Forge 信息安全生态：
    - QLoRA/LoRA 本地微调 (8GB VRAM)
    - 安全知识 RAG 打标与向量强化
    - 模型量化压缩 (GGUF/AWQ/GPTQ)
    - 一键部署推理服务
    - 信息安全领域模型评测

适用场景:
    - 用企业安全数据微调专用安全模型
    - 对 CVE/CWE 知识库做 RAG 向量打标
    - 将通用模型微调为安全审计专用模型
    - 本地/离线环境部署安全 AI Agent
"""

from hosforge.model_optimizer.config import ConfigManager
from hosforge.model_optimizer.inference import UnifiedInferenceEngine
from hosforge.model_optimizer.quantize import QuantizationError
from hosforge.model_optimizer.deploy import HardwareDetector, ConfigSelector, ServiceLauncher

# HOS-Forge 扩展
from hosforge.model_optimizer.rag_tagger import SecurityRAGTagger, RAGTaggingEngine

__all__ = [
    "ConfigManager",
    "UnifiedInferenceEngine",
    "QuantizationError",
    "HardwareDetector",
    "ConfigSelector",
    "ServiceLauncher",
    "SecurityRAGTagger",
    "RAGTaggingEngine",
]
