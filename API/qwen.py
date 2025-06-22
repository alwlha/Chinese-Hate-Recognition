import os
import json
import time
from openai import OpenAI

# 配置API密钥，如果环境变量未设置，可以直接在这里设置
API_KEY = "sk-2fc8d5dfcd96417e97f5d9b7ef6d309d" # 替换为你的API密钥

# 创建OpenAI客户端
client = OpenAI(
    api_key=API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

def process_item(item):
    """
    处理单个数据项
    item: 包含id和content的字典
    """
    try:
        # 构建提示词
        prompt = "请对以下社交媒体文本进行细粒度的仇恨言论分析：\n1. 识别评论对象(Target)和论点(Argument)\n2. 判断目标群体(Targeted Group)和是否仇恨(Hateful)\n3. 严格遵守输出格式：Target | Argument | Targeted Group | Hateful [END]\n4. 多个结果用[SEP]分隔：Target | Argument | Targeted Group | Hateful [SEP] Target | Argument | Targeted Group | Hateful [END]\n5. 目标群体选项：地域、种族、性别、LGBTQ、其他、non-hate\n6. 是否仇恨选项：hate、non-hate"
        
        # 发送请求
        completion = client.chat.completions.create(
            model="qwen-plus",  # 使用通义千问模型
            messages=[
                {'role': 'system', 'content': '你是一个专业的仇恨言论分析助手，请严格按照格式要求输出分析结果。'},
                {'role': 'user', 'content': f"{prompt}\n\n文本：{item['content']}，请直接输出分析结果，且只能输出格式化的结果，不需要其他多余的话。"}
            ]
        )
        
        return completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"处理数据时出错: {str(e)}")
        return None

def get_processed_ids(results_file):
    """获取已经处理过的数据ID列表"""
    if os.path.exists(results_file):
        with open(results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
            return {item['id'] for item in results}
    return set()

if __name__ == "__main__":
    # 读取包含数据的JSON文件
    with open('test1.json', 'r', encoding='utf-8') as file:
        data_list = json.load(file)

    # 创建结果文件
    results_file = 'qwen.json'
    if os.path.exists(results_file):
        with open(results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
    else:
        results = []

    # 获取已处理的数据ID
    processed_ids = get_processed_ids(results_file)
    print(f"已处理数据数量: {len(processed_ids)}")
    print(f"总数据数量: {len(data_list)}")

    # 处理每个数据项
    for i, item in enumerate(data_list):
        # 如果已经处理过，跳过
        if item['id'] in processed_ids:
            print(f"跳过已处理的数据 ID: {item['id']}")
            continue

        print(f"处理第 {i+1}/{len(data_list)} 条数据...")
        
        try:
            # 获取分析结果
            analysis_result = process_item(item)
            
            # 打印结果
            print(f"ID: {item['id']}")
            print(f"内容: {item['content']}")
            print(f"分析结果: {analysis_result}")
            print("-" * 50)
            
            # 创建结果对象
            result = {
                "id": item["id"],
                "content": item["content"],
                "analysis": analysis_result,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 添加到结果列表
            results.append(result)
            
            # 实时写入文件
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            print(f"结果已实时写入到 {results_file}")
            
            # API速率限制
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("\n检测到中断信号，正在保存当前进度...")
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print("进度已保存，程序退出")
            break
        except Exception as e:
            print(f"处理数据时发生错误: {str(e)}")
            print("继续处理下一条数据...")
            continue

    print("处理完成！所有结果已保存到", results_file)
