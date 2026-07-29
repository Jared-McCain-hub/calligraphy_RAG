# 书法 RAG 知识库起始资料清单

## 使用说明

这份清单用于后续构建中国书法问答系统的知识库，优先覆盖 4 类核心语料：

- 术语库
- 书法家人物库
- 作品库
- 背景知识库

推荐原则：

- 优先采用官方馆藏、博物馆、权威百科或公开知识性页面作为起始来源
- 结构化实体先入 MySQL，长文本说明再切分为 `knowledge_chunks`
- 术语类条目优先补齐中英对照，便于后续术语校验和双语回答
- 每条资料都保留 `source_ref` 和原始链接，方便回答引用

## 推荐字段

### 术语类

- `slug`
- `name_cn`
- `name_en`
- `aliases`
- `category`
- `definition`
- `usage_notes`
- `source`
- `source_url`

### 人物类

- `slug`
- `name_cn`
- `name_en`
- `era`
- `birth_year`
- `death_year`
- `biography`
- `achievements`
- `source`
- `source_url`

### 作品类

- `slug`
- `title_cn`
- `title_en`
- `calligrapher`
- `era`
- `style`
- `description`
- `excerpt_text`
- `current_collection`
- `image_url`
- `source`
- `source_url`

### 背景知识类

- `title`
- `theme`
- `era`
- `summary`
- `content`
- `source`
- `source_url`

## 一、术语库

### 一级优先

1. 颜体
   - 建议英文：`Yan Style`
   - 推荐来源：[颜体_百度百科](https://baike.baidu.com/item/%E9%A2%9C%E4%BD%93)
   - 用途：术语标准译法、风格定义、问答核心概念

2. 楷书
   - 建议英文：`Regular Script`
   - 推荐来源：[楷书_百度百科](https://baike.baidu.com/item/%E6%A5%B7%E4%B9%A6/482941)
   - 用途：书体定义、术语父类、作品风格标注

3. 行书
   - 建议英文：`Running Script`
   - 推荐来源：[行书_百度百科](https://baike.baidu.com/item/%E8%A1%8C%E4%B9%A6/472950)
   - 用途：作品风格标注、跨语言译法规范

4. 中锋
   - 推荐来源：[中锋相关资料入口](https://baike.baidu.com/tashuo/browse/content?id=8ebf3bd3727b969085e0dac6&fromModule=tashuo-article_bottom-tashuo-feed)
   - 用途：技法解释、作品分析

5. 藏锋
   - 推荐来源：[藏锋_百度百科](https://baike.baidu.com/item/%E8%97%8F%E9%94%8B/16983097)
   - 用途：技法解释、术语问答

6. 侧锋
   - 推荐来源：[侧锋用笔_百度百科](https://baike.baidu.com/item/%E4%BE%A7%E9%94%8B%E7%94%A8%E7%AC%94/878327)
   - 用途：技法比较、中锋对比

### 二级扩展

- 提按
- 蚕头燕尾
- 外拓
- 骨力
- 笔势

## 二、书法家人物库

### 一级优先

1. 王羲之
   - 推荐来源：[王羲之_维基百科](https://zh.wikipedia.org/zh-cn/%E7%8E%8B%E7%BE%B2%E4%B9%8B)
   - 推荐用途：人物详情、代表作关联、东晋行书体系

2. 颜真卿
   - 推荐来源：[颜真卿_维基百科](https://zh.wikipedia.org/zh-cn/%E9%A1%8F%E7%9C%9F%E5%8D%BF)
   - 推荐用途：颜体定义来源、唐代楷书人物主线

3. 欧阳询
   - 推荐来源：[欧阳询_维基百科](https://zh.wikipedia.org/wiki/%E6%AC%A7%E9%98%B3%E8%AF%A2)
   - 推荐用途：初唐楷书代表、欧体相关问答

4. 柳公权
   - 推荐来源：[柳公权_维基百科](https://zh.wikipedia.org/zh-cn/%E6%9F%B3%E5%85%AC%E6%AC%8A)
   - 推荐用途：柳体相关问答、与颜体对比

5. 赵孟頫
   - 推荐来源：[赵孟頫_维基百科](https://zh.wikipedia.org/zh-cn/%E8%B5%B5%E5%AD%9F%E9%A0%AB)
   - 推荐用途：元代书法、赵体相关问答

### 二级扩展

- 王献之
- 褚遂良
- 怀素
- 张旭

## 三、作品库

### 一级优先

1. 兰亭集序
   - 推荐来源：[兰亭序_故宫博物院](https://www.dpm.org.cn/lemmas/242565.html)
   - 补充来源：[《王羲之<兰亭序>神龙本》_故宫博物院](https://www.dpm.org.cn/journal_detail/239217.html)
   - 推荐用途：王羲之代表作、行书经典、背景知识

2. 多宝塔碑
   - 推荐来源：[宋拓唐颜真卿书多宝塔感应碑册_故宫博物院](https://www.dpm.org.cn/collection/impres/261924.html)
   - 补充来源：[多宝塔碑_维基百科](https://zh.wikipedia.org/wiki/%E5%A4%9A%E5%AF%B6%E5%A1%94%E7%A2%91)
   - 推荐用途：颜真卿早期楷书、颜体入门

3. 祭侄文稿
   - 推荐来源：[祭侄文稿_维基百科](https://zh.wikipedia.org/zh-cn/%E7%A5%AD%E5%A7%AA%E6%96%87%E7%A8%BF)
   - 推荐用途：颜真卿行书、情感书写、经典名作

4. 颜勤礼碑
   - 推荐来源：[颜勤礼_维基百科](https://zh.wikipedia.org/zh-hans/%E9%A2%9C%E5%8B%A4%E7%A4%BC)
   - 推荐用途：晚期颜体特征、楷书代表作品

### 二级扩展

- 十七帖
- 快雪时晴帖
- 玄秘塔碑
- 神策军碑

## 四、背景知识库

### 一级优先

1. 中国书法史总览
   - 推荐来源：[中国书法史_维基百科](https://zh.wikipedia.org/wiki/%E4%B8%AD%E5%9B%BD%E4%B9%A6%E6%B3%95%E5%8F%B2)
   - 用途：总述型背景材料、分时期摘要

2. 魏晋书法
   - 推荐来源：[魏晋书法_百度百科](https://baike.baidu.com/item/%E9%AD%8F%E6%99%8B%E4%B9%A6%E6%B3%95/3126244)
   - 用途：东晋人物与行书背景

3. 东晋书法世家与书体发展
   - 推荐来源：[《中国书法史》：东晋的书法世家](https://k.sina.cn/article_5877221821_15e4f49bd02001azpd.html)
   - 用途：人物谱系、时代背景

4. 中国书法发展概述
   - 推荐来源：[新华网：中国书法追溯](https://www.news.cn/book/20230207/a4a3e3b8029f4166a18b1abe5ba3ed0e/c.html)
   - 用途：通俗化背景语料、答辩展示材料

## 五、建议入库顺序

### 第一批必须入库

- 术语：颜体、楷书、行书、中锋、藏锋、侧锋
- 人物：王羲之、颜真卿、欧阳询、柳公权、赵孟頫
- 作品：兰亭集序、多宝塔碑、祭侄文稿、颜勤礼碑
- 背景：东晋书法、唐代楷书、中国书法史总览

### 第二批增强

- 补充更多作品与人物关系
- 增加中英术语别名
- 增加作品释文和收藏信息
- 增加风格比较材料，如颜体 vs 柳体

## 六、建议整理格式

### 结构化实体

适合直接整理为：

- `terms.json`
- `calligraphers.json`
- `works.json`
- `eras.json`
- `styles.json`

### 长文本知识

适合整理为：

- `background/*.md`
- `work_notes/*.md`
- `person_notes/*.md`

然后通过导入流程写入：

- `knowledge_documents`
- `knowledge_chunks`

## 七、一个最小可用样本规模

用于第一版 RAG，建议至少准备：

- 10 条术语
- 5 条书法家
- 5 条作品
- 10 段背景知识

这批数据就已经足够支持：

- 基础问答
- 术语标准化
- 作品检索
- 书法家介绍
- 简单知识图谱展示

## 八、后续建议

- 正式入库前做一次人工清洗，统一译名和字段格式
- 博物馆页面优先保留原始链接，方便做 citations
- 对维基和百科类资料，优先提炼事实性字段，不直接整段照搬
- 对作品类资料额外补充 `current_collection`、`image_url`、`authenticity`
