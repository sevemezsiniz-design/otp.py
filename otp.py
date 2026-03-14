import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telethon import TelegramClient, events
import os
import signal
import sys

# ========== KONFİGÜRASYON ==========
# Telegram Bot Token
BOT_TOKEN = "8714176193:AAG92471G0yeOY-inQbqyBiT9ODtxQUOe68"

# Userbot için API bilgileri
API_ID = 37084908
API_HASH = "cd19e6488ba6bb624a2b4e66f1321bd1"
SESSION_NAME = "userbot_session.session"

# Kanal linkleri
HEDEF_KANAL_LINK = "https://t.me/+HtrHsyHQRkVjOGM0"  # Mesajların alınacağı kanal
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
        
    async def start(self):
        """Userbot'u başlat ve kanallara katıl"""
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        await self.client.start()
        
        # Kullanıcı bilgisi
        me = await self.client.get_me()
        logger.info(f"Userbot giriş yaptı: {me.first_name} (@{me.username or 'None'})")
        
        # Kanallara katıl
        try:
            # Hedef kanala katıl (mesaj alınacak kanal)
            self.hedef_kanal = await self.client.get_entity(HEDEF_KANAL_LINK)
            logger.info(f"Hedef kanala katılındı: {HEDEF_KANAL_LINK}")
            
            # Kendi kanalımıza katıl (mesaj iletilecek kanal)
            self.hedef_kanalim = await self.client.get_entity(HEDEF_KANALIM_LINK)
            logger.info(f"Kendi kanalımıza katılındı: {HEDEF_KANALIM_LINK}")
            
        except Exception as e:
            logger.error(f"Kanala katılma hatası: {e}")
        
        # Mesaj dinleyiciyi kur
        @self.client.on(events.NewMessage(chats=self.hedef_kanal))
        async def handler(event):
            try:
                # Mesajı kendi kanalına ilet
                await self.client.send_message(
                    self.hedef_kanalim,
                    f"📨 *Yeni Mesaj İletildi:*\n\n{event.message.text}",
                    parse_mode='Markdown'
                )
                logger.info(f"Mesaj iletildi: {event.message.text[:50]}...")
            except Exception as e:
                logger.error(f"Mesaj iletme hatası: {e}")
    
    async def run(self):
        """Userbot'u çalıştır"""
        logger.info("Mesaj dinleme başlatıldı...")
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
    
    # Bot'u başlat (polling ile) - ayrı bir task olarak
    logger.info("Bot başlatılıyor...")
    
    # Bot polling'ini başlat
    await bot_app.initialize()
    await bot_app.start()
    
    # Userbot'u başlat
    await userbot.start()
    
    # Bot'u polling modunda çalıştır
    await bot_app.updater.start_polling()
    
    logger.info("✅ Sistem başarıyla başlatıldı!")
    
    try:
        # Userbot'u çalıştır (burada kalır)
        await userbot.run()
    except KeyboardInterrupt:
        logger.info("Kullanıcı tarafından durduruldu")
    finally:
        # Temizlik işlemleri
        await bot_app.updater.stop()
        await bot_app.stop()
        await bot_app.shutdown()
        await userbot.stop()

# ========== PROGRAMI BAŞLAT ==========
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program kullanıcı tarafından durduruldu")
    except Exception as e:
        logger.error(f"Beklenmeyen hata: {e}")
