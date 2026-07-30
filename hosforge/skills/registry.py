"""Skill 注册表模块，管理 Skill 的注册、注销和执行。"""

from typing import Any, Dict, List, Optional

from hosforge.skills.base_skill import Skill, SkillResult
from hosforge.skills.pipeline import SkillPipeline


class SkillRegistry:
    """Skill 注册表，管理所有已注册的 Skill。

    提供 Skill 的注册、注销、获取、列表和执行功能。
    """

    def __init__(self) -> None:
        """初始化空的 Skill 注册表。"""
        self._skills: Dict[str, Skill] = {}
        self._pipelines: Dict[str, SkillPipeline] = {}

    def register(self, skill: Skill) -> None:
        """注册一个 Skill。

        Args:
            skill: 要注册的 Skill 实例
        """
        self._skills[skill.name] = skill

    def unregister(self, skill_name: str) -> None:
        """注销一个 Skill。

        Args:
            skill_name: 要注销的 Skill 名称
        """
        if skill_name in self._skills:
            del self._skills[skill_name]

    def get(self, skill_name: str) -> Optional[Skill]:
        """获取一个 Skill。

        Args:
            skill_name: Skill 名称

        Returns:
            Skill 实例，如果不存在则返回 None
        """
        return self._skills.get(skill_name)

    def list_skills(self) -> List[Skill]:
        """列出所有已注册的 Skill。

        Returns:
            Skill 实例列表
        """
        return list(self._skills.values())

    def execute_skill(self, skill_name: str, **kwargs) -> SkillResult:
        """执行指定的 Skill。

        Args:
            skill_name: Skill 名称
            **kwargs: 传递给 Skill 的参数

        Returns:
            SkillResult 实例，包含执行结果
        """
        skill = self.get(skill_name)
        if skill is None:
            return SkillResult(success=False, error=f"Skill '{skill_name}' not found")

        if not skill.validate_input(**kwargs):
            return SkillResult(success=False, error="Invalid input parameters")

        try:
            result = skill.execute(**kwargs)
            return SkillResult(success=True, data=result, metadata={"skill_name": skill_name})
        except Exception as e:
            return SkillResult(success=False, error=str(e), metadata={"skill_name": skill_name})

    def register_pipeline(self, pipeline: SkillPipeline) -> None:
        """注册一个管线。

        Args:
            pipeline: 要注册的管线
        """
        self._pipelines[pipeline.name] = pipeline

    def unregister_pipeline(self, pipeline_name: str) -> None:
        """注销一个管线。

        Args:
            pipeline_name: 要注销的管线名称
        """
        if pipeline_name in self._pipelines:
            del self._pipelines[pipeline_name]

    def get_pipeline(self, pipeline_name: str) -> Optional[SkillPipeline]:
        """获取一个管线。

        Args:
            pipeline_name: 管线名称

        Returns:
            SkillPipeline 实例，如果不存在则返回 None
        """
        return self._pipelines.get(pipeline_name)

    def list_pipelines(self) -> List[SkillPipeline]:
        """列出所有已注册的管线。

        Returns:
            SkillPipeline 实例列表
        """
        return list(self._pipelines.values())

    def execute_pipeline(self, pipeline_name: str, initial_input: Dict[str, Any]) -> Dict[str, Any]:
        """执行指定的管线。

        Args:
            pipeline_name: 管线名称
            initial_input: 初始输入数据

        Returns:
            包含执行结果的字典
        """
        pipeline = self.get_pipeline(pipeline_name)
        if pipeline is None:
            return {"success": False, "error": f"Pipeline '{pipeline_name}' not found"}

        try:
            result = pipeline.execute(initial_input)
            return {
                "success": result.success,
                "step_results": [
                    {
                        "step_name": sr.step_name,
                        "success": sr.success,
                        "output": sr.output,
                        "error": sr.error,
                        "skipped": sr.skipped,
                    }
                    for sr in result.step_results
                ],
                "final_output": result.final_output,
                "error": result.error,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
