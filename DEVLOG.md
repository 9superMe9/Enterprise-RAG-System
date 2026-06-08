# StarTech Enterprise RAG System - 开发日志

## V2.1 - 2026-06-03

### UI 全面重构：科技公司暗黑主题
- 暗黑渐变背景 `#0a0a1a` -> `#0d1117`，配合青色 `#00d4ff` 和紫色 `#7b2fff` 霓虹强调色
- 侧边栏玻璃拟态效果 + 毛玻璃背景
- 自定义滚动条（青色渐变滑块）
- 所有按钮渐变悬停动画 + 阴影光晕
- 聊天气泡圆角卡片 + 淡入动画
- 输入框霓虹聚焦光效
- 指标卡片悬停边框高亮
- 文件上传区虚线边框

### 模型路由 (Model Router)
- `config.py` 新增 `MODEL_ROUTES` 配置项（JSON 格式）
- `.env` 中可配置多模型：`MODEL_ROUTES='{"DeepSeek-V3":"deepseek-chat","DeepSeek-R1":"deepseek-reasoner"}'`
- 侧边栏 MODEL ROUTER 下拉切换，无需重启
- `chain.py` 支持 `get_rag(model_name=...)` 动态创建 LLM 实例
- 全局模型缓存 `_rag_instances` dict，切换模型复用已创建的实例
- 主聊天区顶部显示当前激活模型标签

### 知识库信息展示优化
- 隐藏 LLM 模型名称（用户不关心技术细节）
- 展示：**文档数量** + **知识块数量** 双指标卡片
- **INDEXED FILES** 区域：逐文件列出，每个文件显示 chunk 数徽章
- 按文件名排序，自动去重（相同文件名合并统计）
- 空库时显示友好提示 "No documents indexed yet."

### 文件上传优化
- 上传处理成功后自动清空文件选择器（通过 `uploader_key` 自增 + `st.rerun()`）
- Toast 通知替代页面内 success/info 消息
- 去重逻辑：重复文件不重复入库，显示 "Documents already exist"

### 其他改进
- 顶部标题栏霓虹渐变文字效果
- 检索中动画脉冲指示器
- `chain.py` 重构：`get_rag()` 支持模型参数，模型级缓存
- `config.py` 新增 `get_model_options()` 方法解析 JSON 路由
- 全部 `print()` 替换为 `logger`

---

## V2.0 - 2026-06-03

### 项目重构：修复致命缺陷

#### 嵌入模型统一
- `ingest.py` 和 `chain.py` 统一使用 `HuggingFaceEmbeddings(shibing624/text2vec-base-chinese)`
- 之前 ingest 用 OllamaEmbeddings 而 chain 用 HuggingFaceEmbeddings，导致向量空间不一致
- 现在入库和检索共享同一嵌入模型，确保检索正常

#### 消除模块级副作用
- `ingest.py` 移除 import 时执行的 `chromadb.PersistentClient(...)` 连接
- 改为懒加载，仅在函数调用时创建连接

#### web.py 复用核心模块
- 不再独立实现 RAG 逻辑
- 统一调用 `chain.py` 的 `get_rag()` 和 `config.py` 的 `settings`

#### 新增 FastAPI REST API (`api.py`)
| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查（向量库/LLM 状态） |
| `/chat` | POST | 知识库智能问答 |
| `/documents` | GET | 列出所有文档及统计 |
| `/documents/upload` | POST | 上传文档入库 |
| `/documents/{source}` | DELETE | 删除指定文档来源 |

#### 新增日志系统 (`logger.py`)
- 控制台 + 文件双输出
- 日志文件：`logs/app.log`
- 统一日志格式，替换全项目 `print()`

#### 其他
- 删除空文件 `model.py`（0 bytes）
- 新增 8 个单元测试 (`tests/test_ingest.py`)
- `requirements.txt` 精简为核心依赖
- `.gitignore` 新增 `logs/` 规则
- LangChain 1.2+ API 适配（LCEL 替代 RetrievalQA）
- 所有入口文件添加 `sys.path` 修正

---

## 启动方式

```bash
# Web 界面（推荐）
streamlit run app/web.py

# REST API
python -m app.api

# 命令行
python -m app.main

# 测试
python -m pytest tests/ -v
```

