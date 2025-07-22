from playwright.async_api import async_playwright
import asyncio

async def print_element_content(page, selector):
    try:
        # 查找元素
        el = await page.query_selector(selector)
        
        if el:
            # 获取元素的文本内容
            text = await el.inner_text()
            
            # 打印提取到的文本内容
            print(f"选择器 '{selector}' 提取的元素文本：{text.strip()}")
        else:
            print(f"未找到元素：{selector}")
    except Exception as e:
        print(f"提取元素时发生错误: {e}")

async def main():
    # 使用 playwright 启动浏览器
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)  # 可以设置headless=True以在后台运行
        page = await browser.new_page()
        await page.goto("https://www.nmpa.gov.cn/xxgk/ggtg/")  # 打开网页
        selector = "div.list > ul > li:nth-child(1) > a"
        await print_element_content(page, selector)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())  # 使用 asyncio.run 来启动异步的 main 函数
