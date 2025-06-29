import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from config import Config
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

class EmailManager:
    """
    Class quản lý gửi email thông báo booking
    """
    
    def __init__(self):
        self.smtp_server = Config.SMTP_SERVER
        self.smtp_port = Config.SMTP_PORT
        self.email = Config.GMAIL_EMAIL
        self.password = Config.GMAIL_PASSWORD
        self.timezone = pytz.timezone(Config.TIMEZONE)
    
    def _create_smtp_connection(self):
        """
        Tạo kết nối SMTP với Gmail
        
        Returns:
            smtplib.SMTP: SMTP connection object
        """
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # Enable encryption
            server.login(self.email, self.password)
            return server
        except Exception as e:
            logger.error(f"Failed to create SMTP connection: {e}")
            raise
    
    def _create_email_template(self, template_type, booking_data):
        """
        Tạo template email dựa trên loại thông báo
        
        Args:
            template_type (str): 'confirmation' hoặc 'cancellation'
            booking_data (dict): Thông tin booking
        
        Returns:
            tuple: (subject, html_body, text_body)
        """
        customer_name = booking_data.get('name', 'Quý khách')
        booking_date = booking_data.get('date', '')
        
        # Format thời gian từ startTime và endTime
        start_time = booking_data.get('startTime', '')
        end_time = booking_data.get('endTime', '')
        booking_time = f"({start_time} - {end_time})" if start_time and end_time else booking_data.get('time', '')
        
        room = booking_data.get('room', '')
        
        # Lấy thời gian hiện tại
        now = datetime.now(self.timezone)
        formatted_time = now.strftime("%d/%m/%Y lúc %H:%M")
        
        if template_type == 'confirmation':
            subject = f"Xác Nhận Đặt Lịch - {room} - {booking_date} {booking_time}"
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #4CAF50, #45a049); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center;">
                        <h1 style="margin: 0; font-size: 24px;">Đặt lịch đã được xác nhận!</h1>
                    </div>
                    
                    <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #ddd;">
                        <p>Kính chào <strong>{customer_name}</strong>,</p>
                        
                        <p>Chúng tôi xin thông báo lịch đặt của bạn đã được <strong style="color: #4CAF50;">XÁC NHẬN THÀNH CÔNG</strong>!</p>
                        
                        <div style="background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #4CAF50; margin: 20px 0;">
                            <h3 style="color: #4CAF50; margin-top: 0;">📋 Thông tin đặt lịch:</h3>
                            <p><strong>📅 Ngày:</strong> {booking_date}</p>
                            <p><strong>⏰ Giờ:</strong> {booking_time}</p>
                            <p><strong>🏢 Phòng/Địa điểm:</strong> {room}</p>
                            <p><strong>✅ Trạng thái:</strong> <span style="color: #4CAF50; font-weight: bold;">Đã xác nhận</span></p>
                            <p><strong>📆 Thời gian xác nhận:</strong> {formatted_time}</p>
                        </div>
                        
                        <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0;">
                            <h4 style="color: #2e7d32; margin-top: 0;">💡 Lưu ý quan trọng:</h4>
                            <ul style="margin: 0; padding-left: 20px;">
                                <li>Vui lòng có mặt đúng giờ đã đặt</li>
                                <li>Nếu có thay đổi, liên hệ trước ít nhất 2 giờ</li>
                                <li>Mang theo giấy tờ tùy thân khi đến</li>
                            </ul>
                        </div>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <p>Nếu bạn cần hỗ trợ, vui lòng liên hệ:</p>
                            <p><strong>📧 Email:</strong> {Config.COMPANY_EMAIL}</p>
                            <p><strong>📞 Điện thoại:</strong> {Config.COMPANY_PHONE}</p>
                        </div>
                        
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                        
                        <p style="text-align: center; color: #666; font-size: 14px;">
                            Cảm ơn bạn đã tin tưởng sử dụng dịch vụ của <strong>{Config.COMPANY_NAME}</strong>!<br>
                            Email này được gửi tự động, vui lòng không reply.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_body = f"""
            ĐẶT LỊCH ĐÃ ĐƯỢC XÁC NHẬN!
            
            Kính chào {customer_name},
            
            Lịch đặt của bạn đã được XÁC NHẬN THÀNH CÔNG!
            
            THÔNG TIN ĐẶT LỊCH:
            📅 Ngày: {booking_date}
            ⏰ Giờ: {booking_time}
            🏢 Phòng: {room}
            ✅ Trạng thái: Đã xác nhận
            📆 Thời gian xác nhận: {formatted_time}
            
            LỜI NHẮC:
            - Vui lòng có mặt đúng giờ đã đặt
            - Nếu có thay đổi, liên hệ trước ít nhất 2 giờ
            - Mang theo giấy tờ tùy thân khi đến
            
            LIÊN HỆ HỖ TRỢ:
            📧 Email: {Config.COMPANY_EMAIL}
            📞 Điện thoại: {Config.COMPANY_PHONE}
            
            Cảm ơn bạn đã tin tưởng sử dụng dịch vụ của {Config.COMPANY_NAME}!
            """
        
        else:  # cancellation
            subject = f"❌ Thông báo hủy lịch - {booking_date} {booking_time}"
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #f44336, #d32f2f); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center;">
                        <h1 style="margin: 0; font-size: 24px;">❌ Lịch đặt đã bị hủy</h1>
                    </div>
                    
                    <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #ddd;">
                        <p>Kính chào <strong>{customer_name}</strong>,</p>
                        
                        <p>Chúng tôi xin thông báo lịch đặt của bạn đã bị <strong style="color: #f44336;">HỦY</strong>.</p>
                        
                        <div style="background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #f44336; margin: 20px 0;">
                            <h3 style="color: #f44336; margin-top: 0;">📋 Thông tin lịch đã hủy:</h3>
                            <p><strong>📅 Ngày:</strong> {booking_date}</p>
                            <p><strong>⏰ Giờ:</strong> {booking_time}</p>
                            <p><strong>🏢 Phòng/Địa điểm:</strong> {room}</p>
                            <p><strong>❌ Trạng thái:</strong> <span style="color: #f44336; font-weight: bold;">Đã hủy</span></p>
                            <p><strong>📆 Thời gian hủy:</strong> {formatted_time}</p>
                        </div>
                        
                        <div style="background: #ffebee; padding: 15px; border-radius: 8px; margin: 20px 0;">
                            <h4 style="color: #c62828; margin-top: 0;">📝 Lý do hủy lịch:</h4>
                            <p>Lịch đặt có thể bị hủy do một trong các lý do sau:</p>
                            <ul style="margin: 0; padding-left: 20px;">
                                <li>Xung đột thời gian với lịch khác</li>
                                <li>Sự cố kỹ thuật hoặc bảo trì</li>
                                <li>Yêu cầu từ phía khách hàng</li>
                                <li>Lý do bất khả kháng khác</li>
                            </ul>
                        </div>
                        
                        <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0;">
                            <h4 style="color: #1976d2; margin-top: 0;">🔄 Đặt lại lịch mới:</h4>
                            <p>Bạn có thể đặt lại lịch mới bằng cách:</p>
                            <ul style="margin: 0; padding-left: 20px;">
                                <li>Điền form đặt lịch trực tuyến</li>
                                <li>Gọi điện thoại đến hotline</li>
                                <li>Gửi email yêu cầu hỗ trợ</li>
                            </ul>
                        </div>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <p>Chúng tôi xin lỗi vì sự bất tiện này. Để được hỗ trợ:</p>
                            <p><strong>📧 Email:</strong> {Config.COMPANY_EMAIL}</p>
                            <p><strong>📞 Điện thoại:</strong> {Config.COMPANY_PHONE}</p>
                        </div>
                        
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                        
                        <p style="text-align: center; color: #666; font-size: 14px;">
                            Cảm ơn bạn đã hiểu và ủng hộ <strong>{Config.COMPANY_NAME}</strong>!<br>
                            Email này được gửi tự động, vui lòng không reply.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_body = f"""
            ❌ LỊCH ĐẶT ĐÃ BỊ HỦY
            
            Kính chào {customer_name},
            
            Lịch đặt của bạn đã bị HỦY.
            
            THÔNG TIN LỊCH ĐÃ HỦY:
            📅 Ngày: {booking_date}
            ⏰ Giờ: {booking_time}
            🏢 Phòng: {room}
            ❌ Trạng thái: Đã hủy
            📆 Thời gian hủy: {formatted_time}
            
            LÝ DO HỦY LỊCH:
            Lịch đặt có thể bị hủy do:
            - Xung đột thời gian với lịch khác
            - Sự cố kỹ thuật hoặc bảo trì
            - Yêu cầu từ phía khách hàng
            - Lý do bất khả kháng khác
            
            ĐẶT LẠI LỊCH MỚI:
            - Điền form đặt lịch trực tuyến
            - Gọi điện thoại đến hotline
            - Gửi email yêu cầu hỗ trợ
            
            LIÊN HỆ HỖ TRỢ:
            📧 Email: {Config.COMPANY_EMAIL}
            📞 Điện thoại: {Config.COMPANY_PHONE}
            
            Xin lỗi vì sự bất tiện. Cảm ơn sự thông cảm của bạn!
            """
        
        return subject, html_body, text_body
    
    def send_booking_email(self, recipient_email, template_type, booking_data):
        """
        Gửi email thông báo booking
        
        Args:
            recipient_email (str): Email người nhận
            template_type (str): Loại email ('confirmation' hoặc 'cancellation')
            booking_data (dict): Thông tin booking
        
        Returns:
            bool: True nếu gửi thành công
        """
        try:
            # Tạo email template
            subject, html_body, text_body = self._create_email_template(template_type, booking_data)
            
            # Tạo message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{Config.COMPANY_NAME} <{self.email}>"
            msg['To'] = recipient_email
            
            # Attach text và HTML versions
            text_part = MIMEText(text_body, 'plain', 'utf-8')
            html_part = MIMEText(html_body, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Gửi email
            server = self._create_smtp_connection()
            text = msg.as_string()
            server.sendmail(self.email, recipient_email, text)
            server.quit()
            
            logger.info(f"Email sent successfully to {recipient_email} - Type: {template_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {e}")
            return False
    
    def send_confirmation_email(self, booking_data):
        """
        Gửi email xác nhận booking
        
        Args:
            booking_data (dict): Thông tin booking
        
        Returns:
            bool: True nếu gửi thành công
        """
        return self.send_booking_email(
            booking_data.get('email'),
            'confirmation',
            booking_data
        )
    
    def send_cancellation_email(self, booking_data):
        """
        Gửi email hủy booking
        
        Args:
            booking_data (dict): Thông tin booking
        
        Returns:
            bool: True nếu gửi thành công
        """
        return self.send_booking_email(
            booking_data.get('email'),
            'cancellation',
            booking_data
        )
