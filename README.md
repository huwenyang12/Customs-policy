# 海关政策采集流程



## 1. 流程简介

本流程用于定期采集多个政府网站公开发布的政策信息，对政策正文和附件进行统一整理，并将结构化政策数据及附件包同步到业务系统。

---

## 2. 整体处理流程

```mermaid
flowchart LR
    A["政府政策网站"] --> B["读取政策列表"]
    B --> C["与历史记录去重"]
    C --> D["进入政策详情页"]
    D --> E["提取政策字段"]
    D --> F["保存正文与附件"]
    E --> G["生成 JSON 和 Excel"]
    F --> H["生成 ZIP 附件包"]
    G --> I["按政策唯一 ID 查重"]
    H --> J["上传 ZIP 附件包"]
    I --> K["创建业务系统政策记录"]
    J --> K
    K --> L["输出执行结果与日志"]
```

整个程序可以分成四个阶段：

1. **政策采集**：访问各政府网站，读取最新政策列表和详情页。
2. **内容整理**：提取统一字段，保存正文页面并下载政策附件。
3. **结果落盘**：生成 JSON、Excel 和 ZIP 文件，作为本地采集成果。
4. **系统同步**：对业务系统进行查重，上传附件包并创建政策记录。

### 流程入口

代码位置：`app.py` → `main()`

```python
async def main():
    await run_hgfg_spider()   # 海关法规
    await run_zcjd_spider()   # 政策解读
    await run_czb_spider()    # 财政部
    await run_sww_spider()    # 商务委/商务部
    await run_gxb_spider()    # 工信部
    await run_yjj_spider()    # 药监局

if __name__ == "__main__":
    asyncio.run(main())
    run_interface()
```

前六步负责采集不同来源的政策，最后一步负责把采集结果同步到业务系统。

---

## 3. 政策数据来源

系统当前接入六类政策来源：

| 来源 | 程序模块 | 本地数据文件 | 默认采集页数 |
| :-: | :-: | :-: | :--: |
| 海关法规 | `spider/hgfg_spider.py` | `海关法规.json` | 5 |
| 海关政策解读 | `spider/zcjd_spider.py` | `政策解读.json` | 5 |
| 财政部 | `spider/czb_spider.py` | `财政部.json` | 5 |
| 商务委 | `spider/sww_spider.py` | `商务委.json` | 1 |
| 工信部 | `spider/gxb_spider.py` | `工信部.json` | 1 |
| 药监局 | `spider/yjj_spider.py` | `药监局.json` | 5 |

各网站的网页结构不同，因此每个来源有独立的采集模块；采集完成后，所有来源都会转换成相同的数据结构，再进入统一的同步流程。

采集页数集中配置在 `config.py` 中，可以根据业务范围进行调整。

---

## 4. 单条政策处理步骤

### 4.1 读取政策列表

程序首先打开政策发布网站，根据配置依次读取前若干页政策列表，获得政策标题、发布时间和详情页链接。

### 4.2 去重

程序启动时会读取本地已有的 JSON 数据，并使用以下组合判断一条政策是否已经采集：

```text
发布时间 + 政策标题
```

如果组合已经存在，程序会跳过该政策；如果不存在，才会进入详情页继续处理。因此日常运行主要采集新增政策，不需要每次重新处理全部历史数据。

```python
# 读取已有数据组合key
with open(json_path, "r", encoding="utf-8") as f:
    existing_data = json.load(f)
existing_keys = set((item["发布时间"], item["政策标题"])for item in existing_data)
# 判断爬取数据是否重复
if (fbsj, title) in existing_keys:
    continue
```

### 4.3 进入详情页并提取字段

对于没有采集过的政策，程序会进入详情页，根据该网站的页面结构提取正文信息和附件地址。

不同网站的选择器不同，但最终会整理成统一字段：

| 字段 | 说明 |
| --- | --- |
| 政策标题 | 政策或公告名称 |
| 发文机关 | 政策发布部门 |
| 详情页链接 | 政策原始网页地址，便于追溯 |
| 发布时间 | 政策发布日期 |
| 生效日期 | 页面能够取得时使用实际日期 |
| 发布文号 | 页面能够取得时提取文号 |
| 是否有效 | 提供给业务系统的效力状态 |
| 附件列表 | 从详情页发现的附件名称 |
| ZIP 包文件数量 | ZIP 中正文和附件的总数量 |
| ZIP 包路径 | 本地附件包位置 |
| 唯一 ID | 用于业务系统查重的政策标识 |

```python
record = {
    "政策标题": title,
    "发文机关": fwjg,
    "详情页链接": href,
    "发布时间": fbsj,
    "生效日期": sxrq,
    "发布文号": fbwh,
    "是否有效": efficacy,
    "zip包文件数量": zip_file_count,
    "zip包路径": zip_path,
    "附件列表": href_names,
    "唯一ID": policy_id,
}
```

这段 `record` 代表一条完整政策，也是后面生成 JSON、Excel 和同步业务系统的共同数据来源。

### 4.4 保存正文和附件

为了尽可能完整地保留政策发布时的页面内容，程序会：

1. 对政策详情页进行全页面截图；
2. 将页面截图转换为 PDF；
3. 下载详情页中识别到的附件；
4. 将 PDF、页面图片和原始附件统一压缩成 ZIP 包；
5. ZIP 创建成功后清理中间临时文件。

---

## 5. 本地输出结果

所有采集结果保存在 `output` 目录下：

```text
output/
├─ data/                         各来源的 JSON 数据
│  ├─ 海关法规.json
│  ├─ 政策解读.json
│  ├─ 财政部.json
│  ├─ 商务委.json
│  ├─ 工信部.json
│  └─ 药监局.json
├─ downloads/                    正文、附件包和 Excel
│  ├─ hgfg/                      海关法规
│  ├─ zcjd/                      政策解读
│  ├─ czb/                       财政部
│  ├─ sww/                       商务委
│  ├─ gxb/                       工信部
│  └─ yjj/                       药监局
└─ logs/
   └─ all.log                    采集过程日志
```

### 数据累加保存

```python
all_records = existing_data + new_records

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(all_records, f, ensure_ascii=False, indent=4)

df_all = pd.DataFrame(all_records)
df_all.to_excel(excel_path, index=False)
```

```text
最终数据 = 已有历史数据 + 本次新增数据
```

例如原来有 50 条，本次新增 3 条，保存后就是 53 条。程序不会因为网站上的旧政策下架而自动删除本地历史记录。

---

## 6. 同步到业务系统

全部来源采集完成后，程序进入统一的接口处理阶段。

### 6.1 获取访问凭证

程序通过已配置的业务系统账号完成登录，并取得本次同步所需的访问凭证。

### 6.2 按唯一 ID 查重

同步每条政策之前，程序先使用政策唯一 ID 查询业务系统：

- 已存在：跳过，不重复创建；
- 未查询到已存在记录：继续上传附件并创建政策；
- 接口调用过程中的异常会写入日志，便于后续排查。

采集阶段通过“发布时间 + 标题”避免重复下载，同步阶段通过“唯一 ID”避免业务系统重复创建。

### 6.3 上传附件并创建政策

对于需要新增的政策，程序先上传本地 ZIP 包，取得附件地址，然后将标准字段映射为业务系统字段并创建政策记录。

主要映射关系如下：

| 本地字段 | 业务系统字段 | 含义 |
| --- | --- | --- |
| 政策标题 | `articleTitle` | 政策标题 |
| 发文机关 | `documentIssuingAgency` | 发文单位 |
| 详情页链接 | `articleUrl` | 原文地址 |
| 发布时间 | `releaseDate` | 发布时间 |
| 生效日期 | `effectiveDate` | 生效时间 |
| 发布文号 | `issueNum` | 政策文号 |
| 是否有效 | `efficacy` | 效力状态 |
| ZIP 包文件数量 | `attachment` | 附件数量 |
| ZIP 上传地址 | `attachmentUrl` | 附件包地址 |
| 唯一 ID | `policyId` | 查重标识 |

核心代码位置：`Interface/run.py` → `process_customs_policies()`

```python
# 1. 按唯一 ID 查询，已存在的政策直接跳过
if obj.checkout_policy_exists(policy_id):
    result["skipped"].append(policy_id)
    continue

# 2. 上传本地 ZIP 包，取得业务系统可访问的附件地址
zip_path = policy["zip包路径"]
attachment_url = obj.upload_file(zip_path)
if not attachment_url:
    result["failed"].append(policy_id)
    continue

# 3. 将本地字段转换成业务系统字段
policy_data = {
    "articleTitle": policy["政策标题"],
    "documentIssuingAgency": policy["发文机关"],
    "articleUrl": policy["详情页链接"],
    "releaseDate": release_ts,
    "effectiveDate": effective_ts,
    "issueNum": policy["发布文号"],
    "efficacy": policy["是否有效"],
    "attachment": str(policy["zip包文件数量"]),
    "attachmentUrl": attachment_url,
    "policyId": policy_id,
}

# 4. 调用接口创建政策
created_id = obj.create_policy(policy_data)
```

完整顺序：**业务系统查重 → 上传 ZIP → 字段转换 → 创建政策**。如果附件上传失败，当前政策会被记录为失败并跳过，不会继续创建一条没有附件地址的政策。

### 6.4 输出同步结果

程序最终按来源汇总以下信息：

- 成功创建数量；
- 已存在并跳过的数量；
- 处理失败的数量；
- 成功记录 ID；
- 失败政策 ID。

这些信息会输出到控制台和日志中，方便核对本次任务是否完整执行。

---

## 7. 程序入口与模块职责

| 文件或目录 | 职责 |
| --- | --- |
| `app.py` | 主入口，依次执行六个爬虫，然后启动业务系统同步 |
| `config.py` | 输出目录和各来源最大采集页数配置 |
| `spider/` | 六个网站的政策采集与内容整理逻辑 |
| `utils/file_utils.py` | 文件名清洗和附件下载 |
| `utils/page_utils.py` | 部分网站的页面字段提取辅助方法 |
| `logger.py` | 统一采集日志 |
| `Interface/run.py` | 读取 JSON、查重、上传和创建政策的批处理流程 |
| `Interface/customs_policy_client.py` | 封装业务系统查重、上传、创建和删除接口 |
| `Interface/get_token_cookie.py` | 登录业务系统并取得访问凭证 |

主流程中六个来源按以下顺序执行：

```text
海关法规
→ 政策解读
→ 财政部
→ 商务委
→ 工信部
→ 药监局
→ 业务系统同步
```

---

## 8. 运行方式

### 8.1 环境要求

- Windows 运行环境；
- Python 3；
- 可正常访问目标政策网站和业务系统；
- 已安装项目依赖及 Playwright 浏览器组件；
- 已由部署人员完成业务系统账号等运行配置。

### 8.2 启动完整流程

在项目根目录执行：

```powershell
python app.py
```

程序会自动完成政策采集、文件整理、本地保存和业务系统同步。
