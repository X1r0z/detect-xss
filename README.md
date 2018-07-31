# ref-xss

`get_dynamic_links_url`

bs4 批量获取 a 标签中的 href 并获取动态参数

`get_dynamic_links_form`

bs4 批量获取表单 action 值及 input 标签

`get_dynamic_links_rest`

开发中

`get_output_position`

正则匹配检测动态参数的输出位

1. 直接输出在页面中

2. 输出在标签中

3. 输出在标签的参数中

4. 输出在 JavaScript 中

`inject_xss_payload`

根据输出位组合 payload 测试

1 & 2: `<script>alert(0)</script>`

3: `"onmouseover="alert(0)" />`

4: `test";alert(0);//`

*以上给出的 payload 皆为示例*

## 测试流程

1. 检测是否为动态参数

2. 定位输出点

3. 测试过滤参数

4. 根据信息构造 payload

# xss-example

`xss-example` 是为 `ref-xss scanner` 检测 `XSS` 漏洞的示例站点.

包含多种提交方式, 多种输出点的 `XSS`.

包含简单的 `DOM-XSS`

不同的 URL 表示方式

```
http://www.test.com/xss-example/xss.php?query=test
//www.test.com/xss-example/xss.php?query=test
/xss-example/xss.php?query=test
xss.php?query=test
```
