## 项目概述
- **名称**: 自媒体内容生产系统
- **功能**: 数据驱动、自动进化的自媒体内容生产系统，通过分析历史数据持续优化创作策略

### 节点清单
| 节点名 | 文件位置 | 类型 | 功能描述 | 分支逻辑 | 配置文件 |
|-------|---------|------|---------|---------|---------|
| feishu_read | `src/graphs/nodes/feishu_read_node.py` | task | 从飞书多维表格B读取历史数据 | - | - |
| analysis_optimization | `src/graphs/nodes/analysis_optimization_node.py` | agent | 分析历史数据，生成优化策略 | - | `config/analysis_optimization_llm_cfg.json` |
| topic_generation | `src/graphs/nodes/topic_generation_node.py` | agent | 根据核心主题生成爆款选题 | - | `config/topic_generation_llm_cfg.json` |
| content_generation | `src/graphs/nodes/content_generation_node.py` | agent | 基于选题生成完整内容草稿 | - | `config/content_generation_llm_cfg.json` |
| feishu_write | `src/graphs/nodes/feishu_write_node.py` | task | 将生成内容写入飞书多维表格A | - | - |

**类型说明**: task(task节点) / agent(大模型) / condition(条件分支) / looparray(列表循环) / loopcond(条件循环)

## 子图清单
| 子图名 | 文件位置 | 功能描述 | 被调用节点 |
|-------|---------|------|---------|-----------|
| 无 | - | - | - |

## 技能使用
- 节点`topic_generation`、`content_generation`、`analysis_optimization`使用大语言模型(llm)技能
- 节点`feishu_read`、`feishu_write`使用飞书多维表格(feishu-base)技能
