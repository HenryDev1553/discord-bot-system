from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
from config import Config
from datetime import datetime, timedelta
import pytz

logger = logging.getLogger(__name__)

class GoogleSheetsManager:
    """
    Class quản lý kết nối và thao tác với Google Sheets
    """
    
    def __init__(self):
        self.service = None
        self.calendar_service = None
        self.spreadsheet_id = Config.GOOGLE_SHEETS_ID
        self.sheet_name = Config.SHEET_NAME
        self.timezone = pytz.timezone(Config.TIMEZONE)
        self._setup_service()
    
    def _setup_service(self):
        """
        Thiết lập kết nối với Google Sheets API và Calendar API
        """
        try:
            # Đọc credentials từ file JSON
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/calendar'  # Thêm scope cho Calendar
            ]
            creds = Credentials.from_service_account_file(
                Config.GOOGLE_CREDENTIALS_PATH, scopes=scopes
            )
            
            # Tạo service objects
            self.service = build('sheets', 'v4', credentials=creds)
            self.calendar_service = build('calendar', 'v3', credentials=creds)
            logger.info("Google Sheets and Calendar services initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google services: {e}")
            raise
    
    def get_sheet_data(self, range_name=None):
        """
        Lấy dữ liệu từ Google Sheet
        
        Args:
            range_name (str): Range cần lấy dữ liệu (VD: 'A:Z')
        
        Returns:
            list: Dữ liệu từ sheet
        """
        try:
            if not range_name:
                range_name = f"{self.sheet_name}!A:Z"
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            logger.info(f"Retrieved {len(values)} rows from sheet")
            return values
            
        except HttpError as e:
            logger.error(f"Error getting sheet data: {e}")
            return []
    
    def update_booking_status(self, row_number, status, admin_name=None):
        """
        Cập nhật trạng thái booking trong Google Sheet
        
        Args:
            row_number (int): Số dòng cần cập nhật
            status (str): Trạng thái mới ('confirmed', 'cancelled', 'error', 'pending')
            admin_name (str): Tên admin thực hiện action
        
        Returns:
            bool: True nếu cập nhật thành công
        """
        try:
            logger.info(f"Updating booking status: row={row_number}, status={status}, admin={admin_name}")
            
            # Validate input
            if not row_number or row_number < 2:
                logger.error(f"Invalid row number: {row_number}")
                return False
            
            # Lấy thời gian hiện tại
            now = datetime.now(self.timezone)
            timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
            
            # Mapping trạng thái
            status_mapping = {
                'pending': 'Chờ xử lý',
                'confirmed': 'Đã xác nhận',  # Sửa để match với logic conflict
                'cancelled': 'Hủy',
                'error': 'Lịch Lỗi'
            }
            
            status_text = status_mapping.get(status, status)
            admin_info = f"by {admin_name}" if admin_name else ""
            
            logger.info(f"Mapped status '{status}' to '{status_text}'")
            
            # Cập nhật cột trạng thái (cột K) và thời gian xử lý (cột L)
            updates = [
                {
                    'range': f"{self.sheet_name}!K{row_number}",
                    'values': [[status_text]]
                },
                {
                    'range': f"{self.sheet_name}!L{row_number}",
                    'values': [[f"{timestamp} {admin_info}"]]
                }
            ]
            
            # Thực hiện batch update
            body = {
                'valueInputOption': 'RAW',
                'data': updates
            }
            
            result = self.service.spreadsheets().values().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=body
            ).execute()
            
            logger.info(f"Updated booking status for row {row_number}: {status_text}")
            return True
            
        except HttpError as e:
            logger.error(f"Error updating booking status: {e}")
            return False
    
    def find_booking_by_data(self, email, date, time):
        """
        Tìm booking trong sheet dựa trên email, ngày và giờ
        
        Args:
            email (str): Email khách hàng
            date (str): Ngày booking
            time (str): Giờ booking
        
        Returns:
            dict: Thông tin booking nếu tìm thấy, None nếu không tìm thấy
        """
        try:
            data = self.get_sheet_data()
            
            if not data or len(data) < 2:  # Không có dữ liệu hoặc chỉ có header
                return None
            
            # Giả sử cấu trúc: [Timestamp, Email, Name, Phone, Date, Time, Room, Status, ProcessedTime]
            for i, row in enumerate(data[1:], start=2):  # Bỏ qua header, bắt đầu từ row 2
                if len(row) >= 6:
                    row_email = row[1] if len(row) > 1 else ""
                    row_date = row[4] if len(row) > 4 else ""
                    row_time = row[5] if len(row) > 5 else ""
                    
                    if (row_email.lower() == email.lower() and 
                        row_date == date and 
                        row_time == time):
                        
                        return {
                            'row_number': i,
                            'email': row_email,
                            'name': row[2] if len(row) > 2 else "",
                            'phone': row[3] if len(row) > 3 else "",
                            'date': row_date,
                            'time': row_time,
                            'room': row[6] if len(row) > 6 else "",
                            'status': row[7] if len(row) > 7 else "Chờ xử lý"
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding booking: {e}")
            return None
    
    def check_room_conflicts(self, date, start_time, end_time, room, exclude_row=None, limit_rows=30):
        """
        Kiểm tra xung đột lịch phòng với thời gian bắt đầu và kết thúc
        Chỉ check với các booking có trạng thái "Chờ xử lý" hoặc "Đã xác nhận"
        
        Args:
            date (str): Ngày booking (format: dd/mm/yyyy)
            start_time (str): Giờ bắt đầu (format: HH:MM)  
            end_time (str): Giờ kết thúc (format: HH:MM)
            room (str): Phòng booking
            exclude_row (int): Dòng cần loại trừ khỏi kiểm tra
            limit_rows (int): Số hàng mới nhất cần check (default: 15)
        
        Returns:
            list: Danh sách booking xung đột với thông tin chi tiết
        """
        try:
            data = self.get_sheet_data()
            conflicts = []
            
            if not data or len(data) < 2:
                return conflicts
            
            # Parse thời gian input
            def parse_time_to_minutes(time_str):
                """Convert HH:MM or HH:MM:SS to minutes since midnight"""
                try:
                    time_str = str(time_str).strip()
                    # Handle HH:MM:SS format
                    if time_str.count(':') == 2:
                        time_parts = time_str.split(':')
                        hours, minutes = int(time_parts[0]), int(time_parts[1])
                    # Handle HH:MM format  
                    elif time_str.count(':') == 1:
                        hours, minutes = map(int, time_str.split(':'))
                    else:
                        # Invalid format
                        return -1
                    
                    # Validate time range
                    if 0 <= hours <= 23 and 0 <= minutes <= 59:
                        return hours * 60 + minutes
                    else:
                        return -1
                except:
                    return -1
            
            new_start_minutes = parse_time_to_minutes(start_time)
            new_end_minutes = parse_time_to_minutes(end_time)
            
            # Validate input times
            if new_start_minutes == -1 or new_end_minutes == -1:
                logger.error(f"Invalid time format: {start_time} - {end_time}")
                return conflicts
            
            # Chỉ check limit_rows hàng mới nhất (bỏ qua header)
            total_rows = len(data)
            start_row = max(2, total_rows - limit_rows + 1)  # Bắt đầu từ row 2 (skip header)
            end_row = total_rows + 1
            
            logger.info(f"Checking conflicts in rows {start_row} to {end_row-1} (latest {limit_rows} rows)")
            
            # Cấu trúc sheet: [Timestamp, Name, Phone, CustomerCount, Room, Date, StartTime, EndTime, Notes, Email, Status, ProcessedTime]
            for i in range(start_row, end_row):
                row_index = i - 1  # Convert to 0-based index for data array
                if row_index >= len(data):
                    break
                    
                row = data[row_index]
                
                if exclude_row and i == exclude_row:
                    logger.debug(f"Skipping excluded row {i}")
                    continue
                
                if len(row) >= 8:  # Đảm bảo có đủ cột
                    row_room = row[4] if len(row) > 4 else ""
                    row_date = row[5] if len(row) > 5 else ""
                    row_start_time = row[6] if len(row) > 6 else ""
                    row_end_time = row[7] if len(row) > 7 else ""
                    row_status = row[10] if len(row) > 10 else ""
                    
                    # Chỉ kiểm tra những booking có trạng thái "Chờ xử lý" hoặc "Đã xác nhận"
                    # và cùng ngày, cùng phòng
                    valid_statuses = ["Chờ xử lý", "Đã xác nhận"]
                    if (row_status in valid_statuses and
                        row_date == date and 
                        row_room.strip() == room.strip()):
                        
                        # Kiểm tra overlap thời gian - chỉ khi cả start và end time đều hợp lệ
                        existing_start_minutes = parse_time_to_minutes(str(row_start_time))
                        existing_end_minutes = parse_time_to_minutes(str(row_end_time))
                        
                        # Skip nếu thời gian không hợp lệ
                        if existing_start_minutes == -1 or existing_end_minutes == -1:
                            logger.warning(f"Invalid time format in row {i}: {row_start_time} - {row_end_time}")
                            continue
                        
                        # Check if times overlap
                        if (new_start_minutes < existing_end_minutes and 
                            new_end_minutes > existing_start_minutes):
                            
                            logger.debug(f"Conflict found at row {i}: {row[1]} ({row_start_time}-{row_end_time})")
                            
                            conflicts.append({
                                'row_number': i,
                                'name': row[1] if len(row) > 1 else "",
                                'email': row[9] if len(row) > 9 else "",
                                'date': row_date,
                                'start_time': row_start_time,
                                'end_time': row_end_time,
                                'room': row_room,
                                'status': row_status or "Chờ xử lý"
                            })
            
            logger.info(f"Checked {limit_rows} latest rows, found {len(conflicts)} conflicts")
            return conflicts
            
        except Exception as e:
            logger.error(f"Error checking room conflicts: {e}")
            return []
    
    def generate_conflict_message(self, conflicts):
        """
        Tạo message hiển thị conflict cho Discord
        
        Args:
            conflicts (list): Danh sách conflict từ check_room_conflicts
            
        Returns:
            str: Message formatted cho Discord, None nếu không có conflict
        """
        if not conflicts:
            return None
            
        messages = []
        for conflict in conflicts:
            msg = (f"🔴 **Trùng với lịch đặt khác:**\n"
                   f"👤 **Tên:** {conflict['name']}\n" 
                   f"🏠 **Phòng:** {conflict['room']}\n"
                   f"📅 **Ngày:** {conflict['date']}\n"
                   f"⏰ **Thời gian:** {conflict['start_time']} - {conflict['end_time']}")
            messages.append(msg)
        
        return f"🚨 **Lịch bị trùng!**\n\n" + "\n\n".join(messages)

    def add_to_google_calendar(self, booking_data):
        """
        Thêm booking đã xác nhận vào Google Calendar
        
        Args:
            booking_data (dict): Thông tin booking {name, room, date, startTime, endTime, notes, email}
        
        Returns:
            str: Event ID nếu thành công, None nếu thất bại
        """
        try:
            if not self.calendar_service:
                logger.error("Calendar service not initialized")
                return None
            
            # Parse date và time
            date_str = booking_data.get('date', '')  # Format: dd/mm/yyyy
            start_time_str = booking_data.get('startTime', '')  # Format: HH:MM
            end_time_str = booking_data.get('endTime', '')  # Format: HH:MM
            
            # Convert date format from dd/mm/yyyy to yyyy-mm-dd
            date_parts = date_str.split('/')
            if len(date_parts) != 3:
                logger.error(f"Invalid date format: {date_str}")
                return None
            
            day, month, year = date_parts
            iso_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            
            # Tạo datetime objects với timezone Việt Nam
            vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
            
            # Parse start time
            if not start_time_str or ':' not in start_time_str:
                logger.error(f"Invalid start time format: {start_time_str}")
                return None
                
            start_parts = start_time_str.split(':')
            start_hour = int(start_parts[0])
            start_minute = int(start_parts[1]) if len(start_parts) > 1 else 0
            
            # Parse end time
            if not end_time_str or ':' not in end_time_str:
                logger.error(f"Invalid end time format: {end_time_str}")
                return None
                
            end_parts = end_time_str.split(':')
            end_hour = int(end_parts[0])
            end_minute = int(end_parts[1]) if len(end_parts) > 1 else 0
            
            # Tạo datetime objects
            base_date = datetime.strptime(iso_date, '%Y-%m-%d')
            start_datetime = vn_tz.localize(base_date.replace(hour=start_hour, minute=start_minute))
            end_datetime = vn_tz.localize(base_date.replace(hour=end_hour, minute=end_minute))
            
            # Nếu end time < start time, assume next day
            if end_datetime <= start_datetime:
                end_datetime = end_datetime + timedelta(days=1)
                logger.info("End time is next day (overnight booking)")
            
            # Tạo event data
            event = {
                'summary': f"📅 Lịch Họp - {booking_data.get('room', 'Phòng họp')} ({booking_data.get('name', 'Khách hàng')})",
                'description': (
                    f"👤 Khách hàng: {booking_data.get('name', '')}\n"
                    f"📧 Email: {booking_data.get('email', '')}\n"
                    f"📞 Điện thoại: {booking_data.get('phone', '')}\n"
                    f"🏠 Phòng họp: {booking_data.get('room', '')}\n"
                    f"📅 Ngày: {date_str}\n"
                    f"⏰ Giờ: {start_time_str} - {end_time_str}\n"
                    f"👥 Số khách: {booking_data.get('customerCount', '')}\n"
                    f"📝 Ghi chú: {booking_data.get('notes', '')}"
                ),
                'location': 'Coffee Workspace',
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'Asia/Ho_Chi_Minh'
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'Asia/Ho_Chi_Minh'
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 60},  # Email reminder 1 hour before
                        {'method': 'popup', 'minutes': 15}   # Popup reminder 15 minutes before
                    ]
                }
            }
            
            # Tạo event trên Google Calendar
            created_event = self.calendar_service.events().insert(
                calendarId=Config.GOOGLE_CALENDAR_ID,  # Sử dụng calendar từ config
                body=event
            ).execute()
            
            event_id = created_event.get('id')
            event_link = created_event.get('htmlLink')
            
            logger.info(f"✅ Created Google Calendar event: {event_id}")
            logger.info(f"📅 Event link: {event_link}")
            
            return event_id
            
        except Exception as e:
            logger.error(f"Error creating Google Calendar event: {e}")
            return None
        
    def delete_calendar_event_by_booking(self, booking_data):
        """
        Xóa calendar event dựa trên thông tin booking
        
        Args:
            booking_data (dict): Thông tin booking
            
        Returns:
            bool: True nếu xóa thành công hoặc không tìm thấy event, False nếu có lỗi
        """
        try:
            if not self.calendar_service:
                logger.warning("Calendar service not initialized")
                return False
            
            # Tìm event dựa trên thông tin booking
            event_id = self._find_calendar_event_by_booking(booking_data)
            
            if not event_id:
                logger.warning("No calendar event found for this booking")
                return True  # Không có event để xóa cũng coi như thành công
            
            # Xóa event
            self.calendar_service.events().delete(
                calendarId=Config.GOOGLE_CALENDAR_ID,
                eventId=event_id
            ).execute()
            
            logger.info(f"✅ Deleted calendar event: {event_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting calendar event: {e}")
            return False
    
    def _find_calendar_event_by_booking(self, booking_data):
        """
        Tìm calendar event dựa trên thông tin booking
        
        Args:
            booking_data (dict): Thông tin booking
            
        Returns:
            str: Event ID nếu tìm thấy, None nếu không tìm thấy
        """
        try:
            # Parse date để tạo time range tìm kiếm
            date_str = booking_data.get('date', '')
            if not date_str:
                return None
            
            # Chuyển date format từ dd/mm/yyyy sang yyyy-mm-dd
            parts = date_str.split('/')
            if len(parts) != 3:
                return None
            
            day, month, year = parts
            iso_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            
            # Tạo time range để search (cả ngày)
            vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
            search_date = datetime.strptime(iso_date, '%Y-%m-%d')
            
            time_min = vn_tz.localize(search_date).isoformat()
            time_max = vn_tz.localize(search_date + timedelta(days=1)).isoformat()
            
            # Tìm events trong ngày
            events_result = self.calendar_service.events().list(
                calendarId=Config.GOOGLE_CALENDAR_ID,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Tìm event match với booking info
            customer_name = booking_data.get('name', '').strip().lower()
            customer_email = booking_data.get('email', '').strip().lower()
            room = booking_data.get('room', '').strip().lower()
            
            for event in events:
                event_summary = event.get('summary', '').lower()
                event_description = event.get('description', '').lower()
                
                # Check nếu event chứa thông tin của booking
                name_match = customer_name and customer_name in event_summary
                email_match = customer_email and customer_email in event_description
                room_match = room and room in event_description
                
                # Cần ít nhất 2 trong 3 điều kiện match
                matches = sum([name_match, email_match, room_match])
                
                if matches >= 2:
                    logger.info(f"Found matching calendar event: {event.get('id')}")
                    return event.get('id')
            
            logger.warning("No matching calendar event found")
            return None
            
        except Exception as e:
            logger.error(f"Error finding calendar event: {e}")
            return None
