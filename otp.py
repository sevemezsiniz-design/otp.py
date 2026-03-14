import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telethon import TelegramClient, events
import os
import sys
import re
import signal

# ========== KONFİGÜRASYON ==========
# Telegram Bot Token
BOT_TOKEN = "8714176193:AAG92471G0yeOY-inQbqyBiT9ODtxQUOe68"

# Userbot için API bilgileri
API_ID = 37084908
API_HASH = "cd19e6488ba6bb624a2b4e66f1321bd1"
SESSION_NAME = "userbot_session.session"

# Kanal linkleri
HEDEF_KANAL_LINK = "https://t.me/+HtrHsyHQRkVjOGM0"  # 1. kaynak kanal
IKINCI_KANAL_LINK = "https://t.me/+6jUMgsaod6QxMDRl"  # 2. kaynak kanal (güncellendi)
HEDEF_KANALIM_LINK = "https://t.me/+xeR8gaC6u-xlNmE0"  # Mesajların iletileceği kanal

# TXT dosya yolu
DOSYA_YOLU = "SMSNumbers - 2026-03-10T163919.436 (1).txt"

# ========== LOG AYARLARI ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== TELEGRAM BOT SINIFI ==========
class OtpBot:
    def __init__(self, token):
        self.token = token
        self.application = None
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start komutu - Hoşgeldin mesajı ve callback butonu"""
        keyboard = [
            [InlineKeyboardButton("📱 OTP ÇEK", callback_data="otp_cek")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🤖 *Sevemezsiniz OTP Botuna Hoşgeldiniz!*\n\n"
            "OTP çekmek için aşağıdaki butona tıklayın.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Callback butonlarını yönet"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "otp_cek":
            # Ülke seçim butonları
            keyboard = [
                [InlineKeyboardButton("🇩🇪 Almanya", callback_data="ulke_almanya")],
                [InlineKeyboardButton("🔙 Geri", callback_data="geri")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "🌍 *Lütfen ülke seçiniz:*\n\n"
                "Aşağıdaki butonlardan birini seçin.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        elif query.data == "ulke_almanya":
            # Almanya seçildi - SMS dosyasını gönder
            try:
                if os.path.exists(DOSYA_YOLU):
                    with open(DOSYA_YOLU, 'rb') as file:
                        # Önce dosyayı gönder
                        await query.message.reply_document(
                            document=file,
                            filename="Almanya_SMS_Numaraları.txt",
                            caption="🇩🇪 *Almanya SMS Numaraları*\n\nDosya başarıyla yüklendi.",
                            parse_mode='Markdown'
                        )
                        
                        # Sonra talimat mesajını gönder
                        talimat_mesaji = (
                            "*📋 İŞLEM TALİMATLARI:*\n\n"
                            "1️⃣ *Bir OTP seç*\n"
                            "2️⃣ *WhatsApp'ta işlem yap*\n"
                            "3️⃣ *Kanalımıza katılın:*\n"
                            "   https://t.me/+xeR8gaC6u-xlNmE0\n"
                            "4️⃣ *Mesajı bekleyin*\n\n"
                            "✅ İşlem tamamlandığında size bildirilecektir."
                        )
                        
                        await query.message.reply_text(
                            talimat_mesaji,
                            parse_mode='Markdown'
                        )
                        
                        # Geri dönüş butonu
                        keyboard = [[InlineKeyboardButton("🔙 Ana Menü", callback_data="geri")]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        
                        await query.message.reply_text(
                            "Ana menüye dönmek için butona tıklayın:",
                            reply_markup=reply_markup
                        )
                else:
                    await query.edit_message_text(
                        "❌ *Dosya bulunamadı!*\nLütfen yöneticiyle iletişime geçin.",
                        parse_mode='Markdown'
                    )
            except Exception as e:
                logger.error(f"Dosya gönderme hatası: {e}")
                await query.edit_message_text(
                    f"❌ *Hata oluştu:* {str(e)}",
                    parse_mode='Markdown'
                )
                
        elif query.data == "geri":
            # Ana menüye dön
            keyboard = [
                [InlineKeyboardButton("📱 OTP ÇEK", callback_data="otp_cek")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "🤖 *Sevemezsiniz OTP Botuna Hoşgeldiniz!*\n\n"
                "OTP çekmek için aşağıdaki butona tıklayın.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
    
    def setup(self):
        """Bot komutlarını ve callback handler'ları ayarla"""
        self.application = Application.builder().token(self.token).build()
        
        # Handler'ları ekle
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CallbackQueryHandler(self.button_handler))
        
        return self.application

# ========== USERBOT SINIFI ==========
class MesajUserbot:
    def __init__(self, api_id, api_hash, session_name):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.client = None
        self.running = True
        self.hedef_kanal = None  # 1. kaynak kanal
        self.ikinci_kanal = None  # 2. kaynak kanal
        self.hedef_kanalim = None  # Silme işlemi yapılacak kanal
        
    async def start(self):
        """Userbot'u başlat ve kanallara katıl"""
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        await self.client.start()
        
        # Kullanıcı bilgisi
        me = await self.client.get_me()
        logger.info(f"Userbot giriş yaptı: {me.first_name} (@{me.username or 'None'})")
        
        # Kanallara katıl
        kanallar = []
        
        try:
            # 1. kaynak kanala katıl
            if HEDEF_KANAL_LINK:
                self.hedef_kanal = await self.client.get_entity(HEDEF_KANAL_LINK)
                kanallar.append(self.hedef_kanal)
                logger.info(f"1. kaynak kanala katılındı: {HEDEF_KANAL_LINK}")
        except Exception as e:
            logger.error(f"1. kanala katılma hatası: {e}")
        
        try:
            # 2. kaynak kanala katıl
            if IKINCI_KANAL_LINK:
                self.ikinci_kanal = await self.client.get_entity(IKINCI_KANAL_LINK)
                kanallar.append(self.ikinci_kanal)
                logger.info(f"2. kaynak kanala katılındı: {IKINCI_KANAL_LINK}")
        except Exception as e:
            logger.error(f"2. kanala katılma hatası: {e}")
        
        try:
            # Kendi kanalımıza katıl (mesaj iletilecek ve silinecek kanal)
            if HEDEF_KANALIM_LINK:
                self.hedef_kanalim = await self.client.get_entity(HEDEF_KANALIM_LINK)
                logger.info(f"Kendi kanalımıza katılındı: {HEDEF_KANALIM_LINK}")
        except Exception as e:
            logger.error(f"Hedef kanala katılma hatası: {e}")
        
        if not kanallar:
            logger.error("Hiçbir kaynak kanala katılamadı!")
            return
        
        # Kaynak kanallardan mesajları dinle
        @self.client.on(events.NewMessage(chats=kanallar))
        async def handler(event):
            try:
                # "000-000" formatındaki kodu bul
                pattern = r'\b\d{3}-\d{3}\b'
                mesaj_text = event.message.text or ""
                kodlar = re.findall(pattern, mesaj_text)
                kod_bilgisi = f"\n🔢 **Kod:** {kodlar[0]}" if kodlar else ""
                
                # Mesajı kendi kanalına ilet
                mesaj_icerik = f"📨 *Yeni Mesaj İletildi:*\n\n{mesaj_text}{kod_bilgisi}"
                
                # Eğer mesajda callback butonu varsa onu da yakala
                if event.message.reply_markup:
                    mesaj_icerik += "\n\n*🔘 Callback Butonları:*\n"
                    
                    # Buton metinlerini ve callback datalarını ekle
                    try:
                        for row in event.message.reply_markup.rows:
                            for button in row.buttons:
                                if hasattr(button, 'text'):
                                    mesaj_icerik += f"\n▪️ {button.text}"
                                    if hasattr(button, 'data'):
                                        # Callback data içinde 000-000 ara
                                        data_str = button.data.decode() if isinstance(button.data, bytes) else str(button.data)
                                        data_kodlar = re.findall(pattern, data_str)
                                        if data_kodlar:
                                            mesaj_icerik += f" (📌 {data_kodlar[0]})"
                    except:
                        pass
                
                if self.hedef_kanalim:
                    await self.client.send_message(
                        self.hedef_kanalim,
                        mesaj_icerik,
                        parse_mode='Markdown'
                    )
                    logger.info(f"Mesaj iletildi: {mesaj_text[:50] if mesaj_text else 'İçerik yok'}...")
                
            except Exception as e:
                logger.error(f"Mesaj iletme hatası: {e}")
    
    async def kanal_mesajlarini_sil(self):
        """Hedef kanaldaki tüm mesajları 2 dakikada bir siler"""
        while self.running:
            try:
                if self.hedef_kanalim:
                    logger.info("Kanal mesajları siliniyor...")
                    silinen_sayi = 0
                    
                    # Kanalın mesaj geçmişini al
                    async for message in self.client.iter_messages(self.hedef_kanalim):
                        try:
                            await message.delete()
                            silinen_sayi += 1
                            # Rate limit'e takılmamak için kısa bekleme
                            await asyncio.sleep(0.5)
                        except Exception as e:
                            logger.error(f"Mesaj silinirken hata: {e}")
                    
                    logger.info(f"Toplam {silinen_sayi} mesaj silindi.")
                else:
                    logger.warning("Kanal bulunamadı, silme işlemi atlanıyor.")
                    
            except Exception as e:
                logger.error(f"Silme döngüsünde hata: {e}")
            
            # 2 dakika (120 saniye) bekle
            await asyncio.sleep(120)
    
    async def run(self):
        """Userbot'u çalıştır ve periyodik silme görevini başlat"""
        logger.info("Mesaj dinleme ve periyodik silme başlatıldı...")
        
        # Silme görevini arka planda başlat
        asyncio.create_task(self.kanal_mesajlarini_sil())
        
        # Ana görev: mesajları dinlemeye devam et
        await self.client.run_until_disconnected()
    
    async def stop(self):
        """Userbot'u durdur"""
        self.running = False
        if self.client:
            await self.client.disconnect()
            logger.info("Userbot durduruldu")

# ========== ANA FONKSİYON ==========
async def main():
    """Ana fonksiyon - hem botu hem userbot'u başlat"""
    
    # 1. Normal botu oluştur
    otp_bot = OtpBot(BOT_TOKEN)
    bot_app = otp_bot.setup()
    
    # 2. Userbot'u oluştur
    userbot = MesajUserbot(API_ID, API_HASH, SESSION_NAME)
    
    # Bot'u başlat (polling ile)
    logger.info("Bot başlatılıyor...")
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling()
    
    # Userbot'u başlat
    await userbot.start()
    
    logger.info("✅ Sistem başarıyla başlatıldı!")
    
    # Sinyal yakalayıcı
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(bot_app, userbot)))
    
    try:
        # Userbot'u çalıştır
        await userbot.run()
    except Exception as e:
        logger.error(f"Userbot hatası: {e}")
    finally:
        await shutdown(bot_app, userbot)

async def shutdown(bot_app, userbot):
    """Güvenli kapatma"""
    logger.info("Sistem kapatılıyor...")
    await bot_app.updater.stop()
    await bot_app.stop()
    await bot_app.shutdown()
    await userbot.stop()
    logger.info("Sistem kapatıldı")
    sys.exit(0)

# ========== PROGRAMI BAŞLAT ==========
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program kullanıcı tarafından durduruldu")
    except Exception as e:
        logger.error(f"Beklenmeyen hata: {e}")
