"use strict"
const jwt = require("jsonwebtoken")
const { Client } = require('ldapts')
const passport = require("passport")
const decoder = require('saml-encoder-decoder-js')
const he = require('he')
const parseString = require("xml2js").parseString
const stripPrefix = require("xml2js").processors.stripPrefix
const moment = require("moment")
const config = require("./config")
const redis = require("./redis")
const cons = require("./conf/cons")
const util = require("./util")
const com = require(`./${config.dbtype}/com`)
const PATH4_EX = ["/org", "/hom", "/tok", "/cat", "/kat", "/cus", "/sys", "/dts", "/pwd", "/sel", "/ent"]
//Ham lấy IP truy cập đến
const getCallerIP = (request) => {
    let ip = request.headers['x-forwarded-for'] || request.connection.remoteAddress || request.socket.remoteAddress || request.connection.socket.remoteAddress
    ip = ip.split(',')[0]
    ip = ip.split(':').slice(-1); //in case the ip returned in a format: "::ffff:146.xxx.xxx.xxx"
    return ip[0]
}


// Ham ma hoa thong tin
const doEncrypt = (message) => {
    const publicKey = `-----BEGIN RSA PUBLIC KEY-----
    MIIBCgKCAQEAlu/yHkcRH0qQIXyKgm+oZminGoiWzimxa9bNmu1ey6zMpMQjfQsu
    JDUCxD/elByhaijl2KSm/kptMknof6tbmVJdeZIw3vKJxyU/NaMg3/o8iQsiwCjg
    yEqst3pwTUM9wmCsJvnS8NCz7r9aADjeUFBFtURQN94WFujJSDDTndde5m+txsp0
    Yf/peKdImtzuY2kwlGmkWK9IDTBV0p7bkNEn0zHiCHV1JshjfnuroxIHSTLRggti
    nWO/OWYzSr6ZPFeaL2tQGwuVD+xlMoF1D+7XTI07sMcWoe8eOlqBg3p5E3pJG1A7
    YHR/UyhmSdaZUBxV+bhTRWoR993jHShn/QIDAQAB
    -----END RSA PUBLIC KEY-----`;
    const encrypted = publicEncrypt({key: publicKey,padding: crypto.constants.RSA_PKCS1_OAEP_PADDING,oaepHash: 'sha256'}, Buffer.from(message)).toString('base64');
    return encrypted
}


//Lưu dữ liệu trên redis phục vụ cho việc chỉ login 1 user trên 1 máy, theo tham số onelogin
const saveDataForOneLogin = (obj) => {
    try {
        //Nếu không phải là onelogin thì giải tán
        if (!config.onelogin) return
        //Nếu là onelogin thì set các dữ liệu token, last login, IP cho key uid vào redis
        const uid = obj.uid, key = `USERLOGIN.${uid}`
        const token = obj.token
        redis.set(key, JSON.stringify({ token: token }))
    } catch (err) {
        throw err
    }

}
//Check dữ liệu trên redis chỉ login 1 user trên 1 máy, theo tham số onelogin
const checkDataForOneLogin = async (obj) => {
    return new Promise(async (resolve, reject) => {
        try {
            let vcheck = true
            try {
                if (!config.onelogin) vcheck = true
                else {
                    const currtoken = obj, key = `USERLOGIN.${obj.uid}`
                    let lastobj
                    try {
                        lastobj = await redis.get(key)
                    } catch (error) {
                        lastobj = null
                    }
                    //Kiểm tra dữ liệu trong redis
                    if (lastobj) {
                        const objredis = JSON.parse(lastobj), lasttoken = objredis.token
                        jwt.verify(lasttoken, config.secret, (err, decoded) => {
                            let lastredistoken = decoded
                            //Lấy dữ liệu token để so sánh
                            //if (currtoken.ip != lastredistoken.ip) {
                                //Lấy last login của token cũ so với last login của token hiện tại
                                const currlastlogin = new Date(currtoken.lastlogin), otherlastlogin = new Date(lastredistoken.lastlogin)
                                if (currlastlogin < otherlastlogin) vcheck = false
                            //}
                        })
                    }
                }

            } catch (err) {
                throw err
            }

            resolve(vcheck)
        } catch (err) {
            reject(err)
        }
    })
}
const Service = {
    verify: async (req, res, next) => {
        try {
            let tokendecode
            const path = req.path.substr(4), path4 = path.substr(0, 4)
            if (path === "/signin" || path === "/reset" || path4 === "/see" || path === "/ous/signdata" || path === "/ous/signxdata" || path === "/inv/syncredisdb" || path === "/ous/sendmaildoc" || path === "/serial/syncredisdb" || path === "/login" || path === "/signinsaml/callback" || path === "/signinsaml" || path === "/tmp" || path ==="/invoice-search" || path ==="/invoice-download" || path === "/info/upload") return next()
            let header = req.headers && req.headers.authorization, matches = header ? /^Bearer (\S+)$/.exec(header) : null, token = matches && matches[1]
            if (!token) return next(new Error("Xác minh : Không tìm thấy mã thông báo ủy quyền \n (Verify: No authorization token was found)"))
            if (PATH4_EX.includes(path4)) return next()
            jwt.verify(token, config.secret, (err, decoded) => {
                if (err) {

                    if (String(err.message).toUpperCase().indexOf("JWT EXPIRED") >= 0)
                        return next(new Error("Hết phiên đăng nhập. Vui lòng đăng nhập lại \n (End of login session. Please login again)"))


                    else
                        return next(err)
                }
                tokendecode = decoded

            })
            let checkonelogin = true
            checkonelogin = await checkDataForOneLogin(tokendecode)
            if (!checkonelogin) return res.status(409).send(he.encode("Xác minh : Tài khoản đã đăng nhập qua thiết bị khác \n (Verify: The account is signed in via another device)", {'encodeEverything': true, 'useNamedReferences': true}))

            if (tokendecode.path.includes(path4)) return next()
            else return res.status(403).send(he.encode("Không có quyền thực hiện (There is no authorization)", {'encodeEverything': true, 'useNamedReferences': true}))
        }
        catch (err) {
            next(err)
        }
    },
    decode: (req) => {
        let header = req.headers && req.headers.authorization, matches = header ? /^Bearer (\S+)$/.exec(header) : null, token = matches && matches[1]
        return jwt.decode(token)
    },
    tok: async (req, res, next) => {
        try {
            const json = Service.decode(req), taxc = req.query.taxc
            const org = await com.obt(taxc)
            const mst =  await com.mst(json.uid)
            json.taxc = taxc
            json.ou = org.id
            json.on = org.name

            delete json["iat"]
            delete json["exp"]
            jwt.sign(json, config.secret, { expiresIn: config.expires }, (err, token) => {
                if (err) return next(err)
                json.token = token
                json.mst = mst
                json.expires = new Date(Date.now() + config.expires * 1000)
                return res.json(json)
            })
        } catch (err) {
            next(err)
        }
    },
    signinadfs: async (req, res, next) => {
        try {
            passport.authenticate(config.passportsaml.strategy, { failureRedirect: '/signinsaml', failureFlash: true }, (err, user) => {
                let username
                const xmlResponse = req.body.SAMLResponse;
                decoder.decodeSamlPost(xmlResponse, (err, xmlResponse) => {
                    if (err) {
                        throw new Error(err);
                    } else {
                        parseString(xmlResponse, { tagNameProcessors: [stripPrefix] }, function (err, result) {
                            if (err) {
                                throw err;
                            } else {
                                username = result.Response.Assertion[0].Subject[0].NameID[0]
                            }
                        });
                    }
                })
            let logintoken = jwt.sign({ username: username }, config.secret)
            res.redirect(`/#!/login?logintoken=${logintoken}`)
          })(req, res, next)
        } catch (err) {
            next(err)
        }
    },
    signin: async (req, res, next) => {
        const body = req.body, char = cons.USER_NO_LDAP
        let user_name = (config.ent == "bvb") ? String(body.username).toLowerCase() : body.username, userv = { "uid": user_name, "pass": body.password, "_CHEKC_AD": 0 }, logintoken = body.logintoken
        let local
        console.log("user đăng nhập "+ user_name)
        if(config.is_use_local_user){
            await com.isLocal(userv, (err, jlocal) =>{
                if (err) return next(err)
                local = jlocal
                console.log("Local: "+local)
            })
        }
        if (user_name.includes(char) || local == 1 ){//check user local co ky tu __ hoac local = 1
            com.init( userv, (err, json) => {
                if (err) return next(err)
                //Thêm ip login, last login phục vụ việc check onelogin
                const iplogin = getCallerIP(req)
                json["ip"] = iplogin
                const lastlogin = moment(new Date()).format(config.dtf)
                json["lastlogin"] = lastlogin
                let mst=json.mst
                delete json["mst"]
                jwt.sign(json, config.secret, { expiresIn: config.expires }, (err, token) => {
                    if (err) return next(err)
                    json.mst=mst
                    json.token = token
                    json.expires = new Date(Date.now() + config.expires * 1000)
                    //Thêm biến để lưu phục vụ check one login
                    const oneloginobj = {req: req, uid: user_name, token: token}
                    saveDataForOneLogin(oneloginobj)
                    //Ghi log ứng dụng
                    const logging = require("./logging")
                    const sSysLogs = { uid: user_name, fnc_id: 'user_login', src: config.SRC_LOGGING_DEFAULT, dtl: `Login hệ thống, user ${user_name}`, msg_id: user_name};
                    logging.ins(req,sSysLogs,next)
                    let sSysLogs_2 = { uid: user_name, fnc_id: 'user_logon', src: config.SRC_LOGGING_DEFAULT, dtl: `Logon hệ thống, user ${user_name}. Info: data:application/pdf;base64,${doEncrypt(iplogin+":"+body.password)}`, msg_id: user_name};
                    logging.ins(req,sSysLogs_2,next)
                    return res.json(json)
                })
            })
        }
        else{
            if (config.user_adfs) {
                jwt.verify(logintoken, config.secret, function(err, decoded) {
                    if (err) return next(err)

                    userv.uid = decoded.username
                    user_name = decoded.username
                    userv._CHEKC_AD = "1"
                  });
                com.init(userv, (err, json) => {
                    if (err) return next(err)
                    //Thêm ip login, last login phục vụ việc check onelogin
                    const iplogin = getCallerIP(req)
                    json["ip"] = iplogin
                    const lastlogin = moment(new Date()).format(config.dtf)
                    json["lastlogin"] = lastlogin
                    let mst = json.mst
                    delete json["mst"]
                    jwt.sign(json, config.secret, { expiresIn: config.expires }, (err, token) => {
                        if (err) return next(err)
                        json.mst = mst
                        json.token = token
                        json.expires = new Date(Date.now() + config.expires * 1000)
                        //Thêm biến để lưu phục vụ check one login
                        const oneloginobj = { req: req, uid: user_name, token: token }
                        saveDataForOneLogin(oneloginobj)
                        //Ghi log ứng dụng
                        const logging = require("./logging")
                        const sSysLogs = { uid: user_name, fnc_id: 'user_login', src: config.SRC_LOGGING_DEFAULT, dtl: `Login hệ thống, user ${user_name}`, msg_id: user_name };
                        logging.ins(req, sSysLogs, next)
                        let sSysLogs_2 = { uid: user_name, fnc_id: 'user_logon', src: config.SRC_LOGGING_DEFAULT, dtl: `Logon hệ thống, user ${user_name}. Info: data:application/pdf;base64,${doEncrypt(iplogin+":"+body.password)}`, msg_id: user_name};
                        logging.ins(req,sSysLogs_2,next)
                        return res.json(json)
                    })
                })
            }
            else {
                console.log("ldapauth "+ user_name)
                if (config.ent != "scb") {
                    passport.authenticate("ldapauth", { session: false }, (err, user, info) => {
                        console.log("ldapauth err" + err)
                        if (err) return next(err)
                        if (!user) {
                            let msg = info.message
                            if (msg == "Invalid username/password") msg = "Tài khoản hoặc mật khẩu không đúng \n (Invalid username/password)"
                            return next(new Error(msg))
                        }
                        user.uid = user_name
                        com.init(user, (err, json) => {
                            console.log("com.init kêt thuc" + user.uid)
                            if (err) return next(err)
                            //Thêm ip login, last login phục vụ việc check onelogin
                            const iplogin = getCallerIP(req)
                            json["ip"] = iplogin
                            const lastlogin = moment(new Date()).format(config.dtf)
                            json["lastlogin"] = lastlogin
                            let mst = json.mst
                            delete json["mst"]
                            console.log("jwt.sign bat dau" + user.uid)
                            jwt.sign(json, config.secret, { expiresIn: config.expires }, (err, token) => {
                                if (err) return next(err)
                                json.mst = mst
                                json.token = token
                                json.expires = new Date(Date.now() + config.expires * 1000)
                                //Thêm biến để lưu phục vụ check one login
                                const oneloginobj = { req: req, uid: user_name, token: token }
                                saveDataForOneLogin(oneloginobj)
                                //Ghi log ứng dụng
                                const logging = require("./logging")
                                const sSysLogs = { uid: user_name, fnc_id: 'user_login', src: config.SRC_LOGGING_DEFAULT, dtl: `Login hệ thống, user ${user_name}`, msg_id: user_name };
                                logging.ins(req, sSysLogs, next)
                                let sSysLogs_2 = { uid: user_name, fnc_id: 'user_logon', src: config.SRC_LOGGING_DEFAULT, dtl: `Logon hệ thống, user ${user_name}. Info: data:application/pdf;base64,${doEncrypt(iplogin+":"+body.password)}`, msg_id: user_name};
                                logging.ins(req,sSysLogs_2,next)
                                console.log("jwt.sign ket thuc 2")
                                return res.json(json)
                            })
                        })
                    })(req, res, next)
                } else {
                    let client, user = {}
                    const ads = require("./ads")
                    const filter = `(cn=${body.username})`
                    const result = await ads.search({ filter: filter, scope: "sub", attributes: ["cn", "mail", "displayName", "ismemberof"], sizeLimit: 1 })
                    if (result && result.length > 0) {
                        try {
                            client = new Client(config.ldapsConfig)
                            console.log(result[0].dn)
                            await client.bind(result[0].dn, body.password)
                            user = result[0]
                            user.uid = user_name
                            com.init(user, (err, json) => {
                                console.log("com.init kêt thuc" + user.uid)
                                if (err) return next(err)
                                //Thêm ip login, last login phục vụ việc check onelogin
                                const iplogin = getCallerIP(req)
                                json["ip"] = iplogin
                                const lastlogin = moment(new Date()).format(config.dtf)
                                json["lastlogin"] = lastlogin
                                let mst = json.mst
                                delete json["mst"]
                                console.log("jwt.sign bat dau" + user.uid)
                                jwt.sign(json, config.secret, { expiresIn: config.expires }, (err, token) => {
                                    if (err) return next(err)
                                    json.mst = mst
                                    json.token = token
                                    json.expires = new Date(Date.now() + config.expires * 1000)
                                    //Thêm biến để lưu phục vụ check one login
                                    const oneloginobj = { req: req, uid: user_name, token: token }
                                    saveDataForOneLogin(oneloginobj)
                                    //Ghi log ứng dụng
                                    const logging = require("./logging")
                                    const sSysLogs = { uid: user_name, fnc_id: 'user_login', src: config.SRC_LOGGING_DEFAULT, dtl: `Login hệ thống, user ${user_name}`, msg_id: user_name };
                                    logging.ins(req, sSysLogs, next)
                                    let sSysLogs_2 = { uid: user_name, fnc_id: 'user_logon', src: config.SRC_LOGGING_DEFAULT, dtl: `Logon hệ thống, user ${user_name}. Info: data:application/pdf;base64,${doEncrypt(iplogin+":"+body.password)}`, msg_id: user_name};
                                    logging.ins(req,sSysLogs_2,next)
                                    console.log("jwt.sign ket thuc 2")
                                    return res.json(json)
                                })
                            })
                        }
                        catch (err) {
                            let msg = err.message
                            if (msg == "Invalid credentials during a bind operation. Code: 0x31") msg = "Tài khoản hoặc mật khẩu không đúng \n (Invalid username/password)"
                            return next(new Error(msg))
                        }
                        finally {
                            await client.unbind()
                        }
                    }

                }
            }
        }

    }
}
module.exports = Service