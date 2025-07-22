import asyncio
from spider.hgfg_spider import run_hgfg_spider # 海关法规
from spider.zcjd_spider import run_zcjd_spider # 海关法规_政策解读
from spider.czb_spider import run_czb_spider # 财政部
from spider.sww_spider import run_sww_spider # 商务委
from spider.gxb_spider import run_gxb_spider # 工信部
from spider.yjj_spider import run_yjj_spider # 药监局




async def main():
    await run_hgfg_spider()
    await run_zcjd_spider()
    await run_czb_spider()
    await run_sww_spider()
    await run_gxb_spider()
    await run_yjj_spider()

if __name__ == "__main__":
    asyncio.run(main())

