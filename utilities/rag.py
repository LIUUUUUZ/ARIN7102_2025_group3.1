import torch
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import json
import os

class RAG:
    def __init__(self, index_path, qa_file_path, model_name="paraphrase-MiniLM-L6-v2", top_k=5, min_similarity=0.75):
        """
        初始化RAG检索系统
        
        参数:
            index_path: FAISS索引文件路径
            qa_file_path: 问答对JSON文件路径
            model_name: 使用的句子嵌入模型名称
            top_k: 返回的最相关结果数量
            min_similarity: 最小相似度阈值，低于此值的结果将被过滤
        """
        # 设置设备（GPU或CPU）
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        # 加载句子嵌入模型
        self.model = SentenceTransformer(model_name).to(self.device)
        self.qa_file_path = qa_file_path
        # 加载问答数据
        self.qa_pairs = self.load_qa_data(qa_file_path)
        # 设置默认参数
        self.top_k = top_k
        self.min_similarity = min_similarity
        
        # 检查索引文件是否存在，不存在则重新训练
        if os.path.exists(index_path):
            self.index = self.load_faiss_index(index_path)
        else:
            print(f"索引文件 {index_path} 不存在，正在重新训练...")
            # 编码所有问题
            questions = [item["question"] for item in self.qa_pairs]
            question_embeddings = self.generate_embeddings(questions)
            
            # 构建并保存索引
            self.index = self.build_faiss_index(question_embeddings)
            faiss.write_index(self.index, index_path)
            print(f"索引已保存到 {index_path}")

    def load_qa_data(self, file_path):
        """
        从JSON文件加载结构化问答对
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            qa_pairs = json.load(f)
        return qa_pairs

    def generate_embeddings(self, texts):
        """
        为文本列表生成嵌入向量
        """
        embeddings = self.model.encode(texts, convert_to_tensor=True, device=self.device)
        # 归一化向量
        embeddings = embeddings / torch.norm(embeddings, dim=1, keepdim=True)
        return embeddings.cpu().numpy()

    @staticmethod
    def build_faiss_index(embeddings):
        """
        构建FAISS索引用于高效相似度搜索
        """
        embedding_dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(embedding_dim)  # 内积等价于余弦相似度（归一化后）
        index.add(np.array(embeddings))
        return index

    @staticmethod
    def load_faiss_index(index_path):
        """
        加载预先构建的FAISS索引
        """
        return faiss.read_index(index_path)

    def rag_query(self, query, top_k=None, min_similarity=None):
        """
        Execute RAG query, returning the most relevant QA pairs for the query
        
        Parameters:
            query: User query text
            top_k: Number of most relevant results to return, uses default if None
            min_similarity: Minimum similarity threshold, uses default if None
            
        Returns:
            Formatted user_prompt string containing original query and retrieved results
        """
        # Use default values or passed parameters
        top_k = top_k if top_k is not None else self.top_k
        min_similarity = min_similarity if min_similarity is not None else self.min_similarity
        
        # Generate embedding vector for the query
        query_embedding = self.model.encode([query], convert_to_tensor=True, device=self.device)
        query_embedding = query_embedding / torch.norm(query_embedding, dim=1, keepdim=True)
        query_embedding = query_embedding.cpu().numpy()
        
        # Search for the most similar questions
        distances, indices = self.index.search(query_embedding, top_k)

        # Organize results
        results = []
        for i, idx in enumerate(indices[0]):
            similarity = float(distances[0][i])
            # Only add results with similarity above threshold
            if similarity >= min_similarity:
                results.append({
                    "question": self.qa_pairs[idx]["question"],
                    "answer": self.qa_pairs[idx]["answer"],
                    "similarity": similarity
                })

        # Construct user_prompt
        user_prompt = f"User query: {query}\n\nReference information:\n"
        for i, result in enumerate(results):
            user_prompt += f"Reference {i+1}:\n"
            user_prompt += f"Question: {result['question']}\n"
            user_prompt += f"Answer: {result['answer']}\n"
            user_prompt += f"Similarity: {result['similarity']:.4f}\n\n"
        
        # Add guidance text
        user_prompt += "Please answer the user's query based on the reference information above. If the reference is irrevalent to the query, please answer the query based on your knowledge."
        
        return user_prompt
    
    def retrieve_top_questions(self, query, top_k=None, min_similarity=None):
        """
        检索与查询最相似的问题，返回结构化结果
        
        参数:
            query: 用户查询文本
            top_k: 返回的最相关结果数量，如果为None则使用默认值
            min_similarity: 最小相似度阈值，如果为None则使用默认值
            
        返回:
            包含相似问题、答案和相似度分数的列表
        """
        # 使用默认值或传入的参数
        top_k = top_k if top_k is not None else self.top_k
        min_similarity = min_similarity if min_similarity is not None else self.min_similarity
        
        # 生成查询的嵌入向量
        query_embedding = self.model.encode([query], convert_to_tensor=True, device=self.device)
        query_embedding = query_embedding / torch.norm(query_embedding, dim=1, keepdim=True)
        query_embedding = query_embedding.cpu().numpy()
        
        # 搜索最相似的问题
        distances, indices = self.index.search(query_embedding, top_k)

        # 整理结果
        results = []
        for i, idx in enumerate(indices[0]):
            similarity = float(distances[0][i])
            # 只添加相似度高于阈值的结果
            if similarity >= min_similarity:
                results.append({
                    "question": self.qa_pairs[idx]["question"],
                    "answer": self.qa_pairs[idx]["answer"],
                    "similarity": similarity
                })
            
        return results
    





class NextQuestionGenerator:
    """
    基于用户查询和回答生成可能的后续问题
    """
    def __init__(self, api_key_file="api_keys.json", base_url="https://api.deepseek.com", model="deepseek-chat"):
        """
        初始化后续问题生成器
        
        参数:
            api_key_file: 存储API密钥的JSON文件路径
            base_url: API基础URL
            model: 使用的模型名称
        """
        self.base_url = base_url
        self.model = model
        self.client = None
        self.load_api_key(api_key_file)
        
    def load_api_key(self, api_key_file):
        """从JSON文件加载API密钥"""
        try:
            import json
            from openai import OpenAI
            
            with open(api_key_file, 'r', encoding='utf-8') as f:
                keys = json.load(f)
                api_key = keys.get("deepseek_api_key", "")
                
            self.client = OpenAI(
                api_key=api_key,
                base_url=self.base_url
            )
        except Exception as e:
            print(f"加载API密钥失败: {e}")
            self.client = None
    
    def generate_next_questions(self, question, answer, n=3):
        """
        生成用户可能的后续问题
        
        参数:
            question: 用户当前问题
            answer: 系统回答
            n: 生成的后续问题数量
            
        返回:
            可能的后续问题列表
        """
        if not self.client:
            return ["无法生成后续问题：API客户端未初始化"]
            
        user_prompt = f"""You are a helpful, empathetic, and knowledgeable health assistant.

        Your task is to thoughtfully analyze the following Q&A pair and creatively suggest {n} highly relevant and context-aware follow-up questions that the user might naturally ask next.

        Q: {question}
        A: {answer}

        Please provide exactly {n} follow-up questions in a numbered list format:

        1. 
        2. 
        3.
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful and knowledgeable health chatbot."},
                    {"role": "user", "content": user_prompt.strip()}
                ],
                temperature=0.7,
                max_tokens=128
            )
            raw = response.choices[0].message.content.strip()

            # 解析输出为问题列表
            predicted = []
            for line in raw.splitlines():
                line = line.strip()
                if line[:2] in ["1.", "2.", "3."]:
                    predicted.append(line[2:].strip(" .-"))
                elif line.startswith("- ") or line.startswith("* "):
                    predicted.append(line[2:].strip())
            return predicted if predicted else [raw]

        except Exception as e:
            print(f"API调用失败: {e}")
            return ["Error: Unable to generate next questions."]

