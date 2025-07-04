"""
Email Manager sử dụng Google Apps Script Web App
Thay thế hoàn toàn SMTP để tránh bị block ports trên VPS
"""

import requests
import logging
from typing import Dict, Optional, Any
from config import Config

logger = logging.getLogger(__name__)

class EmailManager:
    """
    Email Manager sử dụng Google Apps Script Web App
    Gửi email thông qua POST request đến Apps Script để tránh bị block SMTP ports
    """
    
    def __init__(self, appscript_url: Optional[str] = None):
        """
        Khởi tạo Email Manager
        
        Args:
            appscript_url (str, optional): URL của Apps Script Web App
        """
        self.appscript_url = appscript_url or getattr(Config, 'APPSCRIPT_WEBHOOK_URL', None)
        
        if not self.appscript_url:
            logger.warning("APPSCRIPT_WEBHOOK_URL not configured. Email sending will be disabled.")
        
        # Timeout settings
        self.timeout = getattr(Config, 'APPSCRIPT_TIMEOUT', 30)
        self.max_retries = getattr(Config, 'APPSCRIPT_MAX_RETRIES', 3)
    
    def send_mail_via_appscript(
        self, 
        to: str, 
        subject: str, 
        body: str, 
        html_body: Optional[str] = None,
        sender_name: Optional[str] = None
    ) -> bool:
        """
        Gửi email thông qua Google Apps Script
        
        Args:
            to (str): Email người nhận
            subject (str): Tiêu đề email
            body (str): Nội dung text thuần
            html_body (str, optional): Nội dung HTML
            sender_name (str, optional): Tên người gửi
            
        Returns:
            bool: True nếu gửi thành công, False nếu thất bại
        """
        if not self.appscript_url:
            logger.error("AppScript URL not configured. Cannot send email.")
            return False
            
        if not to or not subject or not body:
            logger.error("Missing required email parameters: to, subject, or body")
            return False
        
        # Tạo payload gửi đến Apps Script
        payload = {
            'to': to,
            'subject': subject,
            'body': body,
            'htmlBody': html_body,
            'senderName': sender_name or getattr(Config, 'COMPANY_NAME', 'Discord Booking System')
        }
        
        # Headers cho request
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Discord-Booking-Bot/1.0'
        }
        
        # Thử gửi với retry mechanism
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Sending email to {to} via AppScript (attempt {attempt + 1}/{self.max_retries})")
                
                response = requests.post(
                    self.appscript_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )
                
                # Kiểm tra response
                if response.status_code == 200:
                    response_data = response.json()
                    
                    if response_data.get('success', False):
                        logger.info(f"Email sent successfully to {to} via AppScript")
                        return True
                    else:
                        error_msg = response_data.get('error', 'Unknown error from AppScript')
                        logger.error(f"AppScript returned error: {error_msg}")
                        
                else:
                    logger.error(f"AppScript request failed with status {response.status_code}: {response.text}")
                    
            except requests.exceptions.Timeout:
                logger.warning(f"Request to AppScript timed out (attempt {attempt + 1})")
                
            except requests.exceptions.ConnectionError:
                logger.warning(f"Connection error to AppScript (attempt {attempt + 1})")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error to AppScript: {e}")
                
            except Exception as e:
                logger.error(f"Unexpected error sending email via AppScript: {e}")
            
            # Nếu không phải lần thử cuối, chờ một chút trước khi retry
            if attempt < self.max_retries - 1:
                import time
                time.sleep(2 ** attempt)  # Exponential backoff
        
        logger.error(f"Failed to send email to {to} after {self.max_retries} attempts")
        return False
    
    def send_confirmation_email(self, booking_data: Dict[str, Any]) -> bool:
        """
        Gửi email xác nhận booking
        
        Args:
            booking_data (dict): Thông tin booking
            
        Returns:
            bool: True nếu gửi thành công
        """
        try:
            subject, html_body, text_body = self._create_email_template('confirmation', booking_data)
            
            return self.send_mail_via_appscript(
                to=booking_data.get('email'),
                subject=subject,
                body=text_body,
                html_body=html_body,
                sender_name=getattr(Config, 'COMPANY_NAME', 'Discord Booking System')
            )
            
        except Exception as e:
            logger.error(f"Error sending confirmation email: {e}")
            return False
    
    def send_cancellation_email(self, booking_data: Dict[str, Any]) -> bool:
        """
        Gửi email hủy booking
        
        Args:
            booking_data (dict): Thông tin booking
            
        Returns:
            bool: True nếu gửi thành công
        """
        try:
            subject, html_body, text_body = self._create_email_template('cancellation', booking_data)
            
            return self.send_mail_via_appscript(
                to=booking_data.get('email'),
                subject=subject,
                body=text_body,
                html_body=html_body,
                sender_name=getattr(Config, 'COMPANY_NAME', 'Discord Booking System')
            )
            
        except Exception as e:
            logger.error(f"Error sending cancellation email: {e}")
            return False
    
    def send_error_email(self, booking_data: Dict[str, Any]) -> bool:
        """
        Gửi email thông báo lỗi booking
        
        Args:
            booking_data (dict): Thông tin booking
            
        Returns:
            bool: True nếu gửi thành công
        """
        try:
            subject, html_body, text_body = self._create_email_template('error', booking_data)
            
            return self.send_mail_via_appscript(
                to=booking_data.get('email'),
                subject=subject,
                body=text_body,
                html_body=html_body,
                sender_name=getattr(Config, 'COMPANY_NAME', 'Discord Booking System')
            )
            
        except Exception as e:
            logger.error(f"Error sending error notification email: {e}")
            return False

    def _create_email_template(self, template_type: str, booking_data: Dict[str, Any]):
        """
        Tạo template email dựa trên loại thông báo
        
        Args:
            template_type (str): 'confirmation', 'cancellation', hoặc 'error'
            booking_data (dict): Thông tin booking
        
        Returns:
            tuple: (subject, html_body, text_body)
        """
        import pytz
        from datetime import datetime
        
        customer_name = booking_data.get('name', 'Quý khách')
        booking_date = booking_data.get('date', '')
        
        # Format thời gian từ startTime và endTime
        start_time = booking_data.get('startTime', '')
        end_time = booking_data.get('endTime', '')
        booking_time = f"({start_time} - {end_time})" if start_time and end_time else booking_data.get('time', '')
        
        room = booking_data.get('room', '')
        
        # Lấy thời gian hiện tại
        timezone = pytz.timezone(getattr(Config, 'TIMEZONE', 'Asia/Ho_Chi_Minh'))
        now = datetime.now(timezone)
        formatted_time = now.strftime("%d/%m/%Y lúc %H:%M")
        
        if template_type == 'confirmation':
            subject = f"✅ Xác Nhận Đặt Lịch - {room} - {booking_date} {booking_time}"
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #4CAF50, #45a049); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center;">
                        <h1 style="margin: 0; font-size: 24px;">✅ Đặt lịch đã được xác nhận!</h1>
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
                            <p><strong>📧 Email:</strong> {getattr(Config, 'COMPANY_EMAIL', 'contact@company.com')}</p>
                            <p><strong>📞 Điện thoại:</strong> {getattr(Config, 'COMPANY_PHONE', '+84 123 456 789')}</p>
                        </div>
                        
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                        
                        <p style="text-align: center; color: #666; font-size: 14px;">
                            Cảm ơn bạn đã tin tưởng sử dụng dịch vụ của <strong>{getattr(Config, 'COMPANY_NAME', 'Your Company')}</strong>!<br>
                            Email này được gửi tự động, vui lòng không reply.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_body = f"""
            ✅ ĐẶT LỊCH ĐÃ ĐƯỢC XÁC NHẬN!
            
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
            📧 Email: {getattr(Config, 'COMPANY_EMAIL', 'contact@company.com')}
            📞 Điện thoại: {getattr(Config, 'COMPANY_PHONE', '+84 123 456 789')}
            
            Cảm ơn bạn đã tin tưởng sử dụng dịch vụ của {getattr(Config, 'COMPANY_NAME', 'Your Company')}!
            """
        
        elif template_type == 'cancellation':
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
                            <p><strong>📧 Email:</strong> {getattr(Config, 'COMPANY_EMAIL', 'contact@company.com')}</p>
                            <p><strong>📞 Điện thoại:</strong> {getattr(Config, 'COMPANY_PHONE', '+84 123 456 789')}</p>
                        </div>
                        
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                        
                        <p style="text-align: center; color: #666; font-size: 14px;">
                            Cảm ơn bạn đã hiểu và ủng hộ <strong>{getattr(Config, 'COMPANY_NAME', 'Your Company')}</strong>!<br>
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
            📧 Email: {getattr(Config, 'COMPANY_EMAIL', 'contact@company.com')}
            📞 Điện thoại: {getattr(Config, 'COMPANY_PHONE', '+84 123 456 789')}
            
            Xin lỗi vì sự bất tiện. Cảm ơn sự thông cảm của bạn!
            """
        
        else:  # error
            subject = f"⚠️ Thông báo lỗi thông tin đặt lịch - {booking_date} {booking_time}"
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #ff9800, #f57c00); color: white; padding: 20px; border-radius: 10px 10px 0 0; text-align: center;">
                        <h1 style="margin: 0; font-size: 24px;">⚠️ Lỗi thông tin đặt lịch</h1>
                    </div>
                    
                    <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #ddd;">
                        <p>Kính chào <strong>{customer_name}</strong>,</p>
                        
                        <p>Chúng tôi nhận thấy có <strong style="color: #ff9800;">LỖI THÔNG TIN</strong> trong form đặt lịch của bạn.</p>
                        
                        <div style="background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #ff9800; margin: 20px 0;">
                            <h3 style="color: #ff9800; margin-top: 0;">📋 Thông tin lịch đã điền:</h3>
                            <p><strong>📅 Ngày:</strong> {booking_date}</p>
                            <p><strong>⏰ Giờ:</strong> {booking_time}</p>
                            <p><strong>🏢 Phòng/Địa điểm:</strong> {room}</p>
                            <p><strong>⚠️ Trạng thái:</strong> <span style="color: #ff9800; font-weight: bold;">Lỗi thông tin</span></p>
                            <p><strong>📆 Thời gian phát hiện lỗi:</strong> {formatted_time}</p>
                        </div>
                        
                        <div style="background: #fff3e0; padding: 15px; border-radius: 8px; margin: 20px 0;">
                            <h4 style="color: #e65100; margin-top: 0;">🔍 Các lỗi thường gặp:</h4>
                            <ul style="margin: 0; padding-left: 20px;">
                                <li><strong>Ngày tháng năm:</strong> Định dạng không đúng hoặc ngày không hợp lệ</li>
                                <li><strong>Giờ bắt đầu:</strong> Sai định dạng giờ (VD: 25:00) hoặc không điền đầy đủ</li>
                                <li><strong>Giờ kết thúc:</strong> Sai định dạng hoặc trước giờ bắt đầu</li>
                                <li><strong>Khoảng thời gian:</strong> Quá ngắn hoặc quá dài</li>
                                <li><strong>Thông tin thiếu:</strong> Một số trường bắt buộc chưa điền</li>
                            </ul>
                        </div>
                        
                        <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0;">
                            <h4 style="color: #2e7d32; margin-top: 0;">✅ Cách khắc phục:</h4>
                            <p><strong>1. Kiểm tra lại thông tin:</strong></p>
                            <ul style="margin: 0; padding-left: 20px;">
                                <li>Ngày: DD/MM/YYYY (VD: 15/07/2025)</li>
                                <li>Giờ: HH:MM (VD: 14:30)</li>
                                <li>Đảm bảo giờ kết thúc sau giờ bắt đầu</li>
                            </ul>
                            
                            <p><strong>2. Đặt lại lịch với thông tin chính xác:</strong></p>
                            <ul style="margin: 0; padding-left: 20px;">
                                <li>Điền lại form đặt lịch với thông tin đúng</li>
                                <li>Kiểm tra kỹ trước khi gửi</li>
                                <li>Hoặc gọi điện thoại để được hỗ trợ trực tiếp</li>
                            </ul>
                        </div>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <p>Nếu bạn cần hỗ trợ, vui lòng liên hệ:</p>
                            <p><strong>📧 Email:</strong> {getattr(Config, 'COMPANY_EMAIL', 'contact@company.com')}</p>
                            <p><strong>📞 Điện thoại:</strong> {getattr(Config, 'COMPANY_PHONE', '+84 123 456 789')}</p>
                        </div>
                        
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                        
                        <p style="text-align: center; color: #666; font-size: 14px;">
                            Cảm ơn bạn đã sử dụng dịch vụ của <strong>{getattr(Config, 'COMPANY_NAME', 'Your Company')}</strong>!<br>
                            Email này được gửi tự động, vui lòng không reply.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_body = f"""
            ⚠️ LỖI THÔNG TIN ĐẶT LỊCH
            
            Kính chào {customer_name},
            
            Chúng tôi nhận thấy có LỖI THÔNG TIN trong form đặt lịch của bạn.
            
            THÔNG TIN LỊCH ĐÃ ĐIỀN:
            📅 Ngày: {booking_date}
            ⏰ Giờ: {booking_time}
            🏢 Phòng: {room}
            ⚠️ Trạng thái: Lỗi thông tin
            📆 Thời gian phát hiện lỗi: {formatted_time}
            
            CÁC LỖI THƯỜNG GẶP:
            - Ngày tháng năm: Định dạng không đúng hoặc ngày không hợp lệ
            - Giờ bắt đầu: Sai định dạng giờ (VD: 25:00) hoặc không điền đầy đủ
            - Giờ kết thúc: Sai định dạng hoặc trước giờ bắt đầu
            
            CÁCH KHẮC PHỤC:
            1. Kiểm tra lại thông tin:
               - Ngày: DD/MM/YYYY (VD: 15/07/2025)
               - Giờ: HH:MM (VD: 14:30)
               - Đảm bảo giờ kết thúc sau giờ bắt đầu
               - Điền đầy đủ tất cả các trường bắt buộc
            
            2. Đặt lại lịch với thông tin chính xác:
               - Điền lại form đặt lịch với thông tin đúng
               - Kiểm tra kỹ trước khi gửi
               - Hoặc gọi điện thoại để được hỗ trợ trực tiếp
            
            LIÊN HỆ HỖ TRỢ:
            📧 Email: {getattr(Config, 'COMPANY_EMAIL', 'contact@company.com')}
            📞 Điện thoại: {getattr(Config, 'COMPANY_PHONE', '+84 123 456 789')}
            
            Cảm ơn bạn đã sử dụng dịch vụ của {getattr(Config, 'COMPANY_NAME', 'Your Company')}!
            """
        
        return subject, html_body, text_body
    
    def test_connection(self) -> bool:
        """
        Test kết nối đến Apps Script Web App
        
        Returns:
            bool: True nếu kết nối thành công
        """
        if not self.appscript_url:
            logger.error("AppScript URL not configured")
            return False
        
        test_payload = {
            'to': 'test@example.com',
            'subject': 'Test Email Connection',
            'body': 'This is a test email to verify Apps Script connection.',
            'test': True  # Flag để Apps Script biết đây là test, không gửi email thật
        }
        
        try:
            response = requests.post(
                self.appscript_url,
                json=test_payload,
                headers={'Content-Type': 'application/json'},
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                logger.info("Apps Script connection test successful")
                return True
            else:
                logger.error(f"Apps Script connection test failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Apps Script connection test error: {e}")
            return False
