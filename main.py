import discord
from discord.ext import commands
from discord.ui import Button, View
from keep_alive import keep_alive
import datetime
import json

# ตั้งค่า intents
intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.message_content = True

# ตั้งค่าคำสั่งบอท
bot = commands.Bot(command_prefix="!", intents=intents)

# ตั้งค่า Channel ID
BUTTON_CHANNEL_ID = 1363887392250921232  # ห้องที่ใช้แสดงปุ่ม
CHECKIN_CHANNEL_ID = 1370867548542865428  # ห้องเช็คอิน
CHECKOUT_CHANNEL_ID = 1370867568122007652  # ห้องเช็คเอาท์

# เก็บข้อมูลเข้าออกเวรและเวลาทำงานสะสม
attendance = {}  # เช็คอินอยู่หรือไม่
work_log = {}  # เก็บเวลาทำงานสะสม

keep_alive()
# ฟังก์ชั่นบันทึกข้อมูลลงไฟล์
def save_data():
    with open("attendance.json", "w") as f:
        json.dump({"attendance": attendance, "work_log": work_log}, f)


# ฟังก์ชั่นโหลดข้อมูลจากไฟล์
def load_data():
    global attendance, work_log
    try:
        with open("attendance.json", "r") as f:
            data = json.load(f)
            attendance = data.get("attendance", {})
            work_log = data.get("work_log", {})
    except FileNotFoundError:
        # หากไม่มีไฟล์จะเริ่มต้นข้อมูลใหม่
        attendance = {}
        work_log = {}


# สร้าง View พร้อมปุ่ม
class AttendanceView(View):

    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(
            Button(label="เข้า-ออกเวร",
                   style=discord.ButtonStyle.primary,
                   custom_id="attendance_button"))


# Event เมื่อบอทพร้อมใช้งาน
@bot.event
async def on_ready():
    load_data()  # โหลดข้อมูลเมื่อบอทเริ่มทำงาน
    print(f"Run bot Discord Complete {bot.user}")


# Event เมื่อมีคนกดปุ่ม
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.data["custom_id"] == "attendance_button":
        user_id = str(interaction.user.id)
        now = datetime.datetime.now()
        formatted_time = now.strftime("%Y-%m-%d %H:%M:%S")

        if user_id in attendance:
            time_in = datetime.datetime.fromisoformat(
                attendance[user_id]["time_in"])
            hours_worked = (now - time_in).total_seconds() / 3600

            # เพิ่มชั่วโมงทำงานสะสม
            if user_id in work_log:
                work_log[user_id]["total_hours"] += hours_worked
            else:
                work_log[user_id] = {
                    "name": interaction.user.name,
                    "total_hours": hours_worked
                }

            total_hours = work_log[user_id]["total_hours"]
            del attendance[user_id]  # ออกจากเวร

            # ส่งข้อความไปห้องเช็คเอาท์
            channel = bot.get_channel(CHECKOUT_CHANNEL_ID)
            if channel:
                await channel.send(
                    f"{interaction.user.mention} เช็คเอาท์เวลา {formatted_time} "
                    f"ทำงาน {hours_worked:.2f} ชั่วโมง | สะสม {total_hours:.2f} ชั่วโมง"
                )

            await interaction.response.send_message("✅ ออกจากเวรเรียบร้อย",
                                                    ephemeral=True)

            # บันทึกข้อมูลทุกครั้งหลังจากการเช็คเอาท์
            save_data()

        else:
            # เช็คอิน
            attendance[user_id] = {
                "name": interaction.user.name,
                "time_in": now.isoformat()  # แปลง datetime เป็น string
            }

            # ส่งข้อความไปห้องเช็คอิน
            channel = bot.get_channel(CHECKIN_CHANNEL_ID)
            if channel:
                await channel.send(
                    f"{interaction.user.mention} เช็คอินเวลา {formatted_time}")

            await interaction.response.send_message("✅ เข้าเวรเรียบร้อย",
                                                    ephemeral=True)

            # บันทึกข้อมูลทุกครั้งหลังจากการเช็คอิน
            save_data()


# เริ่มต้นบอท (ใส่ Token จริงของคุณแทนด้านล่าง)
bot.run(
    'MTM3MDg1ODAzMDY0MzgxMDM0NA.Gqq7Jd.AkkaPJiqv7P5lLWvuk2T0PDK1lJkGle-dlqCAI')
