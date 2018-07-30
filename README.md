# ref-xss

开发中

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