#!/usr/bin/env python3
"""
示例：使用国产AI模型进行文档索引

本示例展示如何使用国产AI模型（如百度文心一言、阿里通义千问、腾讯混元大模型）进行文档索引。
"""

import os
from pageindex.client import PageIndexClient

# 设置API密钥
# 请根据您使用的国产AI模型选择相应的API密钥环境变量

# 示例1: 使用百度文心一言
# os.environ["BAIDU_API_KEY"] = "您的百度API_KEY"
# os.environ["BAIDU_SECRET_KEY"] = "您的百度SECRET_KEY"

# 示例2: 使用阿里通义千问
# os.environ["ALI_API_KEY"] = "您的阿里API_KEY"

# 示例3: 使用腾讯混元大模型
# os.environ["TENCENT_API_KEY"] = "您的腾讯API_KEY"

# 示例4: 使用智谱AI
# os.environ["ZHIPUAI_API_KEY"] = "您的智谱AI API_KEY"

def main():
    # 选择要使用的国产AI模型
    # 百度文心一言
    # model = "baidu/ERNIE-Bot-4"
    
    # 阿里通义千问
    # model = "dashscope/qwen-turbo"
    
    # 或使用其他阿里模型变体
    # model = "dashscope/qwen-plus"
    
    # 腾讯混元大模型
    # model = "tencent/hunyuan-pro"
    
    # 智谱AI
    # model = "zhipu/chatglm3"
    
    # 为了演示，我们仍然使用OpenAI模型
    # 请取消上面的注释并设置相应的API密钥来使用国产AI模型
    model = "gpt-4o"
    
    # 创建PageIndexClient实例
    client = PageIndexClient(
        model=model,
        workspace="./workspace"
    )
    
    # 索引示例文档
    print("正在索引示例文档...")
    doc_id = client.index("./examples/documents/2023-annual-report-truncated.pdf")
    print(f"文档索引完成，文档ID: {doc_id}")
    
    # 获取文档结构
    print("\n获取文档结构...")
    structure = client.get_document_structure(doc_id)
    print(structure)
    
    # 获取文档内容
    print("\n获取文档首页内容...")
    page_content = client.get_page_content(doc_id, "1")
    print(page_content)

if __name__ == "__main__":
    main()
