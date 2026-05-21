# P0 来源元数据映射明细表（8个）

> 目标：给出可直接程序化抓取的统一字段映射（`title/author/date/publisher/license/source_url`）。

## 1) 中国国家图书馆（中华古籍资源库）

- source_id: `nlc_read`
- 获取方式：详情页 HTML 解析（无公开 API）
- URL 模板：`http://read.nlc.cn/allSearch/searchDetail?searchType=1002&showType=1&indexName=data_{aid}&fid={fid}`

| 统一字段 | 来源字段/规则 |
|---|---|
| title | `<input id="title" value="...">` |
| author | `<input id="author" value="...">` |
| date | `span.tt=出版发行项` 对应 `span.t1` |
| publisher | 同 `出版发行项`（该站通常合并记录） |
| license | 固定值：`免费开放·禁止商用·禁止批量下载` |
| source_url | 请求 URL |

## 2) 哈佛大学图书馆 Chinese Rare Books

- source_id: `harvard_rare_books`
- 获取方式：Blacklight JSON API
- URL 模板：`https://curiosity.lib.harvard.edu/chinese-rare-books/catalog/{record_id}.json`

| 统一字段 | 来源字段/规则 |
|---|---|
| title | `data.attributes.title` |
| author | `data.attributes.creator-contributor_tesim.attributes.value` |
| date | `data.attributes.date_ssim.attributes.value` |
| publisher | `data.attributes.publisher_ssim.attributes.value` |
| license | 固定值：`CC BY 4.0` |
| source_url | 请求 URL |

## 3) 国立国会图书馆（NDL）

- source_id: `ndl_item`
- 获取方式：数字馆藏 Item API
- URL 模板：`https://dl.ndl.go.jp/api/item/search/info:ndljp/pid/{book_id}`

| 统一字段 | 来源字段/规则 |
|---|---|
| title | `item.meta.0311Dtct[0]` |
| author | `item.meta.0010Dtct[0]` |
| date | `item.meta.0058Dod[0]` |
| publisher | `item.meta.0058Dod[0]` |
| license | `item.rights.code` |
| source_url | 请求 URL |

## 4) Internet Archive

- source_id: `internet_archive_metadata`
- 获取方式：Metadata API
- URL 模板：`https://archive.org/metadata/{identifier}`

| 统一字段 | 来源字段/规则 |
|---|---|
| title | `metadata.title` |
| author | `metadata.creator` |
| date | `metadata.date`（回退 `metadata.year`） |
| publisher | `metadata.publisher` |
| license | `metadata.licenseurl`（如存在） |
| source_url | 请求 URL |

## 5) 中国哲学书电子化计划（ctext）

- source_id: `ctext_gettext`
- 获取方式：JSON API（章节/原典文本）
- URL 模板：`https://api.ctext.org/gettext?urn={urn}&if={lang}`

| 统一字段 | 来源字段/规则 |
|---|---|
| title | `title` |
| author | `null`（该接口通常不返回） |
| date | `null` |
| publisher | 固定值：`中國哲學書電子化計劃` |
| license | 固定值：`站点规则为准` |
| source_url | 请求 URL |

## 6) 中华寻根网

- source_id: `ouroots_catalog_volume`
- 获取方式：卷册目录 API
- URL 模板：`http://dsnode.ouroots.nlc.cn/gtService/data/catalogVolume?bookId={book_id}`

| 统一字段 | 来源字段/规则 |
|---|---|
| title | `data[0].bookName`（若存在） |
| author | `data[0].author`（若存在） |
| date | `data[0].publishDate`（若存在） |
| publisher | `data[0].publisher`（若存在） |
| license | 固定值：`免费开放浏览` |
| source_url | 请求 URL |

## 7) 温州市图书馆（旧版 API）

- source_id: `wzlib_resource`
- 获取方式：资源详情 API
- URL 模板：`https://oyjy.wzlib.cn/api/search/v1/resource/{book_id}`

| 统一字段 | 来源字段/规则 |
|---|---|
| title | `title`（回退 `resourceName`） |
| author | `author` |
| date | `publishDate` |
| publisher | `publisher` |
| license | 固定值：`站点规则为准` |
| source_url | 请求 URL |

## 8) 国書データベース（NIJL）

- source_id: `kokusho_manifest`
- 获取方式：IIIF Manifest
- URL 模板：`https://kokusho.nijl.ac.jp/biblio/{biblio_id}/manifest`

| 统一字段 | 来源字段/规则 |
|---|---|
| title | `label` 或 `metadata[label=Title].value` |
| author | `metadata[label=Author].value` |
| date | `null`（manifest 常无） |
| publisher | `attribution` |
| license | `license` |
| source_url | 请求 URL |
