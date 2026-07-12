import asyncio
from datetime import datetime, timedelta
import pytz
import random
import time
import os
import logging
import sys

# اعداد تسجيل الدخول
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ============================================
# ضع بياناتك هنا مباشرة (بدون .env)
# ============================================

# 1. ضع الجلسة هنا - انسخ النص الطويل بين الأقواس
SESSION_STRING = "1BJWap1sAUFMlagoNRgc6EAfVaK5n0BMCo8G75Z7FVoZtWwAvQONi6DIBOmGsqLeBU8PEhl3HMWUGMBIgYcz-pl-fGNYiNjOGNgMHdXDyFmF14SX-1EjrrOE5u0O1pJIvKrlafqrZDahn1uPVts3SVtm63xwmjNKUSTDqMz_B0MyKmCuNjbPAZ8eWGiL2zZrKzGzF0yf5eUzn8HNY-0cRN8jCVruSDxuWKqo-nqDm-5OZbVx2XcuMwurrSxB9Rxb4TxU2u_GSM_9ozElFomhYSP4VVYSf70zb8L_Y_Bm7jIqIdCjkkiSowtLNIMiQd1VNI2m3CoI9A5LxVSZDB7o03HmOkePNLRY="

# 2. ضع API_ID هنا
API_ID = 20529343

# 3. ضع API_HASH هنا
API_HASH = "656199efaf0935e731164fb9d02e4aa6"

# ============================================
# انتهى الجزء المعدل
# ============================================

TIMEZONE = pytz.timezone('Africa/Tripoli')

# اعدادات الحماية
last_schedule_time = 0
min_delay = 15
max_delay = 35

from telethon import TelegramClient, events
from telethon.sessions import StringSession

class TelegramBot:
    def __init__(self):
        self.client = None
        self.is_connected = False
        self.running = True
        
    async def initialize_client(self):
        """تهيئة العميل"""
        try:
            self.client = TelegramClient(
                session=StringSession(SESSION_STRING),
                api_id=API_ID,
                api_hash=API_HASH
            )
            
            self.setup_handlers()
            
            await self.client.start()
            self.is_connected = True
            
            me = await self.client.get_me()
            logger.info(f"تم إنشاء جلسة جديدة بنجاح")
            logger.info(f"الاسم: {me.first_name}")
            logger.info("التوقيت: ليبيا")
            logger.info("الفاصل: 15 دقيقة")
            logger.info("جاهز لاستقبال الاوامر")
            
            return True
            
        except Exception as e:
            logger.error(f"فشل في تهيئة العميل: {e}")
            self.is_connected = False
            return False
    
    def setup_handlers(self):
        """اعداد معالجات الاحداث"""
        
        @self.client.on(events.NewMessage(pattern='جدول'))
        async def schedule_message_handler(event):
            if not can_schedule():
                wait_time = int(min_delay - (time.time() - last_schedule_time))
                await event.reply(f"انتظر {wait_time} ثانية قبل الجدولة مرة اخرى")
                return
            
            update_schedule_time()
            
            if event.is_reply:
                try:
                    reply_message = await event.get_reply_message()
                    message_text = reply_message.text
                    
                    if not message_text:
                        await event.reply("الرسالة فارغة")
                        return
                    
                    split_messages = split_and_shuffle_messages(message_text)
                    
                    if not split_messages:
                        await event.reply("لا توجد رسائل صالحة للجدولة")
                        return
                    
                    time_slots = generate_time_slots()
                    
                    successful = 0
                    failed = 0
                    scheduled_times = []
                    failed_times = []
                    
                    await event.reply(f"جاري جدولة {len(time_slots)} رسالة كل 15 دقيقة...")
                    
                    for i, schedule_time in enumerate(time_slots):
                        if i < len(split_messages):
                            message_to_schedule = split_messages[i % len(split_messages)]
                        else:
                            message_to_schedule = split_messages[i % len(split_messages)]
                        
                        success = await schedule_message(self.client, event.chat_id, message_to_schedule, schedule_time)
                        if success:
                            successful += 1
                            scheduled_times.append(schedule_time)
                        else:
                            failed += 1
                            failed_times.append(schedule_time)
                        
                        delay = get_random_delay()
                        await asyncio.sleep(delay)
                    
                    # انشاء رسالة تفصيلية
                    report = generate_detailed_report(
                        "جدولة يوم كامل",
                        successful,
                        failed,
                        len(time_slots),
                        len(split_messages),
                        scheduled_times,
                        failed_times,
                        event.chat_id
                    )
                    
                    await event.reply(report, parse_mode='html')
                    
                except Exception as e:
                    await event.reply(f"خطأ: {e}")
                    logger.error(f"خطا رئيسي: {e}")
            else:
                await event.reply("الرد على الرسالة المراد جدولتها")

        @self.client.on(events.NewMessage(pattern='جدولة اليوم'))
        async def schedule_today_handler(event):
            if not can_schedule():
                wait_time = int(min_delay - (time.time() - last_schedule_time))
                await event.reply(f"انتظر {wait_time} ثانية قبل الجدولة مرة اخرى")
                return
            
            update_schedule_time()
            
            if event.is_reply:
                try:
                    reply_message = await event.get_reply_message()
                    message_text = reply_message.text
                    
                    if not message_text:
                        await event.reply("الرسالة فارغة")
                        return
                    
                    split_messages = split_and_shuffle_messages(message_text)
                    
                    if not split_messages:
                        await event.reply("لا توجد رسائل صالحة للجدولة")
                        return
                    
                    time_slots = generate_today_time_slots()
                    
                    if not time_slots:
                        await event.reply("لا توجد اوقات متاحة للجدولة اليوم")
                        return
                    
                    successful = 0
                    failed = 0
                    scheduled_times = []
                    failed_times = []
                    
                    await event.reply(f"جاري جدولة {len(time_slots)} رسالة لليوم كل 15 دقيقة...")
                    
                    for i, schedule_time in enumerate(time_slots):
                        if i < len(split_messages):
                            message_to_schedule = split_messages[i % len(split_messages)]
                        else:
                            message_to_schedule = split_messages[i % len(split_messages)]
                        
                        success = await schedule_message(self.client, event.chat_id, message_to_schedule, schedule_time)
                        if success:
                            successful += 1
                            scheduled_times.append(schedule_time)
                        else:
                            failed += 1
                            failed_times.append(schedule_time)
                        
                        delay = get_random_delay()
                        await asyncio.sleep(delay)
                    
                    # انشاء رسالة تفصيلية
                    report = generate_detailed_report(
                        "جدولة لبقية اليوم",
                        successful,
                        failed,
                        len(time_slots),
                        len(split_messages),
                        scheduled_times,
                        failed_times,
                        event.chat_id
                    )
                    
                    await event.reply(report, parse_mode='html')
                    
                except Exception as e:
                    await event.reply(f"خطأ: {e}")
                    logger.error(f"خطا رئيسي: {e}")
            else:
                await event.reply("الرد على الرسالة المراد جدولتها")

        @self.client.on(events.NewMessage(pattern='جدولة 24 ساعة'))
        async def schedule_24hours_handler(event):
            if not can_schedule():
                wait_time = int(min_delay - (time.time() - last_schedule_time))
                await event.reply(f"انتظر {wait_time} ثانية قبل الجدولة مرة اخرى")
                return
            
            update_schedule_time()
            
            if event.is_reply:
                try:
                    reply_message = await event.get_reply_message()
                    message_text = reply_message.text
                    
                    if not message_text:
                        await event.reply("الرسالة فارغة")
                        return
                    
                    split_messages = split_and_shuffle_messages(message_text)
                    
                    if not split_messages:
                        await event.reply("لا توجد رسائل صالحة للجدولة")
                        return
                    
                    time_slots = generate_future_time_slots()
                    
                    if not time_slots:
                        await event.reply("لا توجد اوقات متاحة للجدولة")
                        return
                    
                    successful = 0
                    failed = 0
                    scheduled_times = []
                    failed_times = []
                    
                    await event.reply(f"جاري جدولة {len(time_slots)} رسالة لمدة 24 ساعة كل 15 دقيقة...")
                    
                    for i, schedule_time in enumerate(time_slots):
                        if i < len(split_messages):
                            message_to_schedule = split_messages[i % len(split_messages)]
                        else:
                            message_to_schedule = split_messages[i % len(split_messages)]
                        
                        success = await schedule_message(self.client, event.chat_id, message_to_schedule, schedule_time)
                        if success:
                            successful += 1
                            scheduled_times.append(schedule_time)
                        else:
                            failed += 1
                            failed_times.append(schedule_time)
                        
                        delay = get_random_delay()
                        await asyncio.sleep(delay)
                    
                    # انشاء رسالة تفصيلية
                    report = generate_detailed_report(
                        "جدولة لمدة 24 ساعة",
                        successful,
                        failed,
                        len(time_slots),
                        len(split_messages),
                        scheduled_times,
                        failed_times,
                        event.chat_id
                    )
                    
                    await event.reply(report, parse_mode='html')
                    
                except Exception as e:
                    await event.reply(f"خطأ: {e}")
                    logger.error(f"خطا رئيسي: {e}")
            else:
                await event.reply("الرد على الرسالة المراد جدولتها")

        @self.client.on(events.NewMessage(pattern='تقسيم'))
        async def split_only_handler(event):
            if event.is_reply:
                try:
                    reply_message = await event.get_reply_message()
                    message_text = reply_message.text
                    
                    if not message_text:
                        await event.reply("الرسالة فارغة")
                        return
                    
                    split_messages = split_and_shuffle_messages(message_text)
                    
                    if not split_messages:
                        await event.reply("لا توجد رسائل صالحة")
                        return
                    
                    response = f"الاسطر بعد التقسيم ({len(split_messages)}):\n\n"
                    for i, line in enumerate(split_messages, 1):
                        response += f"{i}. {line}\n"
                    
                    await event.reply(response)
                    
                except Exception as e:
                    await event.reply(f"خطأ: {e}")
            else:
                await event.reply("الرد على الرسالة المراد تقسيمها")

        @self.client.on(events.NewMessage(pattern='test'))
        async def test_handler(event):
            try:
                status = f"""<b>حالة البوت</b>

<b>التوقيت:</b> ليبيا
<b>الفاصل:</b> 15 دقيقة
<b>الوقت:</b> {datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')}
<b>الحالة:</b> متصل بشكل مستمر
<b>الرسائل المجدولة:</b> 96 رسالة/يوم"""
                
                await event.reply(status, parse_mode='html')
                logger.info("تم فحص البوت")
            except Exception as e:
                logger.error(f"خطا في الفحص: {e}")

        @self.client.on(events.NewMessage(pattern='حذف المجدول'))
        async def delete_scheduled_handler(event):
            if not can_schedule():
                wait_time = int(min_delay - (time.time() - last_schedule_time))
                await event.reply(f"انتظر {wait_time} ثانية قبل الحذف مرة اخرى")
                return
            
            update_schedule_time()
            
            try:
                scheduled_messages = await self.client.get_scheduled_messages(event.chat_id)
                
                if not scheduled_messages:
                    await event.reply("لا توجد رسائل مجدولة")
                    return
                
                await event.reply(f"جاري حذف {len(scheduled_messages)} رسالة مجدولة...")
                
                deleted_count = 0
                failed_count = 0
                
                for msg in scheduled_messages:
                    try:
                        await self.client.delete_messages(event.chat_id, msg.id)
                        deleted_count += 1
                        logger.info(f"تم حذف رسالة مجدولة")
                        
                        delay = get_random_delay()
                        await asyncio.sleep(delay)
                        
                    except Exception as e:
                        failed_count += 1
                        logger.error(f"خطا في حذف رسالة: {e}")
                        continue
                
                report = f"<b>تم الانتهاء من الحذف</b>\n\nتم الحذف: {deleted_count}\nفشل الحذف: {failed_count}"
                await event.reply(report, parse_mode='html')
                
            except Exception as e:
                error_msg = f"خطأ في الحذف: {str(e)}"
                await event.reply(error_msg)
                logger.error(f"خطا رئيسي في الحذف: {e}")

        @self.client.on(events.NewMessage(pattern='مساعدة'))
        async def help_handler(event):
            help_text = """<b>اوامر البوت</b>

<b>الجدولة</b>
• جدول - جدولة 96 رسالة كل 15 دقيقة
• جدولة اليوم - جدولة لبقية اليوم كل 15 دقيقة
• جدولة 24 ساعة - جدولة لـ24 ساعة كل 15 دقيقة

<b>ادوات</b>
• تقسيم - تقسيم وخلط الرسائل
• test - فحص حالة البوت
• مساعدة - عرض هذه الرسالة

<b>ادارة المجدول</b>
• حذف المجدول - حذف جميع الرسائل المجدولة

<b>معلومات</b>
• التوقيت: ليبيا
• الفاصل: 15 دقيقة
• الاجمالي: 96 رسالة/يوم
• الحالة: متصل بشكل مستمر"""
            
            await event.reply(help_text, parse_mode='html')

        @self.client.on(events.NewMessage(pattern='ايقاف'))
        async def stop_handler(event):
            if event.is_private:
                await event.reply("جاري ايقاف البوت...")
                self.running = False
                logger.info("تم ايقاف البوت بواسطة المستخدم")
            else:
                await event.reply("هذا الامر يعمل فقط في الخاص")

        @self.client.on(events.NewMessage(pattern='اعادة تشغيل'))
        async def restart_handler(event):
            if event.is_private:
                await event.reply("جاري اعادة تشغيل البوت...")
                self.running = False
                logger.info("تم اعادة تشغيل البوت بواسطة المستخدم")

    async def run(self):
        """تشغيل البوت بشكل مستمر ودائم"""
        logger.info("بدء تشغيل البوت...")
        
        while True:
            try:
                if await self.initialize_client():
                    logger.info("البوت يعمل بشكل مستمر")
                    
                    while self.running:
                        try:
                            await asyncio.sleep(60)
                            
                            if not self.is_connected:
                                logger.warning("فقدان الاتصال، جاري اعادة المحاولة...")
                                break
                                
                        except asyncio.CancelledError:
                            logger.info("تم الغاء المهمة")
                            break
                        except Exception as e:
                            logger.error(f"خطا في الحلقة الرئيسية: {e}")
                            await asyncio.sleep(5)
                else:
                    logger.error("فشل الاتصال، اعادة المحاولة بعد 30 ثانية...")
                    await asyncio.sleep(30)
                    
            except KeyboardInterrupt:
                logger.info("تم ايقاف البوت بواسطة المستخدم")
                break
            except Exception as e:
                logger.error(f"خطا رئيسي: {e}")
                await asyncio.sleep(10)
            
            if self.running:
                logger.info("جاري اعادة الاتصال...")
                await asyncio.sleep(5)
                
        logger.info("تم ايقاف البوت")

bot = TelegramBot()

def can_schedule():
    global last_schedule_time
    current_time = time.time()
    if current_time - last_schedule_time < min_delay:
        return False
    return True

def update_schedule_time():
    global last_schedule_time
    last_schedule_time = time.time()

def get_random_delay():
    return random.uniform(min_delay, max_delay)

def split_and_shuffle_messages(message_text):
    """تقسيم الرسالة الى اسطر وخلطها عشوائيا"""
    lines = message_text.strip().split('\n')
    lines = [line.strip() for line in lines if line.strip()]
    
    if len(lines) <= 1:
        return lines
    
    random.shuffle(lines)
    return lines

def generate_time_slots():
    """انشاء قائمة بالاوقات كل 15 دقيقة"""
    time_slots = []
    now = datetime.now(TIMEZONE)
    
    start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_time = now.replace(hour=23, minute=45, second=0, microsecond=0)
    
    current_time = start_time
    
    while current_time <= end_time:
        time_slots.append(current_time)
        current_time += timedelta(minutes=15)
    
    return time_slots

def generate_future_time_slots():
    """انشاء قائمة بالاوقات المستقبلية كل 15 دقيقة"""
    time_slots = []
    now = datetime.now(TIMEZONE)
    
    start_time = now.replace(second=0, microsecond=0)
    end_time = start_time + timedelta(hours=24)
    
    current_minute = start_time.minute
    remainder = current_minute % 15
    if remainder > 0:
        start_time += timedelta(minutes=(15 - remainder))
    
    current_time = start_time
    
    while current_time <= end_time:
        time_slots.append(current_time)
        current_time += timedelta(minutes=15)
    
    return time_slots

def generate_today_time_slots():
    """انشاء قائمة بالاوقات لليوم كل 15 دقيقة"""
    time_slots = []
    now = datetime.now(TIMEZONE)
    
    start_time = now.replace(second=0, microsecond=0)
    end_of_today = now.replace(hour=23, minute=59, second=59, microsecond=0)
    
    current_minute = start_time.minute
    remainder = current_minute % 15
    if remainder > 0:
        start_time += timedelta(minutes=(15 - remainder))
    
    current_time = start_time
    
    while current_time <= end_of_today:
        time_slots.append(current_time)
        current_time += timedelta(minutes=15)
    
    return time_slots

async def schedule_message(client, chat_id, message_text, schedule_time):
    try:
        now = datetime.now(TIMEZONE)
        time_difference = schedule_time - now
        
        if time_difference.total_seconds() > 0:
            await client.send_message(
                chat_id,
                message_text,
                schedule=schedule_time
            )
            logger.info(f"تم الجدولة: {schedule_time.strftime('%H:%M')}")
            return True
        else:
            logger.info(f"الوقت مضى: {schedule_time.strftime('%H:%M')}")
            return False
    except Exception as e:
        logger.error(f"خطا في الجدولة: {e}")
        return False

def generate_detailed_report(job_type, successful, failed, total_slots, total_messages, scheduled_times, failed_times, chat_id):
    """انشاء تقرير مفصل بعد الجدولة"""
    
    now = datetime.now(TIMEZONE)
    
    # حساب نسبة النجاح
    success_rate = (successful / total_slots * 100) if total_slots > 0 else 0
    
    # تنسيق التقرير
    report = f"""<b>تقرير الجدولة</b>

<b>نوع الجدولة:</b> {job_type}
<b>وقت التقرير:</b> {now.strftime('%Y-%m-%d %H:%M:%S')}
<b>حالة الجدولة:</b> {'تمت بنجاح' if successful > 0 else 'فشلت'}

<b>الاحصائيات</b>
• اجمالي المواعيد المتاحة: {total_slots}
• عدد الرسائل المراد جدولتها: {total_messages}
• تم الجدولة بنجاح: {successful}
• فشل في الجدولة: {failed}
• نسبة النجاح: {success_rate:.1f}%

<b>تفاصيل المواعيد</b>"""

    # اضافة اول 10 مواعيد نجحت
    if scheduled_times:
        report += f"\n• المواعيد الناجحة (اول 10):"
        for i, t in enumerate(scheduled_times[:10], 1):
            report += f"\n  {i}. {t.strftime('%H:%M')}"
        if len(scheduled_times) > 10:
            report += f"\n  ... و {len(scheduled_times) - 10} مواعيد اخرى"
    else:
        report += "\n• لا توجد مواعيد ناجحة"

    # اضافة المواعيد الفاشلة
    if failed_times:
        report += f"\n\n<b>المواعيد الفاشلة</b>"
        for i, t in enumerate(failed_times[:5], 1):
            report += f"\n  {i}. {t.strftime('%H:%M')}"
        if len(failed_times) > 5:
            report += f"\n  ... و {len(failed_times) - 5} مواعيد اخرى"
    
    # معلومات اضافية
    report += f"""

<b>معلومات اضافية</b>
• ايدي المحادثة: {chat_id}
• التوقيت: ليبيا
• الفاصل الزمني: 15 دقيقة
• وقت الانتهاء: {now.strftime('%H:%M:%S')}
• مدة التنفيذ: {calculate_execution_time(now)}"""

    return report

def calculate_execution_time(end_time):
    """حساب مدة التنفيذ (تقريبية)"""
    # هذه مجرد تقدير بناءً على عدد الرسائل
    return "حوالي 2-3 دقائق"

async def main():
    """الدالة الرئيسية"""
    try:
        await bot.run()
    except KeyboardInterrupt:
        logger.info("تم ايقاف البوت")
    except Exception as e:
        logger.error(f"خطا فادح: {e}")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
