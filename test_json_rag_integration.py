#!/usr/bin/env python3
"""
测试类：将PageIndex生成的JSON索引文件与大模型集成

本测试类演示如何使用PageIndex生成的JSON索引文件作为知识库，
与大模型集成实现基于文档结构的智能问答。
"""

import json
import os
from pageindex.utils import llm_completion

class JsonRagIntegrationTester:
    """测试JSON索引文件与大模型集成"""
    
    def __init__(self, json_paths, model=None):
        """初始化测试类
        
        Args:
            json_paths: 生成的JSON索引文件路径列表
            model: 要使用的LLM模型
        """
        # 支持单个文件路径或多个文件路径列表
        if isinstance(json_paths, str):
            self.json_paths = [json_paths]
        else:
            self.json_paths = json_paths
        self.model = model or "gpt-4o"
        self.index_data_list = self._load_json_files()
    
    def _load_json_files(self):
        """加载多个JSON索引文件"""
        index_data_list = []
        for json_path in self.json_paths:
            if not os.path.exists(json_path):
                raise FileNotFoundError(f"JSON索引文件不存在: {json_path}")
            
            with open(json_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
                index_data_list.append(index_data)
        return index_data_list
    
    def get_document_info(self):
        """获取所有文档基本信息"""
        info_list = []
        for i, index_data in enumerate(self.index_data_list):
            info_list.append({
                "文档序号": i+1,
                "文档名称": index_data.get('doc_name'),
                "文档描述": index_data.get('doc_description'),
                "章节数量": len(index_data.get('structure', []))
            })
        return info_list
    
    def select_relevant_documents(self, question):
        """选择最相关的文档
        
        Args:
            question: 用户问题
        
        Returns:
            选中文档的索引列表
        """
        # 为每个文档计算相关性得分
        doc_scores = []
        for i, index_data in enumerate(self.index_data_list):
            score = 0
            doc_name = index_data.get('doc_name', '').lower()
            doc_desc = index_data.get('doc_description', '').lower()
            question_text = question.lower()
            
            # 文档名称匹配
            for word in question_text.split():
                if word in doc_name:
                    score += 3
            
            # 文档描述匹配
            for word in question_text.split():
                if word in doc_desc:
                    score += 2
            
            doc_scores.append((i, score))
        
        # 按得分排序，选择得分大于0的文档
        doc_scores.sort(key=lambda x: x[1], reverse=True)
        selected_docs = [i for i, score in doc_scores if score > 0]
        
        # 如果没有得分大于0的文档，选择所有文档
        if not selected_docs:
            selected_docs = list(range(len(self.index_data_list)))
        
        return selected_docs[:3]  # 最多选择3个文档
    
    def search_relevant_chapters(self, question):
        """搜索与问题相关的章节
        
        Args:
            question: 用户问题
        
        Returns:
            相关章节列表
        """
        # 选择相关文档
        selected_doc_indices = self.select_relevant_documents(question)
        print(f"选择的文档: {[i+1 for i in selected_doc_indices]}")
        
        results = []
        
        def search_nodes(nodes, path=[], doc_name=""):
            for node in nodes:
                current_path = path + [node.get('title')]
                
                # 综合评分
                score = 0
                
                # 标题匹配得分
                title = node.get('title', '').lower()
                question_text = question.lower()
                
                # 精确匹配
                for word in question_text.split():
                    if word in title:
                        score += 3  # 标题匹配权重较高
                
                # 摘要匹配得分
                summary = node.get('summary', '').lower()
                for word in question_text.split():
                    if word in summary:
                        score += 2  # 摘要匹配权重次之
                
                # 路径匹配得分
                path_text = ' '.join(current_path).lower()
                for word in question_text.split():
                    if word in path_text:
                        score += 1  # 路径匹配权重较低
                
                # 只有得分大于0的才加入结果
                if score > 0:
                    results.append({
                        'doc_name': doc_name,
                        'path': ' > '.join(current_path),
                        'page_range': f"{node.get('start_index')}-{node.get('end_index')}",
                        'summary': node.get('summary', ''),
                        'relevance': score
                    })
                
                # 递归搜索子节点
                if 'nodes' in node and node['nodes']:
                    search_nodes(node['nodes'], current_path, doc_name)
        
        # 搜索选中文档
        for doc_index in selected_doc_indices:
            index_data = self.index_data_list[doc_index]
            doc_name = index_data.get('doc_name', f"文档{doc_index+1}")
            search_nodes(index_data.get('structure', []), doc_name=doc_name)
        
        # 按相关性排序，取前10个结果
        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results[:10]
    
    def build_context(self, relevant_chapters):
        """构建大模型上下文
        
        Args:
            relevant_chapters: 相关章节列表
        
        Returns:
            构建好的上下文字符串
        """
        # 只使用前5个最相关的章节
        top_chapters = relevant_chapters[:5]
        
        # 构建文档列表信息
        context = "=== 文档列表 ===\n"
        unique_docs = set()
        for chapter in top_chapters:
            unique_docs.add(chapter['doc_name'])
        
        for doc_name in unique_docs:
            context += f"- {doc_name}\n"
        context += "\n"
        
        # 构建相关章节信息
        context += "=== 相关章节信息 ===\n"
        for i, chapter in enumerate(top_chapters):
            context += f"{i+1}. 文档: {chapter['doc_name']}\n"
            context += f"   章节: {chapter['path']}\n"
            context += f"   页码: {chapter['page_range']}\n"
            context += f"   内容: {chapter['summary']}\n\n"
        
        return context
    
    def generate_answer(self, question):
        """使用大模型生成基于JSON索引的回答
        
        Args:
            question: 用户问题
        
        Returns:
            大模型生成的回答
        """
        # 搜索相关章节
        relevant_chapters = self.search_relevant_chapters(question)
        
        # 构建上下文
        context = self.build_context(relevant_chapters)
        
        # 构建更有效的提示词
        prompt = f"""你是一个专业的文档问答助手，精通信息检索和分析。
请仔细阅读以下文档信息，然后回答用户问题。

{context}

用户问题: {question}

回答要求:
1. 直接基于文档内容回答，不要添加文档中没有的信息
2. 优先使用与问题最相关的章节内容
3. 引用相关章节的来源（文档名称和章节名称）
4. 回答要简洁明了，重点突出
5. 如果文档中没有相关信息，请明确说明

请开始回答:
"""
        
        # 打印给AI的数据
        print("\n给AI的提示词:")
        print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
        print("-" * 60)
        
        # 调用大模型
        try:
            answer, tokens = llm_completion(model=self.model, prompt=prompt, return_tokens=True)
            
            # 打印token消耗
            print(f"\nToken消耗:")
            print(f"  提示词Token: {tokens['prompt_tokens']}")
            print(f"  回答Token: {tokens['completion_tokens']}")
            print(f"  总Token: {tokens['total_tokens']}")
            print("-" * 60)
            
            # 写入文件
            self._write_to_file(question, prompt, answer, tokens)
            
            return answer
        except Exception as e:
            error_msg = f"生成回答时出错: {str(e)}"
            print(error_msg)
            return error_msg
    
    def _write_to_file(self, question, prompt, answer, tokens):
        """将问答数据写入文件
        
        Args:
            question: 用户问题
            prompt: 给AI的提示词
            answer: AI的回答
            tokens: token消耗信息
        """
        import os
        import json
        from datetime import datetime
        
        # 创建输出目录
        output_dir = "ai_outputs"
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(output_dir, f"qa_{timestamp}.json")
        
        # 构建数据
        data = {
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "prompt": prompt,
            "answer": answer,
            "tokens": tokens,
            "model": self.model,
            "documents": [index_data.get('doc_name') for index_data in self.index_data_list]
        }
        
        # 写入文件
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n数据已写入文件: {filename}")
    
    def run_integration_test(self, test_questions):
        """运行集成测试
        
        Args:
            test_questions: 测试问题列表
        """
        print(f"=== JSON索引文件与大模型集成测试 ===")
        print(f"测试文档数量: {len(self.index_data_list)}")
        print(f"使用模型: {self.model}")
        print("=" * 80)
        
        # 打印文档列表
        print("\n=== 测试文档列表 ===")
        for i, index_data in enumerate(self.index_data_list):
            print(f"文档{i+1}: {index_data.get('doc_name', f'文档{i+1}')}")
        print("=" * 80)
        
        for i, question in enumerate(test_questions):
            print(f"\n测试问题 {i+1}: {question}")
            print("-" * 60)
            
            # 搜索相关章节
            relevant_chapters = self.search_relevant_chapters(question)
            print(f"找到 {len(relevant_chapters)} 个相关章节")
            
            # 显示相关章节
            for j, chapter in enumerate(relevant_chapters):
                print(f"  {j+1}. [{chapter['doc_name']}] {chapter['path']} (第{chapter['page_range']}页)")
            
            # 生成回答
            answer = self.generate_answer(question)
            print("\n大模型回答:")
            print(answer)
            print("-" * 60)

def main():
    """主函数"""
    # 替换为您生成的JSON索引文件路径列表
    json_paths = [
        ""
    ]
    
    # 选择模型（可以使用国产AI模型）
    # model = "dashscope/qwen-turbo"  # 阿里通义千问
    # model = "baidu/ERNIE-Bot-4"    # 百度文心一言
    # model = "tencent/hunyuan-pro"  # 腾讯混元大模型
    model = "dashscope/qwen-max"  # OpenAI模型
    
    try:
        tester = JsonRagIntegrationTester(json_paths, model=model)
        
        # 打印文档信息
        doc_info_list = tester.get_document_info()
        print("文档信息:")
        for info in doc_info_list:
            print(f"文档{info['文档序号']}:")
            print(f"  名称: {info['文档名称']}")
            print(f"  描述: {info['文档描述']}")
            print(f"  章节数: {info['章节数量']}")
            print()
        print()
        
        # 测试问题
        test_questions = [
            ""
        ]
        
        # 运行集成测试
        tester.run_integration_test(test_questions)
        
    except Exception as e:
        print(f"测试过程中出错: {str(e)}")

if __name__ == "__main__":
    main()
