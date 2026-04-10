#!/usr/bin/env python3
"""
批量处理文件夹下的所有文件，使用PageIndex生成JSON索引文件
"""

import os
import sys
import subprocess

def batch_process_folder(folder_path, model=None):
    """批量处理文件夹下的所有文件
    
    Args:
        folder_path: 要处理的文件夹路径
        model: 要使用的模型
    """
    # 检查文件夹是否存在
    if not os.path.exists(folder_path):
        print(f"错误：文件夹不存在: {folder_path}")
        return
    
    # 获取文件夹下的所有文件
    files = []
    for root, _, filenames in os.walk(folder_path):
        for filename in filenames:
            if filename.lower().endswith(('.pdf', '.md', '.markdown')):
                files.append(os.path.join(root, filename))
    
    if not files:
        print(f"文件夹中没有找到PDF或Markdown文件: {folder_path}")
        return
    
    print(f"找到 {len(files)} 个文件待处理:")
    for file in files:
        print(f"  - {os.path.basename(file)}")
    
    # 处理每个文件
    for file in files:
        print(f"\n处理文件: {os.path.basename(file)}")
        try:
            # 构建命令
            cmd = ["python", "run_pageindex.py"]
            
            # 确定文件类型
            if file.lower().endswith(('.pdf')):
                cmd.extend(["--pdf_path", file])
            else:
                cmd.extend(["--md_path", file])
            
            # 添加模型参数
            if model:
                cmd.extend(["--model", model])
            
            # 执行命令
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # 检查执行结果
            if result.returncode == 0:
                print(f"  成功处理: {os.path.basename(file)}")
            else:
                print(f"  处理失败: {os.path.basename(file)}")
                print(f"  错误信息: {result.stderr}")
                
        except Exception as e:
            print(f"  处理出错: {os.path.basename(file)}")
            print(f"  错误信息: {str(e)}")

if __name__ == "__main__":
    # 解析命令行参数
    import argparse
    
    parser = argparse.ArgumentParser(description="批量处理文件夹下的所有文件")
    parser.add_argument("--folder", type=str, required=True, help="要处理的文件夹路径")
    parser.add_argument("--model", type=str, default=None, help="要使用的模型")
    
    args = parser.parse_args()
    
    # 执行批量处理
    batch_process_folder(args.folder, args.model)