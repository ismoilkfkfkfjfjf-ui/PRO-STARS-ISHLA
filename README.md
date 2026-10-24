# 🌟 Pro Stars Telegram Bot

Telegram foydalanuvchilariga do'stlarini taklif qilish (referal) orqali **Telegram Stars** ishlash va ularni o'z akkauntiga yoki kanaliga yechib olish imkoniyatini beruvchi professional va yuqori tezlikda ishlovchi Telegram bot.

---

## 🚀 Asosiy Imkoniyatlar

### 👤 Foydalanuvchilar uchun:
* **⭐ Stars ishlash:** Har bir foydalanuvchi uchun alohida referal havola (`https://t.me/ProStarsuzbBot?start=refID`). Bir klik bilan do'stlarga yoki guruhlarga ulashish (Share) tugmasi.
* **⭐ Stars yechish:** 
  * Minimal yechish: **15 ⭐**.
  * Tayyor tezkor tugmalar: `15 ⭐`, `25 ⭐`, `50 ⭐`, `100 ⭐`, `200 ⭐`.
  * Manzil / Username yuborish va avtomatik buyurtma yaratish.
* **👤 Hisobim:** ID, ism, joriy balans, taklif qilingan do'stlar soni va jami yechib olingan Stars statistikasi.
* **📋 So'rovlarim:** Foydalanuvchining barcha yechish so'rovlari holati (⏳ Kutilmoqda, ✅ To'lab berildi, ❌ Rad etildi).
* **📖 Qo'llanma:** Botdan qanday foydalanish, do'stlarni taklif qilish va Stars olish haqida to'liq yo'riqnoma.

### ⚙️ Admin Panel (`/admin` yoki tugma):
* **📊 Kengaytirilgan Statistika:** Jami userlar, bugun qo'shilganlar, umumiy buyurtmalar, kutilayotgan so'rovlar, to'langan Stars miqdori.
* **💰 Referal mukofotini o'zgartirish:** Admin istalgan vaqtda har bir taklif uchun beriladigan Stars sonini (masalan: 1, 2, 5, 10...) o'zgartira oladi.
* **📥 So'rovlarni (Buyurtmalarni) boshqarish:** Yangi yechish so'rovlari darhol adminga keladi. Admin `✅ To'landi` yoki `❌ Rad etish` (sababi bilan) tugmalarini bosishi mumkin. Rad etilganda foydalanuvchiga Stars avtomatik qaytariladi.
* **📢 Majburiy obuna (Kanallar):** Yangi homiy kanal qo'shish va o'chirish. Foydalanuvchi kanallarga a'zo bo'lmaguncha referal mukofoti hisoblanmaydi.
* **✉️ Xabar tarqatish (Broadcast):** Barcha foydalanuvchilarga matn, rasm, video xabarlarni xavfsiz va limitlardan oshmagan holda ommaviy yuborish.
* **👤 User balansi:** Istalgan foydalanuvchi balansiga Stars qo'shish yoki ayirish.

---

## ⚡ Tezkor Ma'lumotlar Bazasi (SQLite WAL Mode)
* `aiosqlite` asynchronous drayveri yordamida **WAL (Write-Ahead Logging)** rejimida ishlaydi.
* `PRAGMA synchronous = NORMAL` va indekslar bilan jihozlangan bo'lib, bir vaqtning o'zida minglab foydalanuvchilar so'rovini qotmasdan qayta ishlaydi.

---

## 🌐 Render.com da 24/7 Bepul Ishga Tushirish Yo'riqnomasi

Bot ichiga o'rnatilgan `keep_alive.py` web serveri mavjud bo'lib, u Render.com ning Web Service talablariga to'liq javob beradi va botni 24/7 uyg'oq saqlash imkonini beradi.

### 1-qadam: GitHub ga yuklash
1. Loyihangizni GitHub da shaxsiy (Private) yoki ochiq (Public) repozitoriy sifatida yuklang:
   ```bash
   git init
   git add .
   git commit -m "Pro Stars Bot initial commit"
   git remote add origin https://github.com/USERNAME/pro-stars-bot.git
   git push -u origin main
   ```

### 2-qadam: Render.com da yangi Web Service yaratish
1. [Render.com](https://render.com) saytiga kiring va ro'yxatdan o'ting.
2. **"New +"** tugmasini bosing va **"Web Service"** ni tanlang.
3. GitHub repozitoriyangizni ulang.
4. Quyidagi parametrlarni to'ldiring:
   - **Name:** `pro-stars-bot` (yoki istalgan nom)
   - **Region:** Frankfurt yoki eng yaqin hudud
   - **Branch:** `main`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`
   - **Instance Type:** `Free`

5. **Environment Variables** (Muhit o'zgaruvchilari) bo'limiga quyidagilarni kiriting:
   - `BOT_TOKEN`: `BOT_TOKENINGIZNI_KIRITING`
   - `ADMINS`: `618430308,8422157752`
   - `DEFAULT_REF_BONUS`: `2`
   - `MIN_WITHDRAW`: `15`
   - `PORT`: `8080`

6. **"Create Web Service"** tugmasini bosing. Loyiha avtomatik build bo'lib, bir necha daqiqada ishga tushadi!

### 3-qadam: 24/7 rejimda uxlatmasdan saqlash (UptimeRobot)
Render.com bepul tarifida veb-sayt 15 daqiqa faolsiz tursa "uxlab" qolishi mumkin. Buni oldini olish uchun:
1. Render tomonidan berilgan URL manzilini nusxalang (masalan: `https://pro-stars-bot.onrender.com`).
2. [UptimeRobot.com](https://uptimerobot.com) bepul saytiga kiring.
3. **"Add New Monitor"** bosing:
   - **Monitor Type:** `HTTP(s)`
   - **Friendly Name:** `Pro Stars Bot`
   - **URL:** `https://pro-stars-bot.onrender.com/health`
   - **Monitoring Interval:** Har `5 daqiqada` (Every 5 minutes)
4. Saqlang! Endi botingiz Render.com da 24/7 uzluksiz ishlaydi.

---

## 💻 Mahalliy Kompyuterda Ishga Tushirish

```bash
# 1. Virtual muhitni faollashtirish
.venv\Scripts\activate   # Windows
# yoki: source .venv/bin/activate  # Linux / Mac

# 2. Kutubxonalarni o'rnatish
pip install -r requirements.txt

# 3. Botni ishga tushirish
python main.py
```
