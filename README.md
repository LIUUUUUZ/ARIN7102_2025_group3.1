# ARIN7102_2025_group3.1
### 2025 第一学期 ARIN7102 的小组期末项目
1.后续的项目规划和分工会写在此readme file中.       
2.各位更新的话记得同步更新此readme file且在commit changes时写好comment便于其他组员查看进度。 
3.如果有问题以及建议请及时在微信群中反馈。       

#### 项目为: Online Health Science Knowledge Chatbot
#### 项目主要目标为: 设计一个可以以对话框形式提供健康知识的聊天机器人，并通过构建本地知识库以及RAG技术让机器人回答更有针对性。      
#### 项目模块分为:     
* 健康知识数据库     
* RAG组件    
* 聊天机器人组件     
* ui及其他功能

#### 使用的模型数据为:
~~[Amazon question/answer data/Health and Personal Care](https://mcauleylab.ucsd.edu/public_datasets/data/amazon/qa/icdm/QA_Health_and_Personal_Care.json.gz)~~       
最后选定的本地数据库为融合[Amazon question/answer data/Health and Personal Care](https://mcauleylab.ucsd.edu/public_datasets/data/amazon/qa/icdm/QA_Health_and_Personal_Care.json.gz)以及healthline数据再做筛选后的版本，详见[structured_qa.json](https://github.com/LIUUUUUZ/ARIN7102_2025_group3.1/blob/main/utilities/structured_qa.json)

#### 启动方法
1. 将代码clone到本地后，根据environment.yml安装所需要的环境
2. 根目录下创建traing_data文件夹，将训练好的数据集（qa_embeddnigs.index,structured_qa.json）放入其中。如果你是第一次运行的话，可以在根目录下在conda中启动python运行
```python
from from utilities.rag import RAG, NextQuestionGenerator

rag = RAG(index_path="traing_data/qa_embeddings.index", qa_file_path="traing_data/structured_qa.json", top_k=3, min_similarity=0.75)
```
上述代码将会自动下载并处理所需模型

3. 在根目录下运行
```python
streamlit run Homepage.py
```

#### 注意事项
1. 启动时由于会加载RAG，所以启动速度会很慢，大约2分钟
2. 运行chatbot时请等待完全输出后（包括suggestions）再切换页面,否则有可能会导致chatbot状态异常。