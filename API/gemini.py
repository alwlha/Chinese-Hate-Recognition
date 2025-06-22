import openai
import base64
import json
import os
import time

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def process_item(item, client):
    """
    处理单个数据项
    item: 包含id和content的字典
    """
    try:
        # 构建提示词
        prompt = "请对以下社交媒体文本进行细粒度的仇恨言论分析：\n1. 识别评论对象(Target)和论点(Argument)\n2. 判断目标群体(Targeted Group)和是否仇恨(Hateful)\n3. 严格遵守输出格式：Target | Argument | Targeted Group | Hateful [END]\n4. 多个结果用[SEP]分隔：Target | Argument | Targeted Group | Hateful [SEP] Target | Argument | Targeted Group | Hateful [END]\n5. 目标群体选项：地域、种族、性别、LGBTQ、其他、non-hate\n6. 是否仇恨选项：hate、non-hate"
        
        # 构建消息内容
        content = [
            {"type": "text", "text": f"{prompt}\n\n文本：{item['content']}，请直接输出分析结果，且只能输出格式化的结果，不需要其他多余的话。"}
        ]
        
        # 发送请求
        response = client.chat.completions.create(
            model="gemini-1.5-pro-002",
            messages=[
                {
                    "role": "user",
                    "content": content
                }
            ],
            max_tokens=300
        )
        
        return response.choices[0].message.content.strip()
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
    # 创建 OpenAI 客户端实例
    client = openai.OpenAI(
        api_key="sk-GnrOVKy7Hr8bK7na9aC11bC6F3B548A2A28978D89c5c3c79",
        base_url="https://api.bltcy.ai/v1"
    )

    # 读取包含数据的JSON文件
    with open('test1.json', 'r', encoding='utf-8') as file:
        data_list = json.load(file)

    # 创建结果文件
    results_file = 'gemini-1.5-pro.json'
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
            analysis_result = process_item(item, client)
            
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
