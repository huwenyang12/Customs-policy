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
                return text.strip()
    return ""
# 商务委=================================================================================
# 商务委_发布时间
async def sww_fbsj(page):
    selectors = [
        "div.art-con-gonggao",
        "p.MsoNormal:nth-child(9)"
    ]
    for selector in selectors:
        if selector == "div.art-con-gonggao":
            el = await page.query_selector(selector)
            if el:
                text = await el.inner_text()
                if text.strip():
                    time_match = re.search(r'【发文日期】\s*(\d{4}年\d{1,2}月\d{1,2}日)', text.strip())
                    if time_match:
                        return time_match.group(1) # 表示获取第一个括号内匹配的内容
        else:
            el = await page.query_selector(selector)
            if el:
                text = await el.inner_text()
                if text.strip():
                    return text.strip()
    return ""
# 商务委_发布文号
async def sww_fbwh(page):
    selectors = [
        "div.art-con-gonggao"
    ]
    for selector in selectors:
        el = await page.query_selector(selector)
        if el:
            text = await el.inner_text()
            if text.strip():
                wenhao_match = re.search(r'【发布文号】([^】]+)【', text.strip())
                if wenhao_match:
                    return wenhao_match.group(1) # 表示获取第一个括号内匹配的内容
    return "无文号"

# 工信部===================================================================================
# 工信部_发布时间

