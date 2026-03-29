"""
Protobuf message builders and decoders for Lark API.
Extracted from LarkAgentX/builder/proto.py.
Uses protobuf objects directly (no protobuf_to_dict dependency).
"""
import re
import proto_pb2 as PB
from lark_utils import generate_request_cid


def _strip_html(s):
    return re.sub(r"<[^>]+>", "", s) if s else ""


def build_send_message_proto(text, request_id, chat_id):
    cid_1 = generate_request_cid()
    cid_2 = generate_request_cid()

    pkt = PB.Packet()
    pkt.payloadType = 1
    pkt.cmd = 5
    pkt.cid = request_id

    msg = PB.PutMessageRequest()
    msg.type = 4
    msg.chatId = chat_id
    msg.cid = cid_1
    msg.isNotified = 1
    msg.version = 1

    msg.content.richText.elementIds.append(cid_2)
    msg.content.richText.innerText = text
    msg.content.richText.elements.dictionary[cid_2].tag = 1

    tp = PB.TextProperty()
    tp.content = str(text)
    msg.content.richText.elements.dictionary[cid_2].property = tp.SerializeToString()

    pkt.payload = msg.SerializeToString()
    return pkt


def build_search_proto(request_id, query):
    session = generate_request_cid()
    pkt = PB.Packet()
    pkt.payloadType = 1
    pkt.cmd = 11021
    pkt.cid = request_id

    req = PB.UniversalSearchRequest()
    req.header.searchSession = session
    req.header.sessionSeqId = 1
    req.header.query = query
    req.header.searchContext.tagName = "SMART_SEARCH"

    e1 = PB.EntityItem()
    e1.type = 1

    e2 = PB.EntityItem()
    e2.type = 2
    e2.filter.CopyFrom(PB.EntityItem.EntityFilter())

    e3 = PB.EntityItem()
    e3.type = 3
    e3.filter.groupChatFilter.CopyFrom(PB.GroupChatFilter())

    e4 = PB.EntityItem()
    e4.type = 10
    e4.filter.CopyFrom(PB.EntityItem.EntityFilter())

    req.header.searchContext.entityItems.extend([e1, e2, e3, e4])
    req.header.searchContext.commonFilter.includeOuterTenant = 1
    req.header.searchContext.sourceKey = "messenger"
    req.header.locale = "zh_CN"
    req.header.extraParam.CopyFrom(PB.SearchExtraParam())

    pkt.payload = req.SerializeToString()
    return pkt


def decode_search_response(data):
    pkt = PB.Packet()
    pkt.ParseFromString(data)
    results = []
    if pkt.HasField("payload"):
        resp = PB.UniversalSearchResponse()
        resp.ParseFromString(pkt.payload)
        for r in resp.results:
            t = r.type
            title = _strip_html(r.titleHighlighted) if r.HasField("titleHighlighted") else ""
            if t == 1:
                results.append({"type": "user", "id": r.id, "title": title})
            elif t == 3:
                results.append({"type": "group", "id": r.id, "title": title})
    return results


def build_create_chat_proto(request_id, user_id):
    pkt = PB.Packet()
    pkt.payloadType = 1
    pkt.cmd = 13
    pkt.cid = request_id

    req = PB.PutChatRequest()
    req.type = 1
    req.chatterIds.append(user_id)
    pkt.payload = req.SerializeToString()
    return pkt


def decode_create_chat_response(data):
    pkt = PB.Packet()
    pkt.ParseFromString(data)
    if pkt.HasField("payload"):
        resp = PB.PutChatResponse()
        resp.ParseFromString(pkt.payload)
        if resp.HasField("chat"):
            return resp.chat.id
    return None


def build_get_user_name_proto(request_id, user_id, chat_id):
    pkt = PB.Packet()
    pkt.payloadType = 1
    pkt.cmd = 5023
    pkt.cid = request_id

    req = PB.GetUserInfoRequest()
    req.userId = int(user_id)
    req.chatId = int(chat_id)
    req.userType = 1

    pkt.payload = req.SerializeToString()
    return pkt


def decode_user_name_response(data):
    pkt = PB.Packet()
    pkt.ParseFromString(data)
    if pkt.HasField("payload"):
        info = PB.UserInfo()
        info.ParseFromString(pkt.payload)
        detail = info.userInfoDetail.detail
        name = detail.nickname.decode("utf-8") if detail.HasField("nickname") else None
        for loc in detail.locales:
            if loc.HasField("key_string") and loc.key_string == "zh_cn":
                name = loc.translation
                break
        return name
    return None


def build_get_group_name_proto(request_id, chat_id):
    pkt = PB.Packet()
    pkt.payloadType = 1
    pkt.cmd = 64
    pkt.cid = request_id

    req = PB.GetGroupInfoRequest()
    req.chatId = str(chat_id)

    pkt.payload = req.SerializeToString()
    return pkt


def decode_group_name_response(data):
    pkt = PB.Packet()
    pkt.ParseFromString(data)
    if pkt.HasField("payload"):
        info = PB.UserInfo()
        info.ParseFromString(pkt.payload)
        detail = info.userInfoDetail.detail
        name = None
        if detail.HasField("nickname1"):
            name = detail.nickname1
        elif detail.HasField("nickname4"):
            name = detail.nickname4
        if isinstance(name, bytes):
            name = name.decode("utf-8")
        return name
    return None


# ── WebSocket message decoding ────────────────────────────

def extract_packet_sid(ws_message):
    """Extract packet sid from a WebSocket Frame for ACK."""
    frame = PB.Frame()
    frame.ParseFromString(ws_message)
    pkt = PB.Packet()
    pkt.ParseFromString(frame.payload)
    return pkt.sid


def build_ack_frame(packet_sid):
    """Build an ACK frame to send back over WebSocket."""
    import time as _time
    payload = PB.Packet()
    payload.cmd = 1
    payload.payloadType = 1
    payload.sid = packet_sid

    frame = PB.Frame()
    current = int(_time.time() * 1000)
    frame.seqid = current
    frame.logid = current
    frame.service = 1
    frame.method = 1

    entry = PB.ExtendedEntry()
    entry.key = "x-request-time"
    entry.value = f"{current}000"
    frame.headers.append(entry)
    frame.payloadType = "pb"
    frame.payload = payload.SerializeToString()
    return frame.SerializeToString()


def decode_ws_message(ws_message):
    """Decode a WebSocket push message. Returns dict or None.

    Returns: {from_id, chat_id, chat_type, content, message_type} or None
    """
    frame = PB.Frame()
    frame.ParseFromString(ws_message)
    pkt = PB.Packet()
    pkt.ParseFromString(frame.payload)
    if not pkt.HasField("payload"):
        return None

    push = PB.PushMessagesRequest()
    push.ParseFromString(pkt.payload)

    for _key, msg in push.messages.items():
        result = {
            "from_id": msg.fromId if msg.HasField("fromId") else None,
            "chat_id": msg.chatId if msg.HasField("chatId") else None,
            "chat_type": msg.chatType if msg.HasField("chatType") else 0,
            "message_type": msg.type if msg.HasField("type") else 0,
            "content": None,
        }
        # type 4 = TEXT
        if result["message_type"] == 4 and msg.HasField("content"):
            text_content = PB.TextContent()
            text_content.ParseFromString(msg.content)
            if text_content.HasField("richText"):
                parts = []
                elems = text_content.richText.elements.dictionary
                # Sort element ids to preserve order
                try:
                    sorted_keys = sorted(elems.keys(), key=lambda k: int(k))
                except ValueError:
                    sorted_keys = elems.keys()
                for eid in sorted_keys:
                    elem = elems[eid]
                    if elem.HasField("property"):
                        tp = PB.TextProperty()
                        tp.ParseFromString(elem.property)
                        if tp.HasField("content"):
                            parts.append(tp.content)
                result["content"] = "".join(parts)
        return result
    return None
