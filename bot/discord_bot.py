import discord
from discord.ext import commands
from discord import app_commands
import logging
import asyncio
from datetime import datetime
import pytz
from config import Config
from google_sheets.manager import GoogleSheetsManager
from mail.email_manager import EmailManager

logger = logging.getLogger(__name__)

class BookingView(discord.ui.View):
    """
    Discord UI View cho booking buttons
    """
    
    def __init__(self, booking_data, sheets_manager, email_manager):
        super().__init__(timeout=None)  # Không timeout
        self.booking_data = booking_data
        self.sheets_manager = sheets_manager
        self.email_manager = email_manager
    
    @discord.ui.button(label='✅ Xác nhận', style=discord.ButtonStyle.success, custom_id='confirm_booking')
    async def confirm_booking(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Xử lý khi admin click nút xác nhận
        """
        try:
            await interaction.response.defer()
            
            # Lấy thông tin admin
            admin_name = interaction.user.display_name
            admin_id = interaction.user.id
            
            logger.info(f"Admin {admin_name} ({admin_id}) confirming booking for {self.booking_data.get('email')}")
            
            # Cập nhật trạng thái trong Google Sheets
            success = self.sheets_manager.update_booking_status(
                self.booking_data.get('rowNumber'),  # Sử dụng rowNumber thay vì row_number
                'confirmed',
                admin_name
            )
            
            if not success:
                await interaction.followup.send("❌ Lỗi khi cập nhật Google Sheets!", ephemeral=True)
                return
            
            # Thêm booking vào Google Calendar
            logger.info(f"Adding booking to Google Calendar:")
            logger.info(f"  - booking_data keys: {list(self.booking_data.keys())}")
            logger.info(f"  - name: {self.booking_data.get('name')}")
            logger.info(f"  - email: {self.booking_data.get('email')}")
            logger.info(f"  - date: {self.booking_data.get('date')}")
            logger.info(f"  - startTime: {self.booking_data.get('startTime')}")
            logger.info(f"  - endTime: {self.booking_data.get('endTime')}")
            logger.info(f"  - room: {self.booking_data.get('room')}")
            logger.info(f"  - phone: {self.booking_data.get('phone')}")
            logger.info(f"  - customerCount: {self.booking_data.get('customerCount')}")
            logger.info(f"  - notes: {self.booking_data.get('notes')}")
            
            event_id = self.sheets_manager.add_to_google_calendar(self.booking_data)
            calendar_created = event_id is not None
            
            if calendar_created:
                logger.info(f"✅ Google Calendar event created successfully: {event_id}")
            else:
                logger.error("❌ Failed to create Google Calendar event")
                logger.error(f"❌ Full booking_data: {self.booking_data}")
            
            # Gửi email xác nhận
            email_sent = self.email_manager.send_confirmation_email(self.booking_data)
            
            # Cập nhật message Discord
            embed = discord.Embed(
                title="✅ Booking đã được xác nhận",
                color=0x00FF00,
                timestamp=datetime.now(pytz.timezone(Config.TIMEZONE))
            )
            
            embed.add_field(name="👤 Khách hàng", value=self.booking_data.get('name'), inline=True)
            embed.add_field(name="📧 Email", value=self.booking_data.get('email'), inline=True)
            embed.add_field(name="📞 Điện thoại", value=self.booking_data.get('phone'), inline=True)
            embed.add_field(name="📅 Ngày", value=self.booking_data.get('date'), inline=True)
            
            # Format thời gian cho response xác nhận
            start_time = self.booking_data.get('startTime', '')
            end_time = self.booking_data.get('endTime', '')
            time_display = f"({start_time} - {end_time})" if start_time and end_time else self.booking_data.get('time', 'N/A')
            embed.add_field(name="⏰ Thời gian", value=time_display, inline=True)
            
            embed.add_field(name="🏢 Phòng", value=self.booking_data.get('room'), inline=True)
            embed.add_field(name="👨‍💼 Xác nhận bởi", value=f"{admin_name}", inline=True)
            embed.add_field(name="📧 Email gửi", value="✅ Thành công" if email_sent else "❌ Thất bại", inline=True)
            embed.add_field(name="� Calendar", value="✅ Đã tạo" if calendar_created else "❌ Thất bại", inline=True)
            embed.add_field(name="�🔄 Trạng thái", value="**ĐÃ XÁC NHẬN**", inline=True)
            
            # Disable tất cả buttons
            for item in self.children:
                item.disabled = True
            
            await interaction.edit_original_response(embed=embed, view=self)
            
            # Gửi log message
            start_time = self.booking_data.get('startTime', '')
            end_time = self.booking_data.get('endTime', '')
            time_display = f"({start_time} - {end_time})" if start_time and end_time else self.booking_data.get('time', 'N/A')
            
            log_msg = f"✅ **Booking được xác nhận**\n"
            log_msg += f"👤 Khách: {self.booking_data.get('name')}\n"
            log_msg += f"📧 Email: {self.booking_data.get('email')}\n"
            log_msg += f"📅 Lịch: {self.booking_data.get('date')} - {time_display}\n"
            log_msg += f"👨‍💼 Bởi: {admin_name}"
            
            await interaction.followup.send(log_msg)
            
        except Exception as e:
            logger.error(f"Error confirming booking: {e}")
            await interaction.followup.send(f"❌ Lỗi khi xác nhận booking: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label='❌ Hủy lịch', style=discord.ButtonStyle.danger, custom_id='cancel_booking')
    async def cancel_booking(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Xử lý khi admin click nút hủy lịch
        """
        await self._handle_booking_action(interaction, 'cancelled', "❌ Booking đã bị hủy", 0xFF0000)
    
    @discord.ui.button(label='⚠️ Lịch Lỗi', style=discord.ButtonStyle.secondary, custom_id='error_booking')
    async def error_booking(self, interaction: discord.Interaction, button: discord.ui.Button):
        """
        Xử lý khi admin click nút lịch lỗi
        """
        await self._handle_booking_action(interaction, 'error', "⚠️ Booking đã được đánh dấu lỗi", 0xFFA500)
    
    async def _handle_booking_action(self, interaction: discord.Interaction, status: str, title: str, color: int):
        """
        Xử lý chung cho tất cả các action booking
        
        Args:
            interaction: Discord interaction
            status: Trạng thái mới ('confirmed', 'cancelled', 'error')
            title: Tiêu đề embed
            color: Màu embed
        """
        try:
            await interaction.response.defer()
            
            # Lấy thông tin admin
            admin_name = interaction.user.display_name
            admin_id = interaction.user.id
            
            logger.info(f"Admin {admin_name} ({admin_id}) setting booking status to {status} for {self.booking_data.get('email')}")
            
            # Validate rowNumber
            row_number = self.booking_data.get('rowNumber')
            if not row_number:
                logger.error(f"Missing rowNumber in booking data: {self.booking_data}")
                await interaction.followup.send("❌ Lỗi: Không tìm thấy số dòng booking!", ephemeral=True)
                return
            
            logger.info(f"Updating row {row_number} to status {status}")
            
            # Cập nhật trạng thái trong Google Sheets
            success = self.sheets_manager.update_booking_status(
                row_number,
                status,
                admin_name
            )
            
            if not success:
                logger.error(f"Failed to update booking status for row {row_number}")
                await interaction.followup.send("❌ Lỗi khi cập nhật Google Sheets!", ephemeral=True)
                return
            
            # Gửi email tương ứng và xử lý calendar event
            email_sent = False
            calendar_event_handled = True
            
            if status == 'confirmed':
                email_sent = self.email_manager.send_confirmation_email(self.booking_data)
                # Tạo calendar event khi xác nhận
                try:
                    event_id = self.sheets_manager.add_to_google_calendar(self.booking_data)
                    if event_id:
                        logger.info(f"✅ Created calendar event {event_id} for confirmed booking")
                        # Lưu event_id vào booking_data để có thể xóa sau này
                        self.booking_data['calendar_event_id'] = event_id
                    else:
                        logger.warning("❌ Failed to create calendar event for confirmed booking")
                        calendar_event_handled = False
                except Exception as e:
                    logger.error(f"Error creating calendar event: {e}")
                    calendar_event_handled = False
                    
            elif status == 'cancelled':
                email_sent = self.email_manager.send_cancellation_email(self.booking_data)
                # Note: Calendar event cần được xóa manual bởi admin
                logger.info("📅 Note: Calendar event (if exists) should be deleted manually")
                    
            elif status == 'error':
                # Có thể gửi email thông báo lỗi hoặc không gửi gì
                email_sent = True  # Giả sử không cần gửi email cho lịch lỗi
            
            # Cập nhật message Discord
            embed = discord.Embed(
                title=title,
                color=color,
                timestamp=datetime.now(pytz.timezone(Config.TIMEZONE))
            )
            
            embed.add_field(name="👤 Khách hàng", value=self.booking_data.get('name'), inline=True)
            embed.add_field(name="📧 Email", value=self.booking_data.get('email'), inline=True)
            embed.add_field(name="📞 Điện thoại", value=self.booking_data.get('phone'), inline=True)
            embed.add_field(name="📅 Ngày", value=self.booking_data.get('date'), inline=True)
            
            # Format thời gian
            start_time = self.booking_data.get('startTime', '')
            end_time = self.booking_data.get('endTime', '')
            time_display = f"({start_time} - {end_time})" if start_time and end_time else self.booking_data.get('time', 'N/A')
            embed.add_field(name="⏰ Thời gian", value=time_display, inline=True)
            
            embed.add_field(name="🏢 Phòng", value=self.booking_data.get('room'), inline=True)
            embed.add_field(name="👨‍💼 Xử lý bởi", value=f"{admin_name}", inline=True)
            
            # Status-specific fields
            if status in ['confirmed', 'cancelled']:
                embed.add_field(name="📧 Email gửi", value="✅ Thành công" if email_sent else "❌ Thất bại", inline=True)
            
            # Trạng thái mapping
            status_display = {
                'confirmed': "**ĐÃ XÁC NHẬN**",
                'cancelled': "**ĐÃ HỦY**", 
                'error': "**LỊCH LỖI**"
            }
            embed.add_field(name="🔄 Trạng thái", value=status_display.get(status), inline=True)
            
            # Disable tất cả buttons
            for item in self.children:
                item.disabled = True
            
            await interaction.edit_original_response(embed=embed, view=self)
            
            # Gửi log message
            log_msg = f"{title}\n"
            log_msg += f"👤 Khách: {self.booking_data.get('name')}\n"
            log_msg += f"📧 Email: {self.booking_data.get('email')}\n"
            log_msg += f"📅 Lịch: {self.booking_data.get('date')} - {time_display}\n"
            log_msg += f"👨‍💼 Bởi: {admin_name}"
            
            await interaction.followup.send(log_msg)
            
            logger.info(f"Booking {status} processed successfully for {self.booking_data.get('email')}")
            
        except Exception as e:
            logger.error(f"Error handling booking action {status}: {e}")
            await interaction.followup.send(f"❌ Lỗi khi xử lý: {str(e)}", ephemeral=True)


class DiscordBookingBot(commands.Bot):
    """
    Discord Bot chính cho hệ thống booking
    """
    
    def __init__(self):
        # Thiết lập intents (không cần privileged intents)
        intents = discord.Intents.default()
        intents.message_content = False  # Không cần đọc message content
        intents.guilds = True
        
        super().__init__(command_prefix='!', intents=intents)
        
        # Khởi tạo managers
        self.sheets_manager = GoogleSheetsManager()
        self.email_manager = EmailManager()
        self.channel_id = Config.DISCORD_CHANNEL_ID
        self.timezone = pytz.timezone(Config.TIMEZONE)
    
    async def on_ready(self):
        """
        Event khi bot sẵn sàng
        """
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")
    
    async def on_error(self, event, *args, **kwargs):
        """
        Xử lý lỗi global
        """
        logger.error(f"Discord bot error in {event}: {args}", exc_info=True)
    
    async def process_new_booking(self, booking_data):
        """
        Xử lý booking mới từ webhook
        
        Args:
            booking_data (dict): Dữ liệu booking từ Google Form
        """
        try:
            channel = self.get_channel(self.channel_id)
            if not channel:
                logger.error(f"Cannot find channel with ID: {self.channel_id}")
                return
            
            # Tạo embed message
            embed = discord.Embed(
                title="🆕 Booking mới cần xử lý",
                color=0x0099FF,
                timestamp=datetime.now(self.timezone)
            )
            
            embed.add_field(name="👤 Tên khách hàng", value=booking_data.get('name', 'N/A'), inline=True)
            embed.add_field(name="📧 Email", value=booking_data.get('email', 'N/A'), inline=True)
            embed.add_field(name="📞 Điện thoại", value=booking_data.get('phone', 'N/A'), inline=True)
            embed.add_field(name="📅 Ngày đặt", value=booking_data.get('date', 'N/A'), inline=True)
            
            # Format thời gian từ startTime và endTime
            start_time = booking_data.get('startTime', '')
            end_time = booking_data.get('endTime', '')
            time_display = f"({start_time} - {end_time})" if start_time and end_time else booking_data.get('time', 'N/A')
            embed.add_field(name="⏰ Thời gian", value=time_display, inline=True)
            
            embed.add_field(name="🏢 Phòng/Địa điểm", value=booking_data.get('room', 'N/A'), inline=True)
            embed.add_field(name="📝 Ghi chú", value=booking_data.get('notes', 'Không có') or 'Không có', inline=False)
            embed.add_field(name="🔄 Trạng thái", value="**CHỜ XỬ LÝ**", inline=True)
            
            # Hiển thị conflict message từ Apps Script nếu có
            conflict_message = booking_data.get('conflictMessage', '')
            if conflict_message:
                embed.add_field(
                    name="⚠️ Cảnh báo xung đột",
                    value=conflict_message,
                    inline=False
                )
                embed.color = 0xFFA500  # Orange color for warning
            
            embed.set_footer(text=f"ID: {booking_data.get('rowNumber', 'N/A')}")
            
            # Tạo view với buttons
            view = BookingView(booking_data, self.sheets_manager, self.email_manager)
            
            # Gửi message với embed và buttons
            message = await channel.send(embed=embed, view=view)
            
            logger.info(f"New booking posted to Discord: {booking_data.get('email')}")
            
            # Mention role nếu cần (optional)
            # await channel.send("@here Có booking mới cần xử lý!")
            
        except Exception as e:
            logger.error(f"Error processing new booking: {e}")
            raise
    
    @app_commands.command(name="booking_status", description="Kiểm tra trạng thái booking")
    async def booking_status(self, interaction: discord.Interaction, email: str = None):
        """
        Slash command để kiểm tra trạng thái booking
        """
        try:
            await interaction.response.defer()
            
            if email:
                # Tìm booking theo email
                data = self.sheets_manager.get_sheet_data()
                bookings = []
                
                for i, row in enumerate(data[1:], start=2):
                    if len(row) >= 2 and row[1].lower() == email.lower():
                        bookings.append({
                            'row': i,
                            'data': row
                        })
                
                if not bookings:
                    await interaction.followup.send(f"❌ Không tìm thấy booking nào cho email: {email}")
                    return
                
                # Hiển thị danh sách bookings
                embed = discord.Embed(
                    title=f"📋 Booking của {email}",
                    color=0x0099FF
                )
                
                for booking in bookings[-5:]:  # Chỉ hiển thị 5 booking gần nhất
                    row = booking['data']
                    status = row[7] if len(row) > 7 else "Chờ xử lý"
                    
                    embed.add_field(
                        name=f"📅 {row[4]} - {row[5]}",
                        value=f"🏢 {row[6]}\n🔄 {status}",
                        inline=True
                    )
                
                await interaction.followup.send(embed=embed)
            
            else:
                # Hiển thị thống kê tổng quan
                data = self.sheets_manager.get_sheet_data()
                
                if len(data) < 2:
                    await interaction.followup.send("❌ Không có dữ liệu booking")
                    return
                
                total = len(data) - 1  # Trừ header
                confirmed = 0
                cancelled = 0
                pending = 0
                
                for row in data[1:]:
                    if len(row) > 7:
                        status = row[7].lower()
                        if 'xác nhận' in status:
                            confirmed += 1
                        elif 'hủy' in status:
                            cancelled += 1
                        else:
                            pending += 1
                    else:
                        pending += 1
                
                embed = discord.Embed(
                    title="📊 Thống kê Booking",
                    color=0x0099FF
                )
                
                embed.add_field(name="📝 Tổng số", value=str(total), inline=True)
                embed.add_field(name="✅ Đã xác nhận", value=str(confirmed), inline=True)
                embed.add_field(name="❌ Đã hủy", value=str(cancelled), inline=True)
                embed.add_field(name="⏳ Chờ xử lý", value=str(pending), inline=True)
                
                await interaction.followup.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Error in booking_status command: {e}")
            await interaction.followup.send(f"❌ Lỗi: {str(e)}")
    
    @app_commands.command(name="refresh_booking", description="Làm mới một booking từ Google Sheets")
    async def refresh_booking(self, interaction: discord.Interaction, row_number: int):
        """
        Slash command để làm mới booking từ Google Sheets
        """
        try:
            await interaction.response.defer()
            
            data = self.sheets_manager.get_sheet_data()
            
            if row_number < 2 or row_number > len(data):
                await interaction.followup.send(f"❌ Số dòng không hợp lệ: {row_number}")
                return
            
            row = data[row_number - 1]
            
            if len(row) < 6:
                await interaction.followup.send(f"❌ Dữ liệu dòng {row_number} không đầy đủ")
                return
            
            # Tạo booking data
            booking_data = {
                'row_number': row_number,
                'email': row[1] if len(row) > 1 else "",
                'name': row[2] if len(row) > 2 else "",
                'phone': row[3] if len(row) > 3 else "",
                'date': row[4] if len(row) > 4 else "",
                'time': row[5] if len(row) > 5 else "",
                'room': row[6] if len(row) > 6 else "",
                'note': row[8] if len(row) > 8 else ""
            }
            
            # Xử lý như booking mới
            await self.process_new_booking(booking_data)
            
            await interaction.followup.send(f"✅ Đã làm mới booking dòng {row_number}")
            
        except Exception as e:
            logger.error(f"Error in refresh_booking command: {e}")
            await interaction.followup.send(f"❌ Lỗi: {str(e)}")
