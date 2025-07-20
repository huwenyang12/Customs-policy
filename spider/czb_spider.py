# 抓取主逻辑
import asyncio
import pandas as pd
import time
import os
import json
import zipfile
from playwright.async_api import async_playwright
import img2pdf
from urllib.parse import urljoin, urlparse
from PIL import Image

from config import DATA_DIR, DOWNLOAD_CZB_DIR, MAX_PAGES_CZB
from logger import log_info, log_error
from utils.file_utils import clean_filename, download_file
from utils.page_utils import czb_fbwh

async def run_czb_spider():

    # 读取Excel文档，判断去重条件
    excel_path = os.path.join(DOWNLOAD_CZB_DIR, "财政部.xlsx")
    json_path = os.path.join(DATA_DIR, "财政部.json")
    existing_keys = set()  # 初始化
    existing_data = []  # 存储现有数据
    
    if os.path.exists(excel_path):
        try:
            df_existing = pd.read_excel(excel_path)
            existing_keys = set(zip(df_existing["发布时间"], df_existing["政策标题"]))
            existing_data = df_existing.to_dict('records')
            log_info(f"已有 {len(df_existing)} 条记录，重复标题和时间将跳过。")
        except Exception as e:
            log_error(f"读取 Excel 文件出错: {e}")
            existing_data = []
    else:
        existing_data = []

    # 使用列表存储字典，每个字典代表一条记录
    new_records = []

    try:
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=True)
            context = await browser.new_context(accept_downloads=True, locale="zh-CN")
            page = await context.new_page()
            await page.goto("http://gss.mof.gov.cn/gzdt/zhengcefabu/index.htm", wait_until="networkidle")
            await page.wait_for_timeout(3000)

            sum = 0  # 计数器
            for page_num in range(1, MAX_PAGES_CZB + 1):
                log_info(f"\n正在抓取第 {page_num} 页")
                lis = await page.query_selector_all('.liBox > li')
                if not lis:
                    break
                # 循环li列表
                for i, li in enumerate(lis):
                    detail_page = None
                    try:
                        # 标题
                        title_el = await li.query_selector("a")
                        title = await title_el.inner_text() if title_el else ""
                        # 发布时间
                        time_el = await li.query_selector("span")
                        fbsj = await time_el.inner_text() if time_el else ""
                        
                        # 判断去重
                        if (fbsj, title) in existing_keys:
                            log_info(f"重复记录: {fbsj} - {title}")
                            if detail_page:
                                await detail_page.close()
                            continue
                            
                        # 进入详情页 - 修复URL拼接逻辑
                        href = await title_el.get_attribute("href")
                        if not href:
                            continue
                        
                        # 判断href是否为完整URL
                        if href.startswith("http://") or href.startswith("https://"):
                            # 已经是完整URL，直接使用
                            full_url = href
                        else:
                            # 相对路径，需要拼接
                            if href.startswith("/"):
                                # 绝对路径，使用域名拼接
                                parsed_url = urlparse(page.url)
                                full_url = f"{parsed_url.scheme}://{parsed_url.netloc}{href}"
                            else:
                                # 相对路径，使用当前页面路径拼接
                                full_url = urljoin(page.url, href)
                        
                        log_info(f"访问详情页: {full_url}")
                        
                        detail_page = await context.new_page()
                        await detail_page.goto(full_url, wait_until="networkidle")
                        await detail_page.wait_for_timeout(1500)
                        
                        # 调用文号方法查找
                        fbwh = await czb_fbwh(detail_page)

                        # 发文机关固定为财政部
                        fwjg = "财政部"

                        # 唯一ID
                        policy_id = f"{fbsj}-{fbwh}"

                        # 是否有效（财政部一般默认有效）
                        efficacy = "有效"

                        # 生效日期（财政部通常与发布日期相同，也可以根据实际情况调整）
                        sxrq = fbsj

                        # pdf文件下载
                        unique_suffix = str(int(time.time() * 1000))
                        pdf_filename = f"{clean_filename(title)}_{unique_suffix}"
                        png_path = os.path.join(DOWNLOAD_CZB_DIR, pdf_filename + ".png")
                        await detail_page.screenshot(path=png_path, full_page=True)
                        
                        # 去除图片透明通道
                        def convert_png_to_rgb(png_path):
                            im = Image.open(png_path)
                            if im.mode in ("RGBA", "LA"):
                                background = Image.new("RGB", im.size, (255, 255, 255))
                                background.paste(im, mask=im.split()[3])  # alpha 通道作为遮罩
                                rgb_path = png_path.replace(".png", "_rgb.png")
                                background.save(rgb_path, "PNG")
                                return rgb_path
                            return png_path
                        
                        # 图片转换PDF
                        rgb_png_path = convert_png_to_rgb(png_path)
                        pdf_path = os.path.join(DOWNLOAD_CZB_DIR, pdf_filename + ".pdf")
                        with open(pdf_path, "wb") as f:
                            f.write(img2pdf.convert(rgb_png_path))
                        log_info(f"{i+1}. 网页PDF保存成功")

                        # 附件下载和保存
                        href_names = []
                        downloaded_files = []  # 记录实际下载的文件路径
                        
                        # 查找附件链接（根据财政部网站的实际结构调整选择器）
                        attachments = await detail_page.query_selector_all("a[href*='.pdf'], a[href*='.doc'], a[href*='.docx'], a[href*='.xls'], a[href*='.xlsx'], a[href*='.zip'], a[href*='.wps']")
                        if attachments: 
                            log_info(f"找到 {len(attachments)} 个附件")
                        
                        for a in attachments:
                            try:
                                file_href = await a.get_attribute("href")
                                text = await a.inner_text()
                                if file_href and any(file_href.endswith(ext) for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.wps']):
                                    # 修复附件URL拼接逻辑
                                    if file_href.startswith("http://") or file_href.startswith("https://"):
                                        # 已经是完整URL
                                        file_full_url = file_href
                                    elif file_href.startswith("/"):
                                        # 绝对路径，判断应该使用哪个域名
                                        if "mof.gov.cn" in full_url:
                                            file_full_url = "https://www.mof.gov.cn" + file_href
                                        else:
                                            file_full_url = "http://gss.mof.gov.cn" + file_href
                                    else:
                                        # 相对路径
                                        file_full_url = urljoin(full_url, file_href)

                                    suffix = os.path.splitext(file_href)[-1]
                                    clean_text = clean_filename(text)
                                    if not clean_text.lower().endswith(suffix.lower()):
                                        file_name = clean_text + suffix
                                    else:
                                        file_name = clean_text

                                    save_path = os.path.join(DOWNLOAD_CZB_DIR, file_name)
                                    await download_file(file_full_url, save_path, referer=full_url)  # 使用正确的URL和referer
                                    href_names.append(text)
                                    downloaded_files.append(save_path)  # 记录下载的文件路径
                            except Exception as e:
                                log_error(f"  附件下载处理异常: {e}")

                        # 创建ZIP包
                        zip_filename = f"{fbsj}_{clean_filename(title)}.zip"
                        zip_path = os.path.join(DOWNLOAD_CZB_DIR, zip_filename)
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
                            "详情页链接": full_url,  # 使用修正后的完整URL
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

                if page_num < MAX_PAGES_CZB:
                    next_button = await page.query_selector("div.listBox > p:nth-child(5) > span:nth-child(9) > a")
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
async def get_new_czb_records_only():
    """只返回新增的记录"""
    # 在run_czb_spider函数中，你可以直接返回new_records
    pass