import requests
import re
import json
from typing import List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class RequirementItem:
    """Data structure for individual requirements"""
    id: str
    title: str
    description: str
    priority: str  # High, Medium, Low
    category: str  # Functional, Non-functional, Technical
    source: str    # Which part of conversation this came from


@dataclass
class PRDData:
    """Complete PRD data structure"""
    project_name: str
    version: str
    creation_date: str
    overview: str
    objectives: List[str]
    target_users: List[str]
    functional_requirements: List[RequirementItem]
    non_functional_requirements: List[RequirementItem]
    technical_requirements: List[RequirementItem]
    constraints: List[str]
    assumptions: List[str]


class ConversationAnalyzer:
    """Analyzes conversation data to extract meaningful information"""
    
    def __init__(self):
        self.requirement_patterns = {
            'functional': [
                r'(?i)用户(?:需要|想要|希望|应该能够)(.+?)(?:[。\n]|$)',
                r'(?i)系统(?:需要|必须|应该)(.+?)(?:[。\n]|$)',
                r'(?i)功能(?:包括|需要|要求)(.+?)(?:[。\n]|$)',
                r'(?i)实现(.+?)功能',
                r'(?i)I need (.+?)(?:[.。\n]|$)',
                r'(?i)The system should (.+?)(?:[.。\n]|$)',
                r'(?i)We need to (.+?)(?:[.。\n]|$)'
            ],
            'non_functional': [
                r'(?i)性能(?:要求|需求)(.+?)(?:[。\n]|$)',
                r'(?i)(?:响应时间|加载时间)(?:需要|应该|不超过)(.+?)(?:[。\n]|$)',
                r'(?i)(?:并发|用户数)(.+?)(?:[。\n]|$)',
                r'(?i)(?:安全|权限|认证)(.+?)(?:[。\n]|$)',
                r'(?i)(?:可用性|稳定性|可靠性)(.+?)(?:[。\n]|$)',
                r'(?i)Performance (.+?)(?:[.。\n]|$)',
                r'(?i)Security (.+?)(?:[.。\n]|$)',
                r'(?i)The system must be (.+?)(?:[.。\n]|$)'
            ],
            'technical': [
                r'(?i)技术(?:栈|架构|选型)(.+?)(?:[。\n]|$)',
                r'(?i)使用(.+?)(?:框架|技术|数据库|服务)',
                r'(?i)(?:API|接口|数据库|服务器)(.+?)(?:[。\n]|$)',
                r'(?i)(?:部署|环境|平台)(.+?)(?:[。\n]|$)',
                r'(?i)Using (.+?) framework',
                r'(?i)Built with (.+?)(?:[.。\n]|$)',
                r'(?i)Database (.+?)(?:[.。\n]|$)',
                r'(?i)API (.+?)(?:[.。\n]|$)'
            ]
        }
        
        self.objective_patterns = [
            r'(?i)目标是(.+?)(?:[。\n]|$)',
            r'(?i)目的是(.+?)(?:[。\n]|$)',
            r'(?i)希望(?:实现|达到)(.+?)(?:[。\n]|$)',
            r'(?i)The goal is (.+?)(?:[.。\n]|$)',
            r'(?i)We want to (.+?)(?:[.。\n]|$)',
            r'(?i)The objective is (.+?)(?:[.。\n]|$)'
        ]
        
        self.user_patterns = [
            r'(?i)(?:目标)?用户(?:是|包括|主要是)(.+?)(?:[。\n]|$)',
            r'(?i)面向(.+?)用户',
            r'(?i)Target users (.+?)(?:[.。\n]|$)',
            r'(?i)Users are (.+?)(?:[.。\n]|$)',
            r'(?i)For (.+?) users'
        ]

    def extract_project_info(self, conversation: str) -> Dict[str, Any]:
        """Extract basic project information"""
        info = {
            'project_name': self._extract_project_name(conversation),
            'overview': self._extract_overview(conversation),
            'objectives': self._extract_objectives(conversation),
            'target_users': self._extract_target_users(conversation)
        }
        return info

    def _extract_project_name(self, text: str) -> str:
        """Extract project name from conversation"""
        patterns = [
            r'(?i)项目(?:名称|叫做|是)(.+?)(?:[。\n]|$)',
            r'(?i)开发(.+?)(?:系统|平台|应用|项目)',
            r'(?i)Project (?:name is )?(.+?)(?:[.。\n]|$)',
            r'(?i)Building (.+?) (?:system|platform|application)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            if matches:
                return matches[0].strip()
        
        return "未命名项目"

    def _extract_overview(self, text: str) -> str:
        """Extract project overview"""
        sentences = re.split(r'[。\n.!?]', text)
        overview_sentences = []
        
        for sentence in sentences[:5]:  # Take first few sentences
            if len(sentence.strip()) > 10:
                overview_sentences.append(sentence.strip())
        
        return '。'.join(overview_sentences[:3])

    def _extract_objectives(self, text: str) -> List[str]:
        """Extract project objectives"""
        objectives = []
        for pattern in self.objective_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            objectives.extend([match.strip() for match in matches])
        
        return list(set(objectives))

    def _extract_target_users(self, text: str) -> List[str]:
        """Extract target users"""
        users = []
        for pattern in self.user_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            users.extend([match.strip() for match in matches])
        
        return list(set(users))

    def extract_requirements(self, conversation: str) -> Dict[str, List[RequirementItem]]:
        """Extract requirements from conversation"""
        requirements = {
            'functional': [],
            'non_functional': [],
            'technical': []
        }
        
        for req_type, patterns in self.requirement_patterns.items():
            req_id = 1
            for pattern in patterns:
                matches = re.findall(pattern, conversation, re.MULTILINE)
                for match in matches:
                    if len(match.strip()) > 5:  # Filter out very short matches
                        requirement = RequirementItem(
                            id=f"{req_type[0].upper()}{req_id:03d}",
                            title=match.strip()[:50] + ("..." if len(match.strip()) > 50 else ""),
                            description=match.strip(),
                            priority=self._determine_priority(match),
                            category=req_type.title(),
                            source="对话分析"
                        )
                        requirements[req_type].append(requirement)
                        req_id += 1
        
        return requirements

    def _determine_priority(self, text: str) -> str:
        """Determine requirement priority based on keywords"""
        high_priority_keywords = ['必须', '关键', '重要', '核心', 'critical', 'must', 'essential', 'key']
        medium_priority_keywords = ['应该', '需要', 'should', 'need', 'important']
        
        text_lower = text.lower()
        
        for keyword in high_priority_keywords:
            if keyword in text_lower:
                return "High"
        
        for keyword in medium_priority_keywords:
            if keyword in text_lower:
                return "Medium"
        
        return "Low"


class PRDGenerator:
    """Generates PRD documents from analyzed conversation data"""
    
    def __init__(self):
        self.template = """
# 产品需求文档 (PRD)

## 基本信息
- **项目名称**: {project_name}
- **版本**: {version}
- **创建日期**: {creation_date}
- **文档状态**: 草稿

## 1. 产品概述
{overview}

## 2. 产品目标
{objectives}

## 3. 目标用户
{target_users}

## 4. 功能需求
{functional_requirements}

## 5. 非功能需求
{non_functional_requirements}

## 6. 技术需求
{technical_requirements}

## 7. 约束条件
{constraints}

## 8. 假设条件
{assumptions}

## 9. 验收标准
- 所有功能需求已实现并通过测试
- 非功能需求满足既定标准
- 用户验收测试通过

## 10. 风险评估
- **技术风险**: 需要评估技术实现的可行性
- **时间风险**: 需要合理安排开发周期
- **资源风险**: 需要确保有足够的开发资源

---
*此文档由AI自动生成，请人工审核并完善*
"""

    def generate_prd(self, prd_data: PRDData) -> str:
        """Generate formatted PRD document"""
        
        def format_list(items: List[str], prefix: str = "- ") -> str:
            if not items:
                return "暂无"
            return '\n'.join([f"{prefix}{item}" for item in items])
        
        def format_requirements(requirements: List[RequirementItem]) -> str:
            if not requirements:
                return "暂无"
            
            formatted = []
            for req in requirements:
                formatted.append(f"""
### {req.id}: {req.title}
- **描述**: {req.description}
- **优先级**: {req.priority}
- **来源**: {req.source}
""")
            return '\n'.join(formatted)
        
        return self.template.format(
            project_name=prd_data.project_name,
            version=prd_data.version,
            creation_date=prd_data.creation_date,
            overview=prd_data.overview or "待补充产品概述",
            objectives=format_list(prd_data.objectives),
            target_users=format_list(prd_data.target_users),
            functional_requirements=format_requirements(prd_data.functional_requirements),
            non_functional_requirements=format_requirements(prd_data.non_functional_requirements),
            technical_requirements=format_requirements(prd_data.technical_requirements),
            constraints=format_list(prd_data.constraints),
            assumptions=format_list(prd_data.assumptions)
        )


class ConversationToPRD:
    """Main class that orchestrates the conversion process"""
    
    def __init__(self):
        self.analyzer = ConversationAnalyzer()
        self.generator = PRDGenerator()
    
    def process_conversation(self, conversation_text: str, project_name: str = None) -> str:
        """Process conversation and generate PRD"""
        
        # Extract basic information
        project_info = self.analyzer.extract_project_info(conversation_text)
        
        # Override project name if provided
        if project_name:
            project_info['project_name'] = project_name
        
        # Extract requirements
        requirements = self.analyzer.extract_requirements(conversation_text)
        
        # Create PRD data structure
        prd_data = PRDData(
            project_name=project_info['project_name'],
            version="v1.0",
            creation_date=datetime.now().strftime("%Y-%m-%d"),
            overview=project_info['overview'],
            objectives=project_info['objectives'],
            target_users=project_info['target_users'],
            functional_requirements=requirements['functional'],
            non_functional_requirements=requirements['non_functional'],
            technical_requirements=requirements['technical'],
            constraints=[
                "时间约束：根据项目进度安排",
                "预算约束：在预算范围内完成",
                "技术约束：使用现有技术栈"
            ],
            assumptions=[
                "用户具备基本的计算机使用能力",
                "系统运行环境稳定",
                "网络连接正常"
            ]
        )
        
        # Generate PRD document
        return self.generator.generate_prd(prd_data)
    
    def process_from_file(self, file_path: str, project_name: str = None) -> str:
        """Process conversation from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                conversation_text = file.read()
            return self.process_conversation(conversation_text, project_name)
        except FileNotFoundError:
            return "错误：找不到指定的文件"
        except Exception as e:
            return f"错误：处理文件时出现异常 - {str(e)}"
    
    def save_prd(self, prd_content: str, output_path: str) -> bool:
        """Save PRD to file"""
        try:
            with open(output_path, 'w', encoding='utf-8') as file:
                file.write(prd_content)
            return True
        except Exception as e:
            print(f"保存文件时出现错误：{str(e)}")
            return False


# 示例使用和测试
def main():
    """Main function with example usage"""
    
    # 示例对话数据
    sample_conversation = """
    用户：我想开发一个在线教育平台，主要面向大学生和职场人士。
    AI：好的，请详细描述一下您的需求。
    
    用户：系统需要支持在线视频课程播放，用户注册登录功能，课程管理功能。
    用户还应该能够购买课程，观看进度跟踪，还需要讨论区功能让学生互动。
    
    AI：明白了。对于性能方面有什么要求吗？
    
    用户：系统必须支持至少1000个并发用户，响应时间不应该超过3秒。
    安全方面需要保护用户隐私数据，支持SSL加密。
    
    AI：技术栈方面有偏好吗？
    
    用户：前端使用React，后端用Python Django，数据库用PostgreSQL。
    需要部署在AWS云服务上。目标是创建一个现代化的学习平台，
    提升在线教育体验。
    """
    
    # 创建转换器实例
    converter = ConversationToPRD()
    
    # 处理对话并生成PRD
    print("正在分析对话内容...")
    prd_content = converter.process_conversation(sample_conversation, "在线教育平台")
    
    print("生成的PRD文档：")
    print("=" * 50)
    print(prd_content)
    
    # 保存到文件
    output_file = "generated_prd.md"
    if converter.save_prd(prd_content, output_file):
        print(f"\nPRD文档已保存到: {output_file}")
    
    print("\n使用示例：")
    print("1. 直接处理文本：converter.process_conversation(conversation_text)")
    print("2. 从文件处理：converter.process_from_file('conversation.txt')")
    print("3. 保存结果：converter.save_prd(prd_content, 'output.md')")


if __name__ == "__main__":
    main()