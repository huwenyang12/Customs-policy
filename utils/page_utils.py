import re

# 封装发布文号选择器
async def czb_fbwh(page):
    selectors = [
        "div.TRS_Editor > p > b",
        "div.TRS_Editor > p",
        "div.TRS_Editor > div > b",
        "div.TRS_Editor:nth-child(2) > p:nth-child(2) > b:nth-child(1)"
    ]
    for selector in selectors:
        el = await page.query_selector(selector)
        if el:
            text = await el.inner_text()
            if text.strip():
                # 提取“第X号”或“X号”中的数字
                match = re.search(r'(?:第)?(\d+)号', text.strip())  # 使用(?:第)?表示第字是可选的
                if match:
                    return match.group(1)  # 返回提取的数字
    return ""


# 商务委=================================================================================
async def sww_fbsj(page):
    selectors = [
        "div.f-cb > div > div:nth-child(3) > div",
        "div > div.art-con.art-con-bottonmLine > p:nth-child(3)",
        "div.art-con.art-con-bottonmLine > h2 > strong",
    ]
    for selector in selectors:
        print(f"尝试选择器: {selector}")
        el = await page.query_selector(selector)
        if el:
            text = await el.inner_text()
            print(f"提取的文本: {text}")
            if text.strip():
                match = re.search(r'(?:第)?(\d+)号', text.strip())
                if match:
                    print(f"匹配成功：{match.group(0)}")
                    return match.group(1)
                else:
                    print("没匹配到正则")
        else:
            print(f"找不到元素: {selector}")
    return ""

# 工信部===================================================================================
# 工信部_发布时间

