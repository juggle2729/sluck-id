--[[
    Most code copy from json.lua
--]]

require "cjson"
require("string")

local msg = {
    Payload    = nil,
    Uuid       = nil,
    Type       = nil,
    Logger     = nil,
    Hostname   = nil,
    Severity   = 6,
    EnvVersion = nil,
    Pid        = nil,
    Timestamp  = nil,
    Fields     = {}
}

function process_message()
    local pok, json = pcall(cjson.decode, read_message("Payload"))
    if not pok then return -1, "Failed to decode JSON." end
    msg.Type = 'json'
    local ts = json["@timestamp"]

    local to_save = {
        ["UserId"] = json.user_id,
        ["Set"] = {["updated_at"] = ts},
        ["Inc"] = {},
        ["Data"] = json
    }
    if to_save.UserId == nil then
        return -1, "no user_id"
    end
    -- modify data here
    if json.type == "register" then
        to_save.Set.created_at = ts
        to_save.Set.aid = json.aid
        to_save.Set.chn = json.chn
        to_save.Set.code = json.code
        to_save.Set.pkg = json.pkg
        if json.inviter_id and json.inviter_id ~= "" then
            to_save.Set.inviter_id = json.inviter_id
        end
    elseif json.type == "login" then
        if json.logon == false then
            to_save.Set.first_login_at = ts
        end
    elseif json.type == "win" then
        msg.Type = "win"
        if msg.first_win_cost then
            to_save.Set["win.first_recharged"] = 0
            to_save.Set["win.first_payed"] = 0
            to_save.Set["win.first_price"] = tonumber(json.activity_target)
            to_save.Set["win.first_at"] = ts
        end
        to_save.Inc["win.total"] = tonumber(json.activity_target)
        to_save.Inc["gain"] = to_save.Inc["win.total"]
        to_save.Inc["win.count"] = 1
        to_save.Set["win.last_at"] = ts
    elseif json.type == "create_coupon" or json.type == "use_coupon" or json.type == "expire_coupon" then
        to_save.Inc = nil
        to_save.CouponId = json.coupon_id
        to_save.Set.updated_at = nil
        to_save.Set.user_id = json.user_id
        msg.Type = "coupon"
        if json.type == "create_coupon" then
            to_save.Set["from"] = json.from
            to_save.Set["price"] = tonumber(json.price)
            to_save.Set["created_at"] = ts
            to_save.Set["status"] = 1
        elseif json.type == "use_coupon" then
            to_save.Set["status"] = 2
            to_save.Set["target"] = json.target
            to_save.Set["use_at"] = ts
            to_save.Set["price"] = tonumber(json.price)
        elseif json.type == "expire_coupon" then
            to_save.Set["status"] = 4
            to_save.Set["expire_at"] = ts
        end
    elseif json.type == "recharge" then
        msg.Type = "recharge"
        to_save.Inc["recharge."..json.channel] = tonumber(json.price)
        to_save.Inc["recharge.total"] = tonumber(json.price)
        to_save.Set["recharge.last_at"] = ts
        to_save.Inc["recharge.count"] = 1
        to_save.Inc["gain"] = 0 - tonumber(json.price)
    elseif json.type == "pay" then
        to_save.Inc["pay.count"] = 1
        to_save.Inc["pay.total"] = tonumber(json.price)
        to_save.Set["pay.last_at"] = ts
    elseif json.type == "active" then
        to_save.Set.aid = json.aid
        to_save.Set.chn = json.chn
        to_save.Set.code = json.code
        to_save.Set.pkg = json.pkg
    else
        msg.Type = "droped"
        return -1, "no need type"
    end

    msg.Payload = cjson.encode(to_save)

    if not pcall(inject_message, msg) then
      return -1, "Failed to inject message."
    end

    return 0
end
