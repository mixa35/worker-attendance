"""Translations for the admin web app. EN and KA (Georgian)."""

from __future__ import annotations

from fastapi import Request

EN: dict[str, str] = {
    # Brand / chrome
    "brand.sub": "Worker Attendance",
    "lang.label": "Language",
    "lang.en": "EN",
    "lang.ka": "ქართული",

    # Nav
    "nav.dashboard": "Dashboard",
    "nav.teams": "Teams",
    "nav.workers": "Workers",
    "nav.leads": "Leads",
    "nav.owner": "Owner",
    "nav.excel": "Excel",
    "footer": "AWARD · Worker Attendance Admin",

    # Common
    "common.name": "Name",
    "common.team": "Team",
    "common.color": "Color",
    "common.actions": "",
    "common.save": "Save",
    "common.cancel": "Cancel",
    "common.add": "Add",
    "common.edit": "Edit",
    "common.delete": "Delete",
    "common.remove": "Remove",
    "common.optional": "optional",
    "common.none_dash": "—",
    "common.yes": "Yes",
    "common.no": "No",
    "common.required": "required",

    # Dashboard
    "dash.title": "Dashboard",
    "dash.lede": "At-a-glance overview of teams, workers, and reporting.",
    "dash.stat.teams": "Teams",
    "dash.stat.active_workers": "Active workers",
    "dash.stat.total_workers": "Total workers",
    "dash.stat.leads": "Leads",
    "dash.owner.title": "Owner",
    "dash.owner.chat_id": "Chat ID",
    "dash.owner.none": "No owner set.",
    "dash.owner.edit": "Edit",
    "dash.excel.title": "Excel report",
    "dash.excel.desc": "Live workbook with one sheet per month, color-coded per team.",
    "dash.excel.download": "Download attendance.xlsx",
    "dash.excel.empty": "No attendance recorded yet — file will appear after the first submission.",
    "dash.quick.title": "Quick actions",
    "dash.quick.teams": "Manage teams — add, rename, recolor, delete",
    "dash.quick.workers": "Manage workers — add, drag between teams, deactivate",
    "dash.quick.leads": "Manage team leads — add or edit when leads change",

    # Teams
    "teams.title": "Teams",
    "teams.lede": "A team is a group of workers managed by one Telegram lead. Each team has a color used in the Excel report.",
    "teams.col.color": "Color",
    "teams.col.active_workers": "Active workers",
    "teams.empty": "No teams yet.",
    "teams.confirm_delete": "Delete team '{name}'?",
    "teams.add_title": "Add team",
    "teams.add_button": "Add team",
    "teams.placeholder.name": "e.g. Foundation crew",

    # Workers
    "workers.title": "Workers",
    "workers.lede": "Active workers appear in the daily Telegram form. Drag a row to move a worker between teams.",
    "workers.tip": "Plan transfers at month boundaries when possible — moving a worker mid-month re-attributes the whole month's record to the new team in the Excel report.",
    "workers.tip_label": "Tip:",
    "workers.col.national_id": "National ID",
    "workers.chip.active": "{n} active",
    "workers.empty_active": "No active workers in this team.",
    "workers.archived": "Archived",
    "workers.btn.deactivate": "Deactivate",
    "workers.btn.deactivate_title": "Hide from daily form, keep history",
    "workers.btn.reactivate": "Reactivate",
    "workers.btn.delete": "Delete",
    "workers.confirm_delete": "Permanently delete '{name}'?\n\nOnly works if this worker has no attendance history. For workers who left, use Deactivate instead.",
    "workers.confirm_delete_archived": "Permanently delete '{name}'?\n\nOnly works if this worker has no attendance history.",
    "workers.create_team_first": "Create a team first.",
    "workers.add_title": "Add worker",
    "workers.placeholder.name": "First Last",
    "workers.placeholder.national_id": "e.g. 01001012345",

    # Leads
    "leads.title": "Team leads",
    "leads.lede": "A lead receives the daily attendance form for their team. Use Edit when a lead is replaced — same row, new chat ID.",
    "leads.col.chat_id": "Telegram chat ID",
    "leads.empty": "No leads yet.",
    "leads.confirm_remove": "Remove this lead?",
    "leads.add_title": "Add lead",
    "leads.add_note": "After saving or editing, the bot's command menus refresh automatically — but the new lead must DM the bot once first to receive forms.",

    # Pending invites
    "pending.title": "Pending invites",
    "pending.lede": "Users who messaged the bot but aren't assigned yet. Pick a team and click Assign.",
    "pending.col.first_seen": "First seen",
    "pending.btn.assign": "Assign",
    "pending.btn.dismiss": "Dismiss",
    "pending.confirm_dismiss": "Dismiss this invitation? The user will need to /start the bot again.",
    "pending.no_team_available": "No teams without a lead — create a team or remove a lead first.",

    # Owner
    "owner.title": "Owner",
    "owner.lede": "The owner receives the monthly Excel summary on day 1 of each month and can request the workbook anytime via /report.",
    "owner.current": "Current owner chat ID",
    "owner.not_set": "not set",

    # Server messages (msg= keys)
    "msg.name_required": "Name is required.",
    "msg.invalid_color": "Color must be a 6-character hex.",
    "msg.team_added": "Team added.",
    "msg.team_updated": "Team updated.",
    "msg.team_deleted": "Team deleted.",
    "msg.team_has_workers": "Cannot delete: team has workers. Move or remove them first.",
    "msg.worker_added": "Worker added.",
    "msg.worker_deleted": "Worker deleted.",
    "msg.worker_deactivated": "Worker deactivated.",
    "msg.worker_reactivated": "Worker reactivated.",
    "msg.worker_moved": "Worker moved.",
    "msg.worker_has_attendance": "Cannot delete: worker has attendance history. Use Deactivate to keep the record intact.",
    "msg.target_team_not_found": "Target team not found.",
    "msg.lead_saved": "Lead saved. Command menus refreshed.",
    "msg.lead_updated": "Lead updated. Command menus refreshed.",
    "msg.lead_removed": "Lead removed.",
    "msg.team_already_has_lead": "This team already has a lead. Edit the existing one instead.",
    "msg.chat_id_conflict": "That chat ID is already used by another lead.",
    "msg.owner_updated": "Owner updated.",
    "msg.pending_dismissed": "Invitation dismissed.",

    # ============ Bot (Telegram) strings ============
    "bot.owner_mode": (
        "Owner mode.\n"
        "/report — get the current attendance.xlsx anytime.\n"
        "(A monthly copy is also sent automatically on the 1st.)"
    ),
    "bot.unknown_user": (
        "Hi! 👋\n\n"
        "You're not assigned to a team yet. The administrator has been notified — "
        "they'll add you shortly.\n\n"
        "Once assigned, you'll receive the daily attendance form here automatically."
    ),
    "bot.owner_pending_notif": (
        "📥 *New unassigned user pinged the bot*\n\n"
        "Name: {name}\n"
        "{handle}"
        "Chat ID: `{chat_id}`\n\n"
        "Open the admin → Leads page to assign them."
    ),
    "bot.help.lead_header": "*Team lead commands:*",
    "bot.help.today": "/today — open today's attendance form",
    "bot.help.today_note": "_(also auto-sent every morning at 08:00 Asia/Tbilisi)_",
    "bot.help.owner_header": "*Owner commands:*",
    "bot.help.report": "/report — get the current attendance.xlsx",
    "bot.help.report_note": "_(also auto-sent on the 1st of each month)_",
    "bot.help.unknown": "You're not registered as a team lead or owner.",
    "bot.help.your_id": "Your chat ID: `{chat_id}`",
    "bot.help.contact_admin": "Send this to the administrator to be added.",
    "bot.help.help_cmd": "/help — show this help",
    "bot.help.start_cmd": "/start — same as /today (lead) or owner info (owner)",
    "bot.form.title": "📋 *{team_name}* — {date}\nTap to toggle, then press *Submit*.",
    "bot.form.submit": "📤 Submit",
    "bot.form.expired": "This form is from another day. Send /today to get a fresh form.",
    "bot.form.not_lead": "You're not registered as a team lead.",
    "bot.form.not_in_form": "Worker is not in this form.",
    "bot.form.saved_alert": "Saved!",
    "bot.submit.confirmation": (
        "✅ Saved for *{team_name}* on *{date}*: "
        "{present} / {total} present.\n\n"
        "Made a mistake? Send /today to re-open and edit (until midnight)."
    ),
    "bot.report.owner_only": "This command is for the owner only.",
    "bot.report.empty": "No attendance data has been recorded yet.",
    "bot.report.caption": "Attendance report (live, as of {timestamp}).",
    "bot.scheduler.monthly_caption": "📊 Attendance report — {year:04d}-{month:02d}",
    "bot.lead.assigned_dm": (
        "✅ You've been assigned as the lead for *{team_name}*.\n\n"
        "You'll receive the daily attendance form every morning at "
        "08:00 (Asia/Tbilisi).\n"
        "Use /today to open it any time."
    ),
    "bot.today.not_lead": "You're not registered as a team lead.",
}

KA: dict[str, str] = {
    # Brand / chrome
    "brand.sub": "თანამშრომელთა აღრიცხვა",
    "lang.label": "ენა",
    "lang.en": "ENG",
    "lang.ka": "ქართული",

    # Nav
    "nav.dashboard": "მთავარი",
    "nav.teams": "ჯგუფები",
    "nav.workers": "თანამშრომლები",
    "nav.leads": "ხელმძღვანელები",
    "nav.owner": "მფლობელი",
    "nav.excel": "Excel",
    "footer": "AWARD · თანამშრომელთა აღრიცხვის პანელი",

    # Common
    "common.name": "სახელი",
    "common.team": "ჯგუფი",
    "common.color": "ფერი",
    "common.actions": "",
    "common.save": "შენახვა",
    "common.cancel": "გაუქმება",
    "common.add": "დამატება",
    "common.edit": "რედაქტირება",
    "common.delete": "წაშლა",
    "common.remove": "წაშლა",
    "common.optional": "არასავალდებულო",
    "common.none_dash": "—",
    "common.yes": "კი",
    "common.no": "არა",
    "common.required": "სავალდებულო",

    # Dashboard
    "dash.title": "მთავარი",
    "dash.lede": "ჯგუფების, თანამშრომლებისა და ანგარიშების მოკლე მიმოხილვა.",
    "dash.stat.teams": "ჯგუფები",
    "dash.stat.active_workers": "აქტიური თანამშრომლები",
    "dash.stat.total_workers": "სულ თანამშრომლები",
    "dash.stat.leads": "ხელმძღვანელები",
    "dash.owner.title": "მფლობელი",
    "dash.owner.chat_id": "Chat ID",
    "dash.owner.none": "მფლობელი არ არის მითითებული.",
    "dash.owner.edit": "რედაქტირება",
    "dash.excel.title": "Excel ანგარიში",
    "dash.excel.desc": "ცოცხალი ფაილი თვეებად, ჯგუფების ფერებით.",
    "dash.excel.download": "attendance.xlsx-ის ჩამოტვირთვა",
    "dash.excel.empty": "ჯერ არცერთი ჩანაწერი არ არის — ფაილი გამოჩნდება პირველი შენახვის შემდეგ.",
    "dash.quick.title": "სწრაფი მოქმედებები",
    "dash.quick.teams": "ჯგუფების მართვა — დამატება, სახელის ცვლილება, ფერის ცვლილება, წაშლა",
    "dash.quick.workers": "თანამშრომლების მართვა — დამატება, გადატანა ჯგუფებს შორის, დეაქტივაცია",
    "dash.quick.leads": "ხელმძღვანელების მართვა — დამატება ან რედაქტირება",

    # Teams
    "teams.title": "ჯგუფები",
    "teams.lede": "ჯგუფი არის თანამშრომელთა გუნდი ერთი Telegram ხელმძღვანელით. თითოეულ ჯგუფს აქვს ფერი Excel-ში.",
    "teams.col.color": "ფერი",
    "teams.col.active_workers": "აქტიური თანამშრომლები",
    "teams.empty": "ჯგუფები ჯერ არ არის.",
    "teams.confirm_delete": "წავშალოთ ჯგუფი '{name}'?",
    "teams.add_title": "ჯგუფის დამატება",
    "teams.add_button": "ჯგუფის დამატება",
    "teams.placeholder.name": "მაგ., ძირითადი ბრიგადა",

    # Workers
    "workers.title": "თანამშრომლები",
    "workers.lede": "აქტიური თანამშრომლები გამოჩნდებიან ყოველდღიურ Telegram ფორმაში. გადაიტანეთ მწკრივი ჯგუფებს შორის.",
    "workers.tip": "შეძლებისდაგვარად გადაიტანეთ თანამშრომლები თვის ბოლოს — შუა თვეში გადატანა მთლიან თვის ჩანაწერს გადაანაწილებს ახალ ჯგუფზე.",
    "workers.tip_label": "მნიშვნელოვანი:",
    "workers.col.national_id": "პირადი №",
    "workers.chip.active": "აქტიური: {n}",
    "workers.empty_active": "ამ ჯგუფში აქტიური თანამშრომლები არ არიან.",
    "workers.archived": "არქივი",
    "workers.btn.deactivate": "დეაქტივაცია",
    "workers.btn.deactivate_title": "მალავს ფორმიდან, ისტორიას ინახავს",
    "workers.btn.reactivate": "გააქტიურება",
    "workers.btn.delete": "წაშლა",
    "workers.confirm_delete": "სამუდამოდ წავშალოთ '{name}'?\n\nმუშაობს მხოლოდ მაშინ, თუ თანამშრომელს არ აქვს დასწრების ისტორია. წასული თანამშრომლისთვის გამოიყენე დეაქტივაცია.",
    "workers.confirm_delete_archived": "სამუდამოდ წავშალოთ '{name}'?\n\nმუშაობს მხოლოდ მაშინ, თუ თანამშრომელს არ აქვს დასწრების ისტორია.",
    "workers.create_team_first": "ჯერ შექმენი ჯგუფი.",
    "workers.add_title": "თანამშრომლის დამატება",
    "workers.placeholder.name": "სახელი გვარი",
    "workers.placeholder.national_id": "მაგ., 01001012345",

    # Leads
    "leads.title": "ჯგუფის ხელმძღვანელები",
    "leads.lede": "ხელმძღვანელი იღებს ყოველდღიურ ფორმას თავისი ჯგუფისთვის. ხელმძღვანელის შეცვლისას გამოიყენე რედაქტირება — იგივე მწკრივი, ახალი chat ID.",
    "leads.col.chat_id": "Telegram ID",
    "leads.empty": "ხელმძღვანელები ჯერ არ არიან.",
    "leads.confirm_remove": "წავშალოთ ეს ხელმძღვანელი?",
    "leads.add_title": "ხელმძღვანელის დამატება",
    "leads.add_note": "შენახვის ან რედაქტირების შემდეგ ბოტის მენიუ ავტომატურად განახლდება — მაგრამ ახალმა ხელმძღვანელმა ჯერ პირადად უნდა მისწეროს ბოტს.",

    # Pending invites
    "pending.title": "მოლოდინში მყოფი მოთხოვნები",
    "pending.lede": "მომხმარებლები, რომლებმაც დაუკავშირდნენ ბოტს, მაგრამ ჯერ არ არიან განაწილებული. აირჩიე ჯგუფი და დააჭირე „დანიშვნა“-ს.",
    "pending.col.first_seen": "პირველი კონტაქტი",
    "pending.btn.assign": "დანიშვნა",
    "pending.btn.dismiss": "გაუქმება",
    "pending.confirm_dismiss": "გავაუქმოთ ეს მოთხოვნა? მომხმარებელს დასჭირდება ბოტთან თავიდან /start-ის გაგზავნა.",
    "pending.no_team_available": "ხელმძღვანელის გარეშე ჯგუფი არ არის — ჯერ შექმენი ჯგუფი ან წაშალე ხელმძღვანელი.",

    # Owner
    "owner.title": "მფლობელი",
    "owner.lede": "მფლობელი თვის 1 რიცხვში იღებს Excel ანგარიშს და ნებისმიერ დროს შეუძლია მოითხოვოს /report ბრძანებით.",
    "owner.current": "მფლობელის Chat ID",
    "owner.not_set": "მითითებული არ არის",

    # Server messages
    "msg.name_required": "სახელი სავალდებულოა.",
    "msg.invalid_color": "ფერი უნდა იყოს 6-სიმბოლოიანი hex.",
    "msg.team_added": "ჯგუფი დაემატა.",
    "msg.team_updated": "ჯგუფი განახლდა.",
    "msg.team_deleted": "ჯგუფი წაიშალა.",
    "msg.team_has_workers": "ვერ წავშლი: ჯგუფში არიან თანამშრომლები. ჯერ გადაიტანე ან წაშალე ისინი.",
    "msg.worker_added": "თანამშრომელი დაემატა.",
    "msg.worker_deleted": "თანამშრომელი წაიშალა.",
    "msg.worker_deactivated": "თანამშრომელი დეაქტივირდა.",
    "msg.worker_reactivated": "თანამშრომელი გააქტიურდა.",
    "msg.worker_moved": "თანამშრომელი გადატანილია.",
    "msg.worker_has_attendance": "ვერ წავშლი: თანამშრომელს აქვს დასწრების ისტორია. გამოიყენე დეაქტივაცია.",
    "msg.target_team_not_found": "ჯგუფი ვერ მოიძებნა.",
    "msg.lead_saved": "ხელმძღვანელი დაემატა. მენიუ განახლდა.",
    "msg.lead_updated": "ხელმძღვანელი განახლდა. მენიუ განახლდა.",
    "msg.lead_removed": "ხელმძღვანელი წაშლილია.",
    "msg.team_already_has_lead": "ამ ჯგუფს უკვე ჰყავს ხელმძღვანელი. ჯერ მოახდინე არსებულის რედაქტირება.",
    "msg.chat_id_conflict": "ეს chat ID უკვე გამოიყენება სხვა ხელმძღვანელის მიერ.",
    "msg.owner_updated": "მფლობელი განახლდა.",
    "msg.pending_dismissed": "მოთხოვნა გაუქმდა.",

    # ============ Bot (Telegram) strings ============
    "bot.owner_mode": (
        "მფლობელის რეჟიმი.\n"
        "/report — მიმდინარე attendance.xlsx ფაილის მიღება.\n"
        "(ყოველი თვის 1-ში ასევე ავტომატურად იგზავნება ასლი.)"
    ),
    "bot.unknown_user": (
        "გამარჯობა! 👋\n\n"
        "თქვენ ჯერ არ ხართ ჯგუფში მითითებული. ადმინისტრატორი ინფორმირებულია — "
        "მალე დაგამატებთ.\n\n"
        "დამატების შემდეგ ყოველდღიური ფორმა აქვე მოვა."
    ),
    "bot.owner_pending_notif": (
        "📥 *ახალი მომხმარებელი დაუკავშირდა ბოტს*\n\n"
        "სახელი: {name}\n"
        "{handle}"
        "Chat ID: `{chat_id}`\n\n"
        "გახსენი ადმინი → ხელმძღვანელები და დანიშნე ჯგუფზე."
    ),
    "bot.help.lead_header": "*ჯგუფის ხელმძღვანელის ბრძანებები:*",
    "bot.help.today": "/today — დღევანდელი დასწრების ფორმის გახსნა",
    "bot.help.today_note": "_(ყოველდღე 08:00-ზე (Asia/Tbilisi) ავტომატურად იგზავნება)_",
    "bot.help.owner_header": "*მფლობელის ბრძანებები:*",
    "bot.help.report": "/report — მიმდინარე attendance.xlsx ფაილის მიღება",
    "bot.help.report_note": "_(თვის 1-ში ავტომატურადაც იგზავნება)_",
    "bot.help.unknown": "თქვენ არ ხართ რეგისტრირებული ხელმძღვანელად ან მფლობელად.",
    "bot.help.your_id": "თქვენი chat ID: `{chat_id}`",
    "bot.help.contact_admin": "გადააგზავნეთ ეს ID ადმინისტრატორთან.",
    "bot.help.help_cmd": "/help — ამ დახმარების ჩვენება",
    "bot.help.start_cmd": "/start — იგივე რაც /today (ხელმძღვანელისთვის) ან მფლობელის ინფო",
    "bot.form.title": "📋 *{team_name}* — {date}\nდააჭირე გადასართავად, შემდეგ — *გაგზავნა*.",
    "bot.form.submit": "📤 გაგზავნა",
    "bot.form.expired": "ეს ფორმა სხვა დღისაა. /today გაგზავნე ახალი ფორმისთვის.",
    "bot.form.not_lead": "თქვენ არ ხართ რეგისტრირებული ჯგუფის ხელმძღვანელად.",
    "bot.form.not_in_form": "ეს თანამშრომელი ფორმაში არ არის.",
    "bot.form.saved_alert": "შენახულია!",
    "bot.submit.confirmation": (
        "✅ შენახულია *{team_name}* — *{date}*: "
        "{present} / {total} დამსწრე.\n\n"
        "შეცდომა გაქვთ? /today-ით ხელახლა გახსენით (24:00-მდე)."
    ),
    "bot.report.owner_only": "ეს ბრძანება მხოლოდ მფლობელისთვისაა.",
    "bot.report.empty": "ჯერ არცერთი ჩანაწერი არ არის.",
    "bot.report.caption": "დასწრების ანგარიში (ცოცხალი, {timestamp}-ით).",
    "bot.scheduler.monthly_caption": "📊 დასწრების ანგარიში — {year:04d}-{month:02d}",
    "bot.lead.assigned_dm": (
        "✅ თქვენ დაინიშნეთ *{team_name}*-ის ხელმძღვანელად.\n\n"
        "ყოველდღე 08:00-ზე (Asia/Tbilisi) მიიღებთ დასწრების ფორმას.\n"
        "/today ბრძანებით ნებისმიერ დროს გახსნით."
    ),
    "bot.today.not_lead": "თქვენ არ ხართ რეგისტრირებული ჯგუფის ხელმძღვანელად.",
}

LANGS = {"en": EN, "ka": KA}


def get_lang(request: Request) -> str:
    lang = request.cookies.get("lang", "en")
    return lang if lang in LANGS else "en"


def make_t(lang: str):
    table = LANGS.get(lang, EN)

    def t(key: str, **kwargs) -> str:
        s = table.get(key) or EN.get(key) or key
        if kwargs:
            try:
                return s.format(**kwargs)
            except (KeyError, IndexError):
                return s
        return s

    return t


def bot_t(key: str, **kwargs) -> str:
    """Translate a bot-side string using the language from settings.bot_lang.

    Imported lazily here to avoid circular imports between bot/* modules.
    """
    from ..config import settings

    return make_t(settings.bot_lang)(key, **kwargs)
