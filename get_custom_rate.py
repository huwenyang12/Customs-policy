from clicknium import clicknium as cc, locator
import os
from time import sleep
import MySQLdb
import MySQLdb.cursors as cors
import traceback
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class CustomRate():

    def get_conn(self, is_test=False):
        if is_test:
            return MySQLdb.connect(
                host="localhost",
                port=3306,
                user="root",
                passwd="root",
                db="ysx-cms",
                charset='utf8mb4',
                cursorclass=cors.DictCursor
            )
        return MySQLdb.connect(
            host="123.60.179.95",
            port=3306,
            user="root",
            passwd="admin.789",
            db="ysx-cms",
            charset='utf8mb4',
            cursorclass=cors.DictCursor
        )

    def main(self, start_month, end_month, is_test=False):
        tab = cc.chrome.open("https://www.guanwuxiaoer.com/haiguanhuilv.php")
        try:
            elem = tab.wait_appear(locator.guanwuxiaoer.img_close, wait_timeout=2)
            if elem:
                elem.click()
        except:
            pass
        tab.wait_appear(locator.guanwuxiaoer.input_开始月份)

        # 开始/结束分别填
        tab.find_element(locator.guanwuxiaoer.input_开始月份).set_text(start_month)
        sleep(1)
        tab.find_element(locator.guanwuxiaoer.input_结束月份).set_text(end_month)
        sleep(1)
        tab.find_element(locator.guanwuxiaoer.input_开始月份).set_text(start_month)
        sleep(1)

        # 校验开始月份
        if tab.find_element(locator.guanwuxiaoer.input_开始月份).get_text() != start_month:
            raise Exception("查询错误，开始月份不对应")

        tab.find_element(locator.guanwuxiaoer.button_查询).click()
        sleep(5)

        if tab.wait_appear(locator.guanwuxiaoer.span_共_120_条) == None:
            raise Exception("查询超时")

        total_info = tab.find_element(locator.guanwuxiaoer.span_共_120_条).get_text()
        total = int(total_info.replace("共","").replace("条","").strip())
        pagecount = total // 10 if total % 10 == 0 else total // 10 + 1

        start_int = int(start_month.replace("-", ""))
        end_int = int(end_month.replace("-", ""))

        for page in range(pagecount):
            tab.find_element(locator.guanwuxiaoer.number_el_input_inner).set_text(page+1)
            sleep(1)

            tab.find_element(locator.guanwuxiaoer.span_共_120_条).click()
            sleep(3)

            for rowIndex in range(10):
                if tab.wait_appear(locator.guanwuxiaoer.币种中文, {"index": rowIndex+1}, wait_timeout=10) == None:
                    break

                cur_month = tab.find_element(locator.guanwuxiaoer.适用月份, {"index": rowIndex+1}).get_text().strip()
                cur_int = int(cur_month.replace("-", ""))

                if cur_int < start_int or cur_int > end_int:
                    continue

                chName = tab.find_element(locator.guanwuxiaoer.币种中文, {"index": rowIndex+1}).get_text().strip()
                enName = tab.find_element(locator.guanwuxiaoer.币种英文, {"index": rowIndex+1}).get_text().strip()
                code = tab.find_element(locator.guanwuxiaoer.币种代码, {"index": rowIndex+1}).get_text().strip()
                rate = tab.find_element(locator.guanwuxiaoer.海关汇率, {"index": rowIndex+1}).get_text().strip()

                print([chName, enName, code, rate, cur_month])
                self.insert_qcca_base([chName, enName, code, rate, cur_month], is_test=is_test)

        tab.close()

    def insert_qcca_base(self, params, is_test=False):
        chName, enName, code, rate, month = params

        month_int = int(month.replace("-", ""))
        rate_float = float(rate)
        release_date = datetime.now()

        sql = """INSERT ignore INTO cms_custom_rate_month
                 (month, rate, currency_code, currency_name_cn, currency_name_en, release_date)
                 VALUES (%s, %s, %s, %s, %s, %s)"""

        retry_times = 3
        while True:
            if retry_times < 0:
                raise Exception("入库失败，已重试3次")

            conn = None
            cur = None
            try:
                conn = self.get_conn(is_test=is_test)
                cur = conn.cursor()

                cur.execute(sql, (month_int, rate_float, code, chName, enName, release_date))
                conn.commit()
                print(f"成功插入数据：{chName} ({code}) - {rate_float}")
                break

            except Exception:
                print("插入失败，" + traceback.format_exc())
                if conn:
                    conn.rollback()
                retry_times -= 1

            finally:
                if cur:
                    cur.close()
                if conn:
                    conn.close()

if __name__ == "__main__":
    customrate = CustomRate()
    customrate.main("2025-10", "2026-01", is_test=True)
