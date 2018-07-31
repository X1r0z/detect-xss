<?php
error_reporting(0);
header('X-XSS-Protection: 0');

echo 'id:'.'<b>'.$_GET['id'].'</b> ';
echo 'username:'.$_POST['user'].' ';
echo 'password:'.$_POST['pass'].' ';
echo 'code:'.htmlspecialchars($_POST['code']).' ';
echo 'protect1:'.htmlspecialchars($_GET['protect1']).' ';
echo 'protect2:'.htmlspecialchars($_GET['protect2']).' ';
echo 'api:'.end(explode('/',$_SERVER['PHP_SELF'])).' ';
?>
