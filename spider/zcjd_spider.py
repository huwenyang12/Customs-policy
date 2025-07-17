import asyncio
import pandas as pd
import time
import os
import re
from playwright.async_api import async_playwright
import img2pdf
from urllib.parse import urljoin
from PIL import Image


from config import DATA_DIR, DOWNLOAD_ZCJD_DIR, MAX_PAGES_ZCJD
from logger import log_info, log_error
from utils.file_utils import clean_filename, download_file

async def run_zcjd_spider():

    # 读取Excel文档，判断驱虫条件
    excel_path = os.path.join(DATA_DIR, "政策解读.xlsx")
    json_path = os.path.join(DATA_DIR, "政策解读.json")
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

    # 发布时间、发文机关、发布标题、生效日期、发布文号、附件列表
    FBSJ_list, FWJG_list, FBBT_list, SXRQ_list, FBWH_list, HREF_list = [], [], [], [], [], []

    try:
        async with async_playwright() as p:
            browser = await p.firefox.launch(headless=True)
            context = await browser.new_context(accept_downloads=True, locale="zh-CN")
            page = await context.new_page()
            await page.goto("http://www.customs.gov.cn/customs/302249/302270/302272/index.html", wait_until="networkidle")
            await page.wait_for_timeout(3000)

            sum = 0 # 计数器
            for page_num in range(1, MAX_PAGES_ZCJD + 1):
                log_info( f"\n正在抓取第 {page_num} 页")
                lis = await page.query_selector_all('.conList_ull > li')
                log_info(f"长度,{len(lis)}")
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
                        fbsj_el = await li.query_selector("span")
                        fbsj_raw = await fbsj_el.inner_html() if fbsj_el else ""
                        match = re.search(r'\d{4}-\d{2}-\d{2}', fbsj_raw)# 用正则提取日期格式
                        fbsj = match.group() if match else ""
                        # 判断去重
                        if (fbsj, title) in existing_keys:
                            log_info( f"重复记录: {fbsj} - {title}")
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

                        # # 发布文号
                        # fbwh_el = await detail_page.query_selector("//*[@id='hgfg_con']/div[2]/div[1]")
                        # fbwh_WH = await fbwh_el.inner_text() if fbwh_el else ""
                        # fbwh = fbwh_WH.split('】')[-1].strip() if '】' in fbwh_WH else fbwh_WH
                        # # 发文机关
                        # fwjg_el = await detail_page.query_selector(".hgzs_lis2 > div:nth-child(2)")
                        # fwjg_FWJG = await fwjg_el.inner_text() if fwjg_el else ""
                        # fwjg = fwjg_FWJG.split('】')[-1].strip() if '】' in fwjg_FWJG else fwjg_FWJG

                        # # 生效日期
                        # sxrq_el = await detail_page.query_selector(".hgzs_lis3 > div:nth-child(2)")
                        # sxrq_SXRQ = await sxrq_el.inner_text() if sxrq_el else ""
                        # sxrq = sxrq_SXRQ.split('】')[-1].strip() if '】' in sxrq_SXRQ else sxrq_SXRQ

                        # 解读政策链接
                        zc_href = await detail_page.query_selector("div.easysite-related-news > ul > li > a")
                        file_href = await zc_href.get_attribute("href")
                        if not file_href:
                            continue
                        if file_href.startswith("/"):
                            file_href = "http://www.customs.gov.cn" + file_href

                        # # pdf文件下载
                        unique_suffix = str(int(time.time() * 1000))
                        pdf_filename = f"{clean_filename(title)}_{unique_suffix}"
                        png_path = os.path.join(DOWNLOAD_ZCJD_DIR, pdf_filename + ".png")
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
                        pdf_path = os.path.join(DOWNLOAD_ZCJD_DIR, pdf_filename + ".pdf")
                        with open(pdf_path, "wb") as f:
                            f.write(img2pdf.convert(rgb_png_path))
                        log_info(f"{i+1}.网页PDF保存成功")

                        # 列表追加
                        HREF_list.append(file_href) # 文件链接列表
                        FBBT_list.append(title) # 发布标题
                        FBSJ_list.append(fbsj) # 发布时间
                        FWJG_list.append("") # 发文机关
                        FBWH_list.append("") # 发布文号
                        SXRQ_list.append("") # 生效日期

                        sum += 1
                        await detail_page.close()
                        await asyncio.sleep(1)
                    except Exception as e:
                        log_error(f"{i+1}. 处理条目异常: {e}")
                        if detail_page:
                            await detail_page.close()
                        continue

                # 翻页
                if page_num < MAX_PAGES_ZCJD:
                    next_button = await page.query_selector("div.paging > a.pagingNormal.next")
                    if next_button:
                        await next_button.click()
                        await page.wait_for_timeout(3000)
                    else:
                        break

            await browser.close()
    except Exception as e:
        log_error(f"Playwright 主流程异常: {e}")

    if FBSJ_list:
        df_new = pd.DataFrame(list(zip(FBBT_list, FWJG_list, FBSJ_list, SXRQ_list, FBWH_list, HREF_list)),
                              columns=["政策标题", "发文机关", "发布时间", "生效日期", "发布文号","政策链接"])
        df_all = pd.concat([df_existing, df_new], ignore_index=True) if not df_existing.empty else df_new

        df_all.to_excel(excel_path, index=False)
        df_all.to_json(json_path, orient="records", force_ascii=False, indent=4)
        log_info(f"\n共保存 {len(df_all)} 条记录,新增 {sum} 条记录")
    else:
        log_info(f"\n本次无新增记录")