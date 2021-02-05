import requests
import json
import time

def print_json(json_dict):
    json_formatted_str = json.dumps(json_dict, indent=2)
    print(json_formatted_str)

def list_difference(l1, l2):
    l_diff = [i for i in l1 if i not in l2]
    return l_diff

updates_file_name = "updates.txt"
log_file_name = "logs.txt"
file_name = "id_name.txt"
id_name = []

posted = 0
added = 0
removed = 0

def post_log(log):
    global log_file_name

    f = open(log_file_name, "a")
    f.write(log)
    f.close()
def post_update(update):
    global updates_file_name

    f = open(updates_file_name, "a")
    f.write(update)
    f.close()

def load_id_name():
    global removed_file_name
    global file_name
    global id_name

    f = open(file_name, "r")
    for l in f:
        l = l.split()
        id_name.append([int(l[0]), " ".join(l[1:])])
    f.close()


def add_id_name(id, name):
    global file_name
    global id_name
    global added

    name = " ".join(name.split())

    if name.count(' ') == len(name):
        print("Failed to add new name. Name is empty")
        requests.post(url + "sendMessage", data = {"chat_id": id, "text": "Имя не должно быть пустым"})
        post_log("Unable to add \"" + name + "\" from " + str(id) + " to names. Name is empty\n")
        return

    if [id, name] in id_name:
        print("Failed to add new name. Pair [id, name] already in the list")
        requests.post(url + "sendMessage", data = {"chat_id": id, "text": "В вашей рассылке уже есть такое имя"})
        post_log("Unable to add \"" + name + "\"" + " from " + str(id) + " to names. Name is already in the list\n")
        return

    f = open(file_name, "a")
    f.write(str(id) + " " + str(name) + "\n")
    f.close()

    post_log("Name \"" + name + "\" from " + str(id) + " added to names\n")

    id_name.append([id, name])
    added += 1
    requests.post(url + "sendMessage", data = {"chat_id": id, "text": "Имя спешно добавлено в вашу рассылку"})

def remove_id_name(id, name):
    global removed_file_name
    global id_name
    global removed

    name = " ".join(name.split())

    if name.count(' ') == len(name):
        print("Failed to remove name. Name is empty")
        requests.post(url + "sendMessage", data = {"chat_id": id, "text": "Имя не должно быть пустым"})
        post_log("Unable to remove \"" + name + "\"" + " from " + str(id) + " from names. Name is empty\n")
        return

    if [id, name] not in id_name:
        print("Failed to remove name. Pair [id, name] not in the list")
        requests.post(url + "sendMessage", data = {"chat_id": id, "text": "В вашей рассылке нет такого имени"})
        post_log("Unable to remove \"" + name + "\"" + " from " + str(id) + " from names. Name is not in the list\n")
        return

    id_name.remove([id, name])

    f = open(file_name, "w")
    for idn in id_name:
        f.write(str(idn[0]) + " " + str(idn[1]) + "\n")
    f.close()

    post_log("Name \"" + name + "\" from " + str(id) + " removed from names\n")

    removed += 1
    requests.post(url + "sendMessage", data = {"chat_id": id, "text": "Имя удалено из вашей рассылки"})


TOKEN = "1452934021:AAEahcOavjhnYuJNd4YoT0tNPkvA0f2bKL0"
url = "https://api.telegram.org/bot" + TOKEN + "/"


def send_list(send_to_id):
    s = "Ваша рассылка:\n"
    global id_name
    for i in id_name:
        if i[0] == send_to_id:
            s = s + i[1] + "\n"
    requests.post(url + "sendMessage", data = {"chat_id": send_to_id, "text": s})
    post_log("list sended to " + str(send_to_id) + "\n")


def find(text, link):
    global posted

    need_to_send = dict()
    for idn in id_name:
        if text.count(idn[1].lower()):
            if idn[0] in need_to_send:
                need_to_send[idn[0]].append((idn[1], link))
            else:
                need_to_send[idn[0]] = [(idn[1], link)]
            posted += 1

    for dat in need_to_send:
        s = ""
        for c in need_to_send[dat]:
            s = s + "Найдено упоминание \"" + c[0] + "\" в\n" + c[1] + "\n"
        requests.post(url + "sendMessage", data = {"chat_id": dat, "text": s})
        post_log(s + " sended to " + str(dat) + "\n")

def command(sender_id, text):
    if text.lower().startswith("/add"):
        if len(text) >= 5:
            add_id_name(sender_id, text[4:])
        else:
            print("Failed to add new name. Name is empty")
            post_log("Unable to add name from " + str(id) + ". Name is empty\n")
            requests.post(url + "sendMessage", data = {"chat_id": sender_id, "text": "Имя не должно быть пустым"})

    if text.lower().startswith("/remove"):
        if len(text) >= 8:
            remove_id_name(sender_id, text[7:])
        else:
            print("Failed to remove name. Name is empty")
            post_log("Unable to remove name from " + str(id) + ". Name is empty\n")
            requests.post(url + "sendMessage", data = {"chat_id": sender_id, "text": "Имя не должно быть пустым"})

    if text.lower().startswith("/list"):
        send_list(sender_id)

redirecting_chat_id = -1001427157906
def process_message(msg):
    global bot_chat_id
    global redirecting_chat_id

    if "from" in msg and "text" in msg:
        if msg["text"].startswith("/"):
            command(msg["from"]["id"], msg["text"])

def process_channel_post(post):
    if "text" in post:
        if post["chat"]["id"] == redirecting_chat_id:
            if "entities" in post:
                link = ""
                for ent in post["entities"]:
                    if ent["type"] == "text_link" and ent["url"].startswith("https://t.me/spiski_okrestina/"):
                        link = ent["url"]
                        break
                if link != "":
                    find(post["text"].lower(), link)

def process_update(update):
    if "message" in update:
        process_message(update["message"])
    if "channel_post" in update:
        process_channel_post(update["channel_post"])

updates_offset = 0
no_updates_cnt = 0
def get_messages():
    global updates_offset
    global no_updates_cnt
    global posted
    global added
    global removed

    updates = requests.get(url + "getUpdates", data = {"offset": updates_offset}).json()
    post_update(str(updates) + "\n")
    if not updates["ok"]:
        print("Failed to get updates")
        return

    updates = updates["result"]
    if len(updates):
        post_log(str(len(updates)) + " new updates\n")
        if no_updates_cnt > 0:
            print()
            no_updates_cnt = 0
        print(len(updates), "new updates")

        posted = added = removed = 0

        for upd in updates:
            process_update(upd)

        print("Posted:", posted)
        print("New names:", added)
        print("Names removed:", removed)

        post_log("Posted: " + str(posted) + "\n" +
                 "New names: " + str(added) + "\n" +
                 "Names removed: " + str(removed) + "\n")

        updates_offset = updates[-1]["update_id"] + 1
    else:
        no_updates_cnt += 1
        print("No new updates x", no_updates_cnt, sep = "", end = "\r")


print("Loading names")
load_id_name()
print("Names count:", len(id_name))
print("Started")
while True:
    get_messages()
    time.sleep(10)