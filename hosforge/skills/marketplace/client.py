"""Skill 市场客户端，提供远程 skill 的列表、安装、卸载、更新和搜索功能。"""

import json
import logging
import shutil
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError

from hosforge.skills.marketplace.models import (
    InstallStatus,
    RemoteSkill,
)
from hosforge.skills.marketplace.registry import RemoteSkillRegistry
from hosforge.skills.marketplace.lockfile import LockfileManager

logger = logging.getLogger(__name__)


class MarketplaceClient:
    """Skill 市场客户端。

    提供与远程 skill 市场交互的功能，包括列出、安装、卸载、更新和搜索 skills。

    Attributes:
        registry: 远程 skill 注册表
        install_dir: skill 安装目录
        cache_dir: 缓存目录
    """

    def __init__(
        self,
        registry: Optional[RemoteSkillRegistry] = None,
        install_dir: Optional[Path] = None,
        cache_dir: Optional[Path] = None,
        lockfile_manager: Optional[LockfileManager] = None,
    ) -> None:
        """初始化 MarketplaceClient。

        Args:
            registry: 远程 skill 注册表，如果为 None 则使用默认注册表
            install_dir: skill 安装目录，如果为 None 则使用默认目录
            cache_dir: 缓存目录，如果为 None 则使用默认目录
            lockfile_manager: lockfile 管理器，如果为 None 则使用默认管理器
        """
        self.registry = registry or RemoteSkillRegistry()
        self.install_dir = install_dir or Path.home() / ".hos" / "skills"
        self.cache_dir = cache_dir or Path.home() / ".hos" / "cache"
        self.lockfile_manager = lockfile_manager or LockfileManager()

        # 确保目录存在
        self.install_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def list_remote_skills(self, force_refresh: bool = False) -> List[RemoteSkill]:
        """列出所有可用的远程 skills。

        Args:
            force_refresh: 是否强制刷新缓存

        Returns:
            RemoteSkill 实例列表
        """
        return self.registry.list_skills(force_refresh=force_refresh)

    def install_skill(self, skill_name: str, version: Optional[str] = None) -> Dict[str, Any]:
        """安装指定的 skill。

        Args:
            skill_name: skill 名称
            version: 指定版本，如果为 None 则安装最新版本

        Returns:
            包含安装结果的字典
        """
        # 查找 skill
        skill = self.registry.get_skill(skill_name)
        if skill is None:
            return {
                "success": False,
                "error": f"Skill '{skill_name}' not found in marketplace",
            }

        # 确定要安装的版本
        target_version = version
        if target_version is None:
            if skill.latest_version:
                target_version = skill.latest_version.version
            elif skill.versions:
                target_version = skill.versions[0].version
            else:
                return {
                    "success": False,
                    "error": f"No versions available for skill '{skill_name}'",
                }

        # 检查是否已安装
        skill_install_dir = self.install_dir / skill_name
        if skill_install_dir.exists():
            return {
                "success": False,
                "error": f"Skill '{skill_name}' is already installed. Use update to upgrade.",
            }

        temp_files: List[Path] = []

        try:
            # 更新状态为安装中
            skill.install_status = InstallStatus.INSTALLING

            # 1. 下载 skill 包
            download_result = self._download_skill(skill_name, target_version)

            if not download_result["success"]:
                skill.install_status = InstallStatus.ERROR
                return download_result

            package_path = Path(download_result["file_path"])
            temp_files.append(package_path)

            # 2. 解压 skill 包
            extract_result = self._extract_skill_package(
                package_path, skill_install_dir, skill_name
            )

            if not extract_result["success"]:
                skill.install_status = InstallStatus.ERROR
                self._rollback_installation(skill_name, skill_install_dir, temp_files)
                return extract_result

            # 3. 验证 skill 文件完整性
            validation_result = self._validate_skill_files(skill_install_dir, skill_name)

            if not validation_result["valid"]:
                error_msg = "; ".join(validation_result["errors"])
                skill.install_status = InstallStatus.ERROR
                self._rollback_installation(skill_name, skill_install_dir, temp_files)
                return {
                    "success": False,
                    "error": f"Skill validation failed: {error_msg}",
                }

            # 记录验证警告
            for warning in validation_result.get("warnings", []):
                logger.warning(f"Skill validation warning: {warning}")

            # 4. 保存 skill 元数据
            metadata = {
                "name": skill_name,
                "version": target_version,
                "source": skill.repository or "marketplace",
            }
            metadata_file = skill_install_dir / "metadata.json"
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            # 5. 清理临时下载文件（保留安装目录）
            for temp_file in temp_files:
                try:
                    if temp_file.exists():
                        temp_file.unlink()
                except Exception:
                    pass

            # 6. 更新状态
            skill.install_status = InstallStatus.INSTALLED
            skill.installed_version = target_version

            # 7. 如果该 skill 被锁定，确保锁定版本与安装版本一致
            if self.lockfile_manager.is_locked(skill_name):
                locked_version = self.lockfile_manager.get_locked_version(skill_name)
                if locked_version and locked_version != target_version:
                    # 更新锁定版本
                    self.lockfile_manager.lock_skill(skill_name, target_version, skill.repository or "marketplace")

            return {
                "success": True,
                "message": f"Successfully installed {skill_name} v{target_version}",
                "skill_name": skill_name,
                "version": target_version,
            }

        except Exception as e:
            skill.install_status = InstallStatus.ERROR
            self._rollback_installation(skill_name, skill_install_dir, temp_files)
            return {
                "success": False,
                "error": f"Failed to install {skill_name}: {str(e)}",
            }

    def uninstall_skill(self, skill_name: str) -> Dict[str, Any]:
        """卸载指定的 skill。

        Args:
            skill_name: skill 名称

        Returns:
            包含卸载结果的字典
        """
        skill_install_dir = self.install_dir / skill_name

        if not skill_install_dir.exists():
            return {
                "success": False,
                "error": f"Skill '{skill_name}' is not installed",
            }

        try:
            # 更新状态
            skill = self.registry.get_skill(skill_name)
            if skill:
                skill.install_status = InstallStatus.UNINSTALLING

            # 删除安装目录
            shutil.rmtree(skill_install_dir)

            # 更新状态
            if skill:
                skill.install_status = InstallStatus.NOT_INSTALLED
                skill.installed_version = None

            return {
                "success": True,
                "message": f"Successfully uninstalled {skill_name}",
                "skill_name": skill_name,
            }

        except Exception as e:
            if skill:
                skill.install_status = InstallStatus.ERROR
            return {
                "success": False,
                "error": f"Failed to uninstall {skill_name}: {str(e)}",
            }

    def update_skill(self, skill_name: str, version: Optional[str] = None) -> Dict[str, Any]:
        """更新指定的 skill。

        Args:
            skill_name: skill 名称
            version: 目标版本，如果为 None 则更新到最新版本

        Returns:
            包含更新结果的字典
        """
        skill_install_dir = self.install_dir / skill_name

        if not skill_install_dir.exists():
            return {
                "success": False,
                "error": f"Skill '{skill_name}' is not installed. Use install first.",
            }

        # 查找 skill
        skill = self.registry.get_skill(skill_name)
        if skill is None:
            return {
                "success": False,
                "error": f"Skill '{skill_name}' not found in marketplace",
            }

        # 确定目标版本
        target_version = version
        if target_version is None:
            if skill.latest_version:
                target_version = skill.latest_version.version
            elif skill.versions:
                target_version = skill.versions[0].version
            else:
                return {
                    "success": False,
                    "error": f"No versions available for skill '{skill_name}'",
                }

        # 检查当前版本
        current_version = self._get_installed_version(skill_name)
        if current_version == target_version:
            return {
                "success": True,
                "message": f"Skill '{skill_name}' is already at version {target_version}",
                "skill_name": skill_name,
                "version": target_version,
            }

        # 检查是否被锁定
        if self.lockfile_manager.is_locked(skill_name):
            locked_version = self.lockfile_manager.get_locked_version(skill_name)
            if locked_version and locked_version != target_version:
                return {
                    "success": False,
                    "error": f"Skill '{skill_name}' is locked to version {locked_version}. Unlock it first or use --force.",
                }

        try:
            # 更新状态
            skill.install_status = InstallStatus.INSTALLING

            # 下载新版本
            download_result = self._download_skill(skill_name, target_version)

            if not download_result["success"]:
                skill.install_status = InstallStatus.ERROR
                return download_result

            # 更新元数据
            metadata = {
                "name": skill_name,
                "version": target_version,
                "source": skill.repository or "marketplace",
            }
            metadata_file = skill_install_dir / "metadata.json"
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            # 更新状态
            skill.install_status = InstallStatus.INSTALLED
            skill.installed_version = target_version

            return {
                "success": True,
                "message": f"Successfully updated {skill_name} from v{current_version} to v{target_version}",
                "skill_name": skill_name,
                "old_version": current_version,
                "new_version": target_version,
            }

        except Exception as e:
            skill.install_status = InstallStatus.ERROR
            return {
                "success": False,
                "error": f"Failed to update {skill_name}: {str(e)}",
            }

    def search_skills(self, query: str) -> List[RemoteSkill]:
        """搜索 skills。

        Args:
            query: 搜索查询字符串

        Returns:
            匹配的 RemoteSkill 实例列表
        """
        all_skills = self.list_remote_skills()
        return [skill for skill in all_skills if skill.matches_query(query)]

    def _download_skill(self, skill_name: str, version: str) -> Dict[str, Any]:
        """从 GitHub releases 下载 skill 包。

        Args:
            skill_name: skill 名称
            version: 版本号

        Returns:
            包含下载结果的字典，包括 success, message, file_path 等
        """
        # 1. 获取 skill 信息
        skill = self.registry.get_skill(skill_name)
        if not skill or not skill.repository:
            return {"success": False, "error": "Skill not found or no repository"}

        # 2. 解析 GitHub URL
        try:
            owner, repo = self._parse_github_url(skill.repository)
        except ValueError as e:
            return {"success": False, "error": str(e)}

        # 3. 构造下载 URL
        download_url = self._get_release_asset_url(owner, repo, version)

        # 4. 创建临时文件
        temp_dir = Path(tempfile.gettempdir()) / "hosforge_downloads"
        temp_dir.mkdir(parents=True, exist_ok=True)

        # 尝试 tar.gz 和 zip 格式
        for ext in [".tar.gz", ".zip"]:
            filename = f"{repo}-{version}{ext}"
            temp_file = temp_dir / filename

            # 5. 下载文件（带重试）
            if self._download_with_retry(download_url + ext, temp_file):
                return {
                    "success": True,
                    "message": f"Downloaded {skill_name} v{version}",
                    "file_path": str(temp_file),
                }

        return {
            "success": False,
            "error": f"Failed to download {skill_name} v{version} after retries",
        }

    def _parse_github_url(self, url: str) -> Tuple[str, str]:
        """解析 GitHub URL 返回 (owner, repo)。

        Args:
            url: GitHub URL，如 https://github.com/owner/repo

        Returns:
            (owner, repo) 元组

        Raises:
            ValueError: 如果 URL 格式无效
        """
        # 移除末尾斜杠
        url = url.rstrip("/")

        # 支持格式:
        # - https://github.com/owner/repo
        # - https://github.com/owner/repo/releases/...
        if "github.com" not in url:
            raise ValueError(f"Invalid GitHub URL: {url}")

        parts = url.split("/")
        # 找到 github.com 后的 owner/repo
        try:
            github_idx = parts.index("github.com")
            if len(parts) < github_idx + 3:
                raise ValueError(f"Invalid GitHub URL: {url}")
            owner = parts[github_idx + 1]
            repo = parts[github_idx + 2]
            # 移除可能的 .git 后缀
            if repo.endswith(".git"):
                repo = repo[:-4]
            return owner, repo
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid GitHub URL: {url}") from e

    def _get_release_asset_url(self, owner: str, repo: str, version: str) -> str:
        """构造 GitHub release asset 下载 URL。

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            version: 版本号

        Returns:
            下载 URL 基础路径（不含扩展名）
        """
        # GitHub release asset URL 格式:
        # https://github.com/{owner}/{repo}/releases/download/{version}/{asset_name}
        return f"https://github.com/{owner}/{repo}/releases/download/{version}/{repo}-{version}"

    def _download_with_retry(
        self, url: str, dest: Path, max_retries: int = 3, retry_delay: float = 1.0
    ) -> bool:
        """带重试的下载。

        Args:
            url: 下载 URL
            dest: 目标文件路径
            max_retries: 最大重试次数
            retry_delay: 重试间隔（秒）

        Returns:
            是否下载成功
        """
        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(url)
                req.add_header("User-Agent", "HOS-Forge-Skill-Marketplace")

                with urllib.request.urlopen(req, timeout=30) as response:
                    with open(dest, "wb") as f:
                        shutil.copyfileobj(response, f)

                logger.info(f"Downloaded {url} to {dest}")
                return True

            except HTTPError as e:
                logger.warning(f"HTTP error {e.code} on attempt {attempt + 1}/{max_retries}: {e.reason}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
            except URLError as e:
                logger.warning(f"Network error on attempt {attempt + 1}/{max_retries}: {e.reason}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
            except Exception as e:
                logger.warning(f"Unexpected error on attempt {attempt + 1}/{max_retries}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)

        # 清理临时文件
        if dest.exists():
            try:
                dest.unlink()
            except Exception:
                pass

        return False

    def _get_installed_version(self, skill_name: str) -> Optional[str]:
        """获取已安装 skill 的版本。

        Args:
            skill_name: skill 名称

        Returns:
            版本号字符串，如果未安装则返回 None
        """
        metadata_file = self.install_dir / skill_name / "metadata.json"

        if not metadata_file.exists():
            return None

        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            return metadata.get("version")
        except Exception:
            return None

    def _extract_skill_package(
        self, package_path: Path, target_dir: Path, skill_name: str
    ) -> Dict[str, Any]:
        """解压 skill 包到目标目录。

        Args:
            package_path: 压缩包文件路径（tar.gz 或 zip）
            target_dir: 解压目标目录
            skill_name: skill 名称

        Returns:
            包含解压结果的字典
        """
        try:
            # 确保目标目录存在
            target_dir.mkdir(parents=True, exist_ok=True)

            # 创建临时解压目录
            temp_extract_dir = target_dir / ".temp_extract"
            temp_extract_dir.mkdir(parents=True, exist_ok=True)

            package_str = str(package_path)

            # 根据扩展名选择解压方式
            if package_str.endswith(".tar.gz") or package_str.endswith(".tgz"):
                with tarfile.open(package_path, "r:gz") as tar:
                    # Python 3.14+ 需要 filter 参数
                    try:
                        tar.extractall(temp_extract_dir, filter="data")
                    except TypeError:
                        # Python < 3.12 不支持 filter 参数
                        tar.extractall(temp_extract_dir)
            elif package_str.endswith(".zip"):
                with zipfile.ZipFile(package_path, "r") as zip_ref:
                    zip_ref.extractall(temp_extract_dir)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported package format: {package_path.suffix}",
                }

            # 处理压缩包内的目录结构（去除顶层目录）
            extracted_items = list(temp_extract_dir.iterdir())
            if len(extracted_items) == 1 and extracted_items[0].is_dir():
                # 只有一个顶层目录，将其内容移动到目标目录
                top_dir = extracted_items[0]
                for item in top_dir.iterdir():
                    dest = target_dir / item.name
                    shutil.move(str(item), str(dest))
                # 删除临时目录
                shutil.rmtree(temp_extract_dir, ignore_errors=True)
                # 删除空的顶层目录
                shutil.rmtree(top_dir, ignore_errors=True)
            else:
                # 多个文件或目录，直接移动到目标目录
                for item in extracted_items:
                    dest = target_dir / item.name
                    shutil.move(str(item), str(dest))
                # 删除临时目录
                shutil.rmtree(temp_extract_dir, ignore_errors=True)

            logger.info(f"Extracted {package_path} to {target_dir}")
            return {
                "success": True,
                "message": f"Successfully extracted to {target_dir}",
                "extract_dir": str(target_dir),
            }

        except tarfile.TarError as e:
            logger.error(f"Failed to extract tar.gz: {e}")
            # 清理临时目录
            if temp_extract_dir.exists():
                shutil.rmtree(temp_extract_dir, ignore_errors=True)
            return {"success": False, "error": f"Failed to extract tar.gz: {str(e)}"}

        except zipfile.BadZipFile as e:
            logger.error(f"Failed to extract zip: {e}")
            # 清理临时目录
            if temp_extract_dir.exists():
                shutil.rmtree(temp_extract_dir, ignore_errors=True)
            return {"success": False, "error": f"Failed to extract zip: {str(e)}"}

        except Exception as e:
            logger.error(f"Unexpected error during extraction: {e}")
            # 清理临时目录
            if temp_extract_dir.exists():
                shutil.rmtree(temp_extract_dir, ignore_errors=True)
            return {"success": False, "error": f"Extraction failed: {str(e)}"}

    def _validate_skill_files(self, skill_dir: Path, skill_name: str) -> Dict[str, Any]:
        """验证 skill 文件完整性。

        Args:
            skill_dir: skill 安装目录
            skill_name: skill 名称

        Returns:
            包含验证结果的字典
        """
        errors = []
        warnings = []

        # 检查目录是否存在
        if not skill_dir.exists():
            return {
                "valid": False,
                "errors": [f"Skill directory does not exist: {skill_dir}"],
                "warnings": [],
            }

        # 检查必要文件
        required_files = ["__init__.py"]
        optional_files = ["README.md", "metadata.json"]

        # 至少需要 __init__.py 或 <skill_name>.py
        has_init = (skill_dir / "__init__.py").exists()
        has_skill_file = (skill_dir / f"{skill_name}.py").exists()

        if not has_init and not has_skill_file:
            errors.append(
                f"Missing required files: __init__.py or {skill_name}.py"
            )

        # 检查其他必要文件
        for req_file in required_files:
            if req_file == "__init__.py" and (has_init or has_skill_file):
                continue
            if not (skill_dir / req_file).exists():
                errors.append(f"Missing required file: {req_file}")

        # 检查可选文件（只产生警告）
        for opt_file in optional_files:
            if not (skill_dir / opt_file).exists():
                warnings.append(f"Missing optional file: {opt_file}")

        # 验证 metadata.json（如果存在）
        metadata_file = skill_dir / "metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)

                # 检查必要字段
                if "name" not in metadata:
                    errors.append("metadata.json missing required field: name")
                if "version" not in metadata:
                    errors.append("metadata.json missing required field: version")

                # 验证 name 字段
                if metadata.get("name") != skill_name:
                    warnings.append(
                        f"metadata.json name '{metadata.get('name')}' "
                        f"does not match skill_name '{skill_name}'"
                    )

            except json.JSONDecodeError as e:
                errors.append(f"Invalid metadata.json: {str(e)}")
            except Exception as e:
                errors.append(f"Failed to read metadata.json: {str(e)}")

        is_valid = len(errors) == 0

        return {
            "valid": is_valid,
            "errors": errors,
            "warnings": warnings,
        }

    def _rollback_installation(
        self, skill_name: str, skill_dir: Path, temp_files: Optional[List[Path]] = None
    ) -> Dict[str, Any]:
        """回滚安装操作，清理文件和目录。

        Args:
            skill_name: skill 名称
            skill_dir: skill 安装目录
            temp_files: 需要清理的临时文件列表

        Returns:
            包含回滚结果的字典
        """
        logger.info(f"Rolling back installation of {skill_name}")

        errors = []

        # 清理临时文件
        if temp_files:
            for temp_file in temp_files:
                try:
                    if temp_file.exists():
                        if temp_file.is_dir():
                            shutil.rmtree(temp_file, ignore_errors=False)
                        else:
                            temp_file.unlink()
                        logger.debug(f"Cleaned up temp file: {temp_file}")
                except Exception as e:
                    error_msg = f"Failed to cleanup temp file {temp_file}: {str(e)}"
                    logger.warning(error_msg)
                    errors.append(error_msg)

        # 清理安装目录
        if skill_dir.exists():
            try:
                shutil.rmtree(skill_dir)
                logger.info(f"Removed skill directory: {skill_dir}")
            except Exception as e:
                error_msg = f"Failed to remove skill directory {skill_dir}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        if errors:
            return {
                "success": False,
                "errors": errors,
            }

        return {
            "success": True,
            "message": f"Successfully rolled back {skill_name}",
        }

    def get_installed_skills(self) -> List[Dict[str, Any]]:
        """获取所有已安装的 skills。

        Returns:
            已安装 skill 的信息列表
        """
        installed = []

        if not self.install_dir.exists():
            return installed

        for skill_dir in self.install_dir.iterdir():
            if skill_dir.is_dir():
                metadata_file = skill_dir / "metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file, "r", encoding="utf-8") as f:
                            metadata = json.load(f)
                        installed.append(metadata)
                    except Exception:
                        pass

        return installed
