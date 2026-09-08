# 项目指令（故事库）

本文件对在本工作区（E:\claude\测试题\教育\故事）启动的所有 ZCode 会话自动生效。

## 项目约定（备忘）

- 站点数据管线：改故事后运行 `python3 _regen_indexes.py` 与 `python3 build_site.py`，再提交推送。
- 引号规范：对话“”、特指「」、内层‘’；新故事写完用 `_quote_convert.py --dry` 自查。
- 中国国家地理分类的新增地标：在 `_fetch_geo_images.py` 的 STORIES 里加词条下载图片（Commons 开放授权），逐张目检后在 `中国国家地理/图片版权.md` 登记署名。
- 老规矩：不逐字照抄有版权的译本/文章；故事信息行与「小启示」体例保持一致。
