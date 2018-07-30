<?php
error_reporting(0);
header('X-XSS-Protection: 0');
?>

<h1>Ref-XSS Test Example Page</h1>

<p><i>xss-example is a example site for ref-xss scanners.</i></p>

<a href="non-xss.php">non-xss</a>
// Not dynamic Link, so scanners should not test it.
<br />
<a href="<?php echo 'http://'.$_SERVER['SERVER_NAME'].':8000'.dirname($_SERVER['SCRIPT_NAME']);?>/xss.php?id=123">id</a>
// Dynamic Link, GET method, the output will be shown on the page.
<br />
<a href="<?php echo dirname($_SERVER['SCRIPT_NAME']);?>/index.php?form=search">form</a>
// Dynamic Link, GET method, the output will be used as a value parameter in `input` tag.
<br />
<a href="<?php echo '//'.$_SERVER['SERVER_NAME'].':8000'.dirname($_SERVER['SCRIPT_NAME']);?>/index.php?callback=ajax">callback</a>
// Dynamic Link, GET method, the output will be shown between `script` tags.
<br />
<a href="xss.php?protect1=test">protect1</a>
// Dynamic Link, GET method, the output will be shown on the page by `htmlspecialchars()`.
<br />
<a href="index.php?protect2=test">protect2</a>
// Dynamic Link, GET method, tthe output will be used as a value parameter in `input` tag by `htmlspecialchars()`.

<h2>Login Test</h2>
<form method="post" action="xss.php">
<input type="text" name="user">
<input type="password" name="pass" />
<input type="text" name="code" />
<input type="submit" name="submit" value="login" />
</form>

// Dynamic Link, POST method, the output will be shown on the page.

<h2>Search Test</h2>
<form method="get" action="index.php">
    <input type="text" name="form" value="<?php echo $_GET['form']?>" />
    <input type="text" name="protect2" value="<?php echo htmlspecialchars($_GET['protect2'])?>" />
    <input type="submit" name="submit" value="search" />
</form>

// The output of the value parameter.

<h2>DOM-XSS Test</h2>

<script>
    var a = "<?php echo $_GET['callback']?>";
    eval(location.hash.substr(1));
</script>

<?php echo 'eval(location.hash.substr(1));' ?>

<br />

// DOM-XSS Test, execute code after `#` in url.
