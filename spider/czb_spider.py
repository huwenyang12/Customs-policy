# 抓取主逻辑
import asyncio
import pandas as pd
import time
import os
from playwright.async_api import async_playwright
import img2pdf
from urllib.parse import urljoin
from PIL import Image

from config import DATA_DIR, DOWNLOAD_CZB_DIR, MAX_PAGES_CZB
from logger import log_info, log_error
from utils.file_utils import clean_filename
from utils.page_utils import czb_fbwh

async def run_czb_spider():

    # 读取Excel文档，判断驱虫条件
    excel_path = os.path.join(DATA_DIR, "财政部.xlsx")
    json_path = os.path.join(DATA_DIR, "财政部.json")
    existing_keys = {} # 初始化
    if os.path.exists(excel_path):
        try:
            df_existing = pd.read_excel(excel_path)
            existing_keys = set(zip(df_existing["发布时间"], df_existing["政策标题"]))
            log_info( f"已有 {len(df_existing)} 条记录，重复标题和时间将跳过。")
        except Exception as e:
            log_error( f"读取 Excel 文件出错: {e}")
            df_existing = pd.DataFrame()
    else:
        df_existing = pd.DataFrame()

    # 所需字段列表：发布时间、发文机关、发布标题、生效日期、发布文号
    FBSJ_list, FWJG_list, FBBT_list, SXRQ_list, FBWH_list = [], [], [], [], []

    try:
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=False)
            context = await browser.new_context(accept_downloads=True, locale="zh-CN")
            page = await context.new_page()
            await page.goto("http://gss.mof.gov.cn/gzdt/zhengcefabu/index.htm", wait_until="networkidle")
            await page.wait_for_timeout(3000)

            sum = 0 # 计数器
            for page_num in range(1, MAX_PAGES_CZB + 1):
                log_info( f"\n正在抓取第 {page_num} 页")
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
                            log_info( f"重复记录: {fbsj} - {title}")
                            if detail_page:
                                await detail_page.close()
                            continue
                        # 进入详情页
                        href = await title_el.get_attribute("href")
                        if not href:
                            continue
                        href = page.url.rsplit('/', 1)[0] + "/" + href
                        detail_page = await context.new_page()
                        await detail_page.goto(href, wait_until="networkidle")
                        await detail_page.wait_for_timeout(1500)
                        # 调用文号方法查找
                        fbwh = await czb_fbwh(detail_page)

                        # pdf文件下载
                        unique_suffix = str(int(time.time() * 1000))
                        pdf_filename = f"{clean_filename(title)}_{unique_suffix}"
                        png_path = os.path.join(DOWNLOAD_CZB_DIR, pdf_filename + ".png")
                        await detail_page.screenshot(path=png_path, full_page=True)
                        # # 去除图片透明通道
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
                        # 列表追加
                        FBBT_list.append(title)
                        FBSJ_list.append(fbsj)
                        FWJG_list.append("财政部")
                        FBWH_list.append(fbwh)
                        SXRQ_list.append("")

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

    if FBSJ_list:
        df_new = pd.DataFrame(list(zip(FBBT_list, FWJG_list, FBSJ_list, SXRQ_list, FBWH_list)),
                              columns=["政策标题", "发文机关", "发布时间", "生效日期", "发布文号"])
        df_all = pd.concat([df_existing, df_new], ignore_index=True) if not df_existing.empty else df_new

        df_all.to_excel(excel_path, index=False)
        df_all.to_json(json_path, orient="records", force_ascii=False, indent=4)
        log_info(f"\n共保存 {len(df_all)} 条记录,新增 {sum} 条记录")
    else:
        log_info("\n本次无新增记录")
