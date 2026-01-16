import time
import logging
from playwright.sync_api import sync_playwright

TARGET_URL = "http://123.60.179.95/"
URL_KEYWORD = ""          # 抓取指定接口的请求
WAIT_SECONDS = 60

SEL_USERNAME = 'input.el-input__inner[placeholder="请输入用户名"]'
SEL_PASSWORD = 'input.el-input__inner[type="password"][placeholder="请输入密码"]'
SEL_LOGIN_BTN = 'button.el-button--primary:has-text("登录")'

def valid(auth: str) -> bool:
    a = (auth or "").lower()
    return auth and "null" not in a and "undefined" not in a and len(auth) >= 20

def cookie_header(context) -> str:
    return "; ".join(f"{c['name']}={c['value']}" for c in context.cookies() if c.get("name") and c.get("value"))

def query_voucher(username: str, password: str):
    """
    return: (请求URL, Token, Cookie) 三元组，未获取到返回 None
    """
    with sync_playwright() as p:
        # 无头模式开关
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        result = {"url": None, "auth": None, "cookie": None}

        def on_request(req):
            if result["auth"]:
                return
            auth = req.headers.get("authorization") or req.headers.get("Authorization")
            if not valid(auth):
                return
            if URL_KEYWORD and URL_KEYWORD not in req.url:
                return

            result.update(url=req.url, auth=auth, cookie=cookie_header(context))
            print("Request URL:", result["url"])
            print("Authorization:", result["auth"])
            print("Cookie:", result["cookie"])

        page.on("request", on_request)
        page.goto(TARGET_URL)

        # 尝试登录：找不到登录框就跳过（可能已登录）
        try:
            page.wait_for_selector(SEL_USERNAME, timeout=3000)
            page.fill(SEL_USERNAME, username)
            page.fill(SEL_PASSWORD, password)
            page.click(SEL_LOGIN_BTN)
        except Exception:
            pass
        # 轻触发一次请求
        try:
            page.wait_for_timeout(800)
            page.reload()
        except Exception:
            pass

        end = time.time() + WAIT_SECONDS
        while time.time() < end and not result["auth"]:
            page.wait_for_timeout(300)

        context.close()
        browser.close()

        return (result["url"], result["auth"], result["cookie"]) if result["auth"] else None


def main():
    username = "cmshgzc"
    password = "123456"
    url, token, cookie = query_voucher(username, password)
    return url, token, cookie


if __name__ == "__main__":
    main()
