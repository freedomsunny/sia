default = {
    "GET": ["admin", "service_ocmdb", "_member_", "user"],
    "POST": ["admin", "service_ocmdb", "_member_", "user"],
    "PUT": ["admin", "service_ocmdb", "_member_", "user"],
    "DELETE": ["admin", "service_ocmdb", "_member_", "user"],
}

policy = {
    "/user/syncpwd$": {},
    "/auth_code": {},
    "/user/checkexist": {},
    "/user/reset_password": {},
    "/user/adduser": {},
    "/test/sayhello": {},
    "/user/verifyuser": {},
    "/sms_auth_code": {}
}
