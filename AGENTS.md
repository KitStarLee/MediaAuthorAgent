## 项目概述
- **名称**: 自媒体内容生产系统（简化版）
- **功能**: 基于核心主题词批量生成自媒体内容，支持历史数据优化和可配置内容数量

### 节点清单
| 节点名 | 文件位置 | 类型 | 功能描述 | 分支逻辑 | 配置文件 |
|-------|---------|------|---------|---------|---------|
| analysis_optimization | `nodes/analysis_optimization_node.py` | agent | 分析历史数据，生成优化策略 | - | `config/analysis_optimization_llm_cfg.json` |
| topic_generation | `nodes/topic_generation_node.py` | agent | 生成爆款选题 | - | `config/topic_generation_llm_cfg.json` |
| content_generation | `nodes/content_generation_node.py` | agent | 生成多篇完整内容，包含标题、内容、话题 | - | `config/content_generation_llm_cfg.json` |

**类型说明**: task(task节点) / agent(大模型) / condition(条件分支) / looparray(列表循环) / loopcond(条件循环)

## 子图清单
无

## 技能使用
- 节点`topic_generation`使用大语言模型技能
- 节点`content_generation`使用大语言模型技能
- 节点`analysis_optimization`使用大语言模型技能

## API调用示例
```json
{
  "core_topic": "AI短视频创作",
  "historical_data": null,
  "content_count": 3
}
```

## 输出格式
```json
{
  "topics": ["选题1", "选题2", "选题3", "选题4", "选题5"],
  "contents": [
    {
      "title": "文章标题",
      "content": "完整文章内容",
      "topics": ["#话题1", "#话题2", "#话题3"]
    }
  ],
  "optimization_strategy": {
    "has_data": false,
    "message": "暂无历史数据，使用默认创作策略",
    "good_features": [],
    "bad_features": [],
    "suggestions": []
  }
}
```
