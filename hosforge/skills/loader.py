"""Skill 加载器模块，支持从目录和模块动态加载 Skill。"""

import importlib
import importlib.util
import inspect
import logging
import os
from pathlib import Path
from typing import Any, List, Optional

from hosforge.skills.base_skill import Skill

logger = logging.getLogger(__name__)


class SkillLoader:
    """Skill 加载器，负责从不同来源动态加载 Skill。"""

    def load_from_directory(self, path: str) -> List[Skill]:
        """从本地目录动态加载 skills。

        递归扫描目录，查找包含 Skill 子类的 Python 模块并实例化。

        Args:
            path: 目录路径

        Returns:
            加载到的 Skill 实例列表
        """
        skills: List[Skill] = []
        dir_path = Path(path)

        if not dir_path.exists() or not dir_path.is_dir():
            logger.warning(f"目录不存在或不是目录: {path}")
            return skills

        for py_file in dir_path.rglob("*.py"):
            if py_file.name.startswith("_"):
                continue

            module_skills = self._load_module_from_file(py_file)
            skills.extend(module_skills)

        logger.info(f"从目录 {path} 加载了 {len(skills)} 个 skills")
        return skills

    def load_from_module(self, module_path: str) -> List[Skill]:
        """从 Python 模块加载 skills。

        Args:
            module_path: 模块路径，如 "hosforge.skills.security.github_skill"

        Returns:
            加载到的 Skill 实例列表
        """
        skills: List[Skill] = []

        try:
            module = importlib.import_module(module_path)
            module_skills = self._extract_skills_from_module(module)
            skills.extend(module_skills)
            logger.info(f"从模块 {module_path} 加载了 {len(skills)} 个 skills")
        except ImportError as e:
            logger.error(f"无法导入模块 {module_path}: {e}")
        except Exception as e:
            logger.error(f"加载模块 {module_path} 时出错: {e}")

        return skills

    def discover_skills(self, paths: List[str]) -> List[Skill]:
        """自动发现并加载 skills。

        遍历多个路径，支持目录和模块路径混合。

        Args:
            paths: 路径列表，可以是目录或模块路径

        Returns:
            发现并加载的所有 Skill 实例列表
        """
        all_skills: List[Skill] = []

        for path in paths:
            if os.path.isdir(path):
                skills = self.load_from_directory(path)
            else:
                skills = self.load_from_module(path)
            all_skills.extend(skills)

        logger.info(f"共发现并加载 {len(all_skills)} 个 skills")
        return all_skills

    def _load_module_from_file(self, file_path: Path) -> List[Skill]:
        """从单个 Python 文件加载 skills。

        Args:
            file_path: Python 文件路径

        Returns:
            从该文件加载的 Skill 实例列表
        """
        skills: List[Skill] = []

        try:
            module_name = file_path.stem
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                logger.warning(f"无法为 {file_path} 创建模块规范")
                return skills

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            module_skills = self._extract_skills_from_module(module)
            skills.extend(module_skills)

        except Exception as e:
            logger.error(f"加载文件 {file_path} 时出错: {e}")

        return skills

    def _extract_skills_from_module(self, module: Any) -> List[Skill]:
        """从模块中提取 Skill 实例。

        查找模块中所有 Skill 的子类并实例化。

        Args:
            module: Python 模块对象

        Returns:
            模块中的 Skill 实例列表
        """
        skills: List[Skill] = []

        for name, obj in inspect.getmembers(module, inspect.isclass):
            if self._is_skill_subclass(obj):
                try:
                    skill_instance = obj()
                    skills.append(skill_instance)
                    logger.debug(f"实例化 Skill: {name}")
                except Exception as e:
                    logger.error(f"实例化 Skill {name} 时出错: {e}")

        return skills

    def _is_skill_subclass(self, cls: type) -> bool:
        """检查类是否为 Skill 的子类且可实例化。

        Args:
            cls: 要检查的类

        Returns:
            是否为可实例化的 Skill 子类
        """
        if not inspect.isclass(cls):
            return False

        if cls is Skill:
            return False

        if not issubclass(cls, Skill):
            return False

        if inspect.isabstract(cls):
            return False

        return True
