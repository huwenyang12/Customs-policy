import asyncio
import pandas as pd
import time
import os
import re
import json
import zipfile
from playwright.async_api import async_playwright
import img2pdf
from urllib.parse import urljoin
from PIL import Image

from config import DATA_DIR, DOWNLOAD_YJJ_DIR
from logger import log_info, log_error
from utils.file_utils import clean_filename, download_file

MAX_PAGES_YJJ = 1

async def run_yjj_spider():

    # 读取Excel文档，判断去重条件
    excel_path = os.path.join(DOWNLOAD_YJJ_DIR, "药监局.xlsx")
    json_path = os.path.join(DATA_DIR, "药监局.json")
    existing_keys = set()  # 初始化
    existing_data = []  # 存储现有数据
    
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            existing_keys = set((item["发布时间"], item["政策标题"]) for item in existing_data)
            log_info(f"已有 {len(existing_data)} 条记录，重复标题和时间将跳过。")
        except Exception as e:
            log_error(f"读取 JSON 文件出错: {e}")
            existing_data = []
            existing_keys = set()
    else:
        existing_data = []
        existing_keys = set()

    # 使用列表存储字典，每个字典代表一条记录
    new_records = []

    try:
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=True)
            context = await browser.new_context(accept_downloads=True, locale="zh-CN")
            page = await context.new_page()
            # 增加初次加载的超时时间
            await page.goto("https://www.nmpa.gov.cn/xxgk/ggtg/", wait_until="networkidle", timeout=60000)  # 60秒超时
            await page.wait_for_timeout(10000)  # 增加等待时间到10秒

            sum = 0  # 计数器
            for page_num in range(1, MAX_PAGES_YJJ + 1):
                log_info(f"\n正在抓取第 {page_num} 页")
                
                lis = await page.query_selector_all('.list > ul > li')
                log_info(f"长度,{len(lis)}")
                if not lis:
                    break
                
                # 循环li列表
                for i, li in enumerate(lis):
                    detail_page = None
                    try:
                        # 标题
                        title_el = await li.query_selector("a")
                        title = await title_el.get_attribute("title") if title_el else ""

                        # 发布时间
                        fbsj_el = await li.query_selector("span")
                        fbsj_raw = await fbsj_el.inner_html() if fbsj_el else ""
                        match = re.search(r'\d{4}-\d{2}-\d{2}', fbsj_raw)  # 用正则提取日期格式
                        fbsj = match.group() if match else ""
                        print("发布日期:", fbsj)
                        
                        # 发布文号【从标题中提取，无文号用发布时间代替】
                        fbwh_raw = title
                        matches = re.findall(r'[（(]20\d{2}年第(\d+)号[）)]', fbwh_raw)
                        fbwh = matches[-1] if matches else ""

                        # 判断去重
                        if (fbsj, title) in existing_keys:
                            log_info(f"重复记录: {fbsj} - {title}")
                            if detail_page:
                                await detail_page.close()
                            continue

                        # 标题获取href链接，进入详情页
                        href = await title_el.get_attribute("href")
                        if not href:
                            continue
                        href = urljoin(page.url, href)
                        
                        # 2.点击打开新页面（模拟真实行为）
                        detail_page, _ = await asyncio.gather(
                            context.wait_for_event("page"),
                            title_el.click()
                        )
                        await detail_page.goto(href, wait_until="networkidle")
                        await detail_page.wait_for_timeout(1500)

                        # 发文机关固定为药监局
                        fwjg = "药监局"

                        # 唯一ID
                        policy_id = f"{fwjg}-{fbsj}-{title}" if not fbwh else f"{fwjg}-{fbsj}-{fbwh}"


                        # 是否有效
                        efficacy = "1"

                        # 生效日期 - 药监局通常没有明确的生效日期，可以使用发布日期或留空
                        sxrq = fbsj  # 默认使用发布日期作为生效日期

                        # PDF文件下载
                        unique_suffix = str(int(time.time() * 1000))
                        pdf_filename = f"{clean_filename(title)}_{unique_suffix}"
                        png_path = os.path.join(DOWNLOAD_YJJ_DIR, pdf_filename + ".png")
                        await detail_page.screenshot(path=png_path, full_page=True)
                        
                        # 图片格式转换
                        def convert_png_to_rgb(png_path):
                            im = Image.open(png_path)
                            if im.mode in ("RGBA", "LA"):
                                background = Image.new("RGB", im.size, (255, 255, 255))
                                background.paste(im, mask=im.split()[3])  # alpha 通道作为遮罩
                                rgb_path = png_path.replace(".png", "_rgb.png")
                                background.save(rgb_path, "PNG")
                                return rgb_path
                            return png_path
                        
                        # 应用转换函数
                        rgb_png_path = convert_png_to_rgb(png_path)
                        pdf_path = os.path.join(DOWNLOAD_YJJ_DIR, pdf_filename + ".pdf")
                        with open(pdf_path, "wb") as f:
                            f.write(img2pdf.convert(rgb_png_path))
                        log_info(f"{i+1}.PDF保存成功")

                        # 附件下载和保存
                        href_names = []
                        downloaded_files = []  # 记录实际下载的文件路径
                        attachments = await detail_page.query_selector_all(".text > p > a")
                        if attachments:
                            log_info(f"找到 {len(attachments)} 个附件")
                        
                        for a in attachments:
                            try:
                                file_href = await a.get_attribute("href")
                                text = await a.inner_text()
                                if file_href and any(file_href.endswith(ext) for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.wps']):
                                    if file_href.startswith("/"):
                                        file_href = "https://www.nmpa.gov.cn" + file_href  # 药监局_补充href地址

                                    suffix = os.path.splitext(file_href)[-1]
                                    clean_text = clean_filename(text)
                                    if not clean_text.lower().endswith(suffix.lower()):
                                        file_name = clean_text + suffix
                                    else:
                                        file_name = clean_text

                                    save_path = os.path.join(DOWNLOAD_YJJ_DIR, file_name)
                                    await download_file(file_href, save_path, referer=href)  # 药监局文件下载
                                    href_names.append(text)
                                    downloaded_files.append(save_path)  # 记录下载的文件路径
                            except Exception as e:
                                log_error(f"  附件下载处理异常: {e}")

                        # 创建ZIP包
                        zip_filename = f"{fbsj}_{clean_filename(title)}.zip"
                        zip_path = os.path.join(DOWNLOAD_YJJ_DIR, zip_filename)
                        zip_file_count = 0
                        
                        try:
                            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                                # 添加PDF截图到ZIP
                                if os.path.exists(pdf_path):
                                    zipf.write(pdf_path, os.path.basename(pdf_path))
                                    zip_file_count += 1
                                    log_info(f"PDF文件已添加到ZIP包")
                                
                                # 添加PNG截图到ZIP
                                if os.path.exists(rgb_png_path):
                                    zipf.write(rgb_png_path, os.path.basename(rgb_png_path))
                                    zip_file_count += 1
                                    log_info(f"PNG截图已添加到ZIP包")
                                
                                # 添加附件到ZIP
                                for file_path in downloaded_files:
                                    if os.path.exists(file_path):
                                        zipf.write(file_path, os.path.basename(file_path))
                                        zip_file_count += 1
                                        log_info(f"附件 {os.path.basename(file_path)} 已添加到ZIP包")
                            
                            log_info(f"ZIP包创建成功: {zip_path}, 包含 {zip_file_count} 个文件")
                            
                            # 清理临时文件（可选）
                            try:
                                if os.path.exists(png_path):
                                    os.remove(png_path)
                                if os.path.exists(rgb_png_path) and rgb_png_path != png_path:
                                    os.remove(rgb_png_path)
                                if os.path.exists(pdf_path):
                                    os.remove(pdf_path)
                                for file_path in downloaded_files:
                                    if os.path.exists(file_path):
                                        os.remove(file_path)
                                log_info("临时文件清理完成")
                            except Exception as e:
                                log_error(f"清理临时文件时出错: {e}")
                                
                        except Exception as e:
                            log_error(f"创建ZIP包时出错: {e}")
                            zip_path = ""
                            zip_file_count = 0
                        
                        # 创建单条记录字典
                        record = {
                            "政策标题": title,
                            "发文机关": fwjg,
                            "详情页链接": href,  # 添加详情页URL
                            "发布时间": fbsj,
                            "生效日期": sxrq,
                            "发布文号": fbwh,
                            "是否有效": efficacy,
                            "zip包文件数量": zip_file_count,  # ZIP包内文件数量
                            "zip包路径": zip_path,  # ZIP包完整路径
                            "附件列表": href_names,  # 直接存储列表，不转换为字符串
                            "唯一ID": policy_id,  # 唯一ID
                        }
                        
                        # 添加到新记录列表
                        new_records.append(record)

                        sum += 1
                        await detail_page.close()
                        await asyncio.sleep(1)
                    except Exception as e:
                        log_error(f"{i+1}. 处理条目异常: {e}")
                        if detail_page:
                            await detail_page.close()
                        continue

                # 翻页
                if page_num < MAX_PAGES_YJJ:
                    next_button = page.get_by_text("下一页")  # 返回的是一个 Locator 对象，不加 await
                    if next_button:
                        await next_button.click()
                        await page.wait_for_timeout(3000)
                    else:
                        break

            await browser.close()
    except Exception as e:
        log_error(f"Playwright 主流程异常: {e}")

    # 数据保存
    if new_records:
        # 合并现有数据和新数据
        all_records = existing_data + new_records
        
        # 保存为JSON格式（直接保存字典列表）
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(all_records, f, ensure_ascii=False, indent=4)
        
        # 保存为Excel格式
        df_all = pd.DataFrame(all_records)
        # 对于Excel，将附件列表转换为字符串格式
        df_all['附件列表'] = df_all['附件列表'].apply(lambda x: str(x) if x else "[]")
        df_all.to_excel(excel_path, index=False)
        
        log_info(f"\n共保存 {len(all_records)} 条记录,新增 {sum} 条记录")
        
        # 返回完整的记录列表
        return all_records
    else:
        log_info(f"\n本次无新增记录")
        return existing_data

# 如果你只想获取新增的记录，可以添加这个函数
async def get_new_records_only():
    """只返回新增的记录"""
    # ... 在run_yjj_spider函数中，你可以直接返回new_records
    pass