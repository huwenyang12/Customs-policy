import json
import logging
from customs_policy_client import CustomsPolicyClient

# 初始化客户端
obj = CustomsPolicyClient(token="9591bca2739d476ea4ef77ce3df5908d")

# 读取海关法规数据
file_name = "财政部.json"
# file_name = "海关法规.json"
json_file_path = rf"D:\海关接口\海关_附件1\output\data\{file_name}"

def read_file(path=json_file_path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            customs_data = json.load(f)
        print(f"成功读取JSON文件，共 {len(customs_data)} 条政策数据")
        return customs_data
    except Exception as e:
        print(f"错误：读取文件时发生未知错误 - {str(e)}")

def process_customs_policies(data_list):
    """
    处理海关政策数据，逐一推送到接口
    """
    success_count = 0
    failed_count = 0
    ckip_count = 0
    created_ids = []  # 用于存储成功创建的政策ID
    
    for i, policy in enumerate(data_list):
        print(f"\n=== 处理第 {i+1}/{len(data_list)} 条政策 ===")
        print(f"政策标题: {policy['政策标题']}")
        
        # 获取唯一标识ID
        policy_id = policy["唯一ID"]
        
        # 检查政策是否已存在
        if obj.checkout_policy_exists(policy_id):
            print(f"该政策已存在，policyId: {policy_id}，跳过创建")
            ckip_count += 1
            continue
        
        try:
            # 获取发文时间和生效日期，转为毫秒字符串
            releaseDate_str = policy["发布时间"]
            effectiveDate_str = policy["生效日期"]
            release_ts = obj.timestamp_ms_str(releaseDate_str)
            effective_ts = obj.timestamp_ms_str(effectiveDate_str)
            
            # 获取压缩包路径并上传文件
            zip_path = policy["zip包路径"]
            print(f"正在上传文件: {zip_path}")
            attachment_url = obj.upload_file(zip_path)
            
            if not attachment_url:
                print("文件上传失败，跳过该政策")
                failed_count += 1
                continue
            
            # 提取各字段数据
            title = policy["政策标题"]
            issuing_agency = policy["发文机关"]
            url = policy["详情页链接"]
            document_number = policy["发布文号"]
            validity_status = policy["是否有效"]
            attachment_count = str(policy["zip包文件数量"])
            
            # 构建政策数据
            policy_data = {
                "articleTitle": title,
                "documentIssuingAgency": issuing_agency,
                "articleUrl": url,
                "releaseDate": release_ts,              # 发布时间，时间戳（毫秒）
                "effectiveDate": effective_ts,          # 生效时间，时间戳（毫秒）
                "issueNum": document_number,            # 文号
                "efficacy": validity_status,            # 有效/已废止
                "attachment": attachment_count,         # 附件数量
                "attachmentUrl": attachment_url,        # 压缩包下载链接
                "policyId": policy_id                   # 唯一 ID
            }
            
            print(f"文件上传成功，开始创建政策...")
            
            # 创建政策，获取返回的 ID
            created_id = obj.create_policy(policy_data)
            
            if created_id:
                print(f"创建成功，ID: {created_id}")
                created_ids.append(created_id)  # 将成功的ID添加到列表
                success_count += 1
            else:
                print("创建失败，尝试回滚删除该政策...")
                deleted = obj.delete_policy(created_id)
                if deleted:
                    print("创建失败已自动删除")
                else:
                    print("创建失败但删除失败，请手动处理")
                failed_count += 1
                
        except Exception as e:
            print(f"处理政策时发生错误: {str(e)}")
            failed_count += 1
    
    print(f"\n=== 处理完成 ===")
    print(f"成功: {success_count} 条")
    print(f"失败: {failed_count} 条")
    print(f"跳过: {ckip_count} 条")
    print(f"总计: {len(data_list)} 条")
    
    # 打印成功创建的所有 policy_id
    if success_count > 0:
        # 记录成功创建的政策 ID 到日志文件
        logging.info(f"成功创建的政策ID列表：")
        logging.info(f"{created_ids}\n")

# 执行处理
if __name__ == "__main__":
    customs_data = read_file()
    process_customs_policies(customs_data)
