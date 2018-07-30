<?php
error_reporting(0);
header('X-XSS-Protection: 0');

echo 'id:'.'<b>'.$_GET['id'].'</b>';
echo '<br / >';

echo 'username:'.$_POST['user'];
echo '<br />';
echo 'password:'.$_POST['pass'];
echo '<br / >';
echo 'code:'.htmlspecialchars($_POST['code']);
echo '<br />';
echo 'protect1'.htmlspecialchars($_GET['protect1']);
?>